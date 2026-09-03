"""BébéCare : API.

Plateforme de santé de l'enfant 0-5 ans pour les 15 pays de la CEDEAO.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import croissance as croiss
from . import dhis2 as passerelle
from . import donnees, triage as moteur_triage
from . import bd, comptes, ia_triage, pdf_vaccins
from fastapi import Header
from .pays_meta import CATEGORIES, DHIS2_NATIONAL, PAYS

app = FastAPI(
    title="BébéCare API",
    version="2.14",
    description="Santé de l'enfant 0-5 ans : 15 pays de la CEDEAO. "
                "Données OMS, OpenStreetMap et DHIS2.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Noms lisibles des champs, pour les erreurs de saisie (jamais de JSON brut).
_CHAMPS_LISIBLES = {
    "age_mois": "L'âge en mois", "poids_kg": "Le poids (kg)",
    "taille_cm": "La taille (cm)", "pb_mm": "Le périmètre brachial (mm)",
    "sexe": "Le sexe", "temp_c": "La température", "freq_resp": "Le rythme respiratoire",
    "question": "La question", "texte": "Le texte", "org_unit": "La formation sanitaire",
    "periode": "La période", "identifiant": "L'identifiant", "mot_de_passe": "Le mot de passe",
    "date_naissance": "La date de naissance", "prenom": "Le prénom",
}


@app.exception_handler(RequestValidationError)
async def _erreurs_de_saisie(_requete, exc: RequestValidationError):
    """Transforme les 422 Pydantic en phrases lisibles par un parent."""
    phrases = []
    for e in exc.errors():
        brut = str(e.get("loc", ["champ"])[-1])
        champ = _CHAMPS_LISIBLES.get(brut, brut)
        typ = e.get("type", "")
        ctx = e.get("ctx") or {}
        if typ == "missing":
            phrases.append(f"{champ} est obligatoire.")
        elif typ == "greater_than":
            phrases.append(f"{champ} : valeur trop petite (minimum {ctx.get('gt'):g}). Vérifiez l'unité.")
        elif typ == "greater_than_equal":
            phrases.append(f"{champ} : valeur trop petite (minimum {ctx.get('ge'):g}).")
        elif typ in ("less_than", "less_than_equal"):
            phrases.append(f"{champ} : valeur trop grande (maximum {ctx.get('lt', ctx.get('le')):g}).")
        elif "pattern" in typ:
            phrases.append(f"{champ} : valeur invalide.")
        else:
            phrases.append(f"Vérifiez {champ} : valeur invalide.")
    return JSONResponse(status_code=422, content={"detail": " ".join(phrases)})


@app.on_event("startup")
def _demarrage():
    donnees.charger()
    comptes.initialiser()


# ------------------------------------------------------------------ SANTE API

@app.get("/api/sante", tags=["système"])
def sante():
    return {
        "statut": "ok",
        "service": "bebecare",
        "version": "2.14",
        "pays_charges": len(donnees.pays_charges()),
        "structures_sante": donnees.total_lieux(),
        "base": bd.description(),
    }


# ---------------------------------------------------------------------- PAYS

@app.get("/api/pays", tags=["pays"])
def liste_pays():
    out = []
    for code, m in PAYS.items():
        if code not in donnees.pays_charges():
            continue
        cov = donnees.couverture_oms()["pays"].get(code, {}).get("indicateurs", {})
        out.append({
            "code": code, **{k: m[k] for k in
                             ("nom", "nom_en", "drapeau", "langue", "urgence",
                              "capitale", "lat", "lon", "zoom", "iso3")},
            "nb_structures": len(donnees.lieux_de(code)),
            "dhis2_national": code in DHIS2_NATIONAL,
            "dtp3": cov.get("DTP3", {}).get("valeur"),
            "u5mr": cov.get("U5MR", {}).get("valeur"),
        })
    return sorted(out, key=lambda p: p["nom"])


@app.get("/api/pays/{code}", tags=["pays"])
def detail_pays(code: str):
    if code not in PAYS:
        raise HTTPException(404, "pays inconnu")
    cal = donnees.calendriers()["pays"].get(code, {})
    cov = donnees.couverture_oms()["pays"].get(code, {})
    return {
        "code": code, **PAYS[code],
        "dhis2_national": code in DHIS2_NATIONAL,
        "structures": {
            "total": len(donnees.lieux_de(code)),
            "par_categorie": donnees.repartition(code),
            **donnees.meta_donnees(code),
        },
        "calendrier": cal,
        "couverture_oms": cov.get("indicateurs", {}),
        "sources": {
            "structures": "OpenStreetMap (ODbL 1.0)",
            "calendrier": donnees.calendriers()["source"],
            "couverture": donnees.couverture_oms()["source"],
        },
    }


@app.get("/api/categories", tags=["pays"])
def categories():
    return CATEGORIES


# ---------------------------------------------------------------------- CARTE

@app.get("/api/carte/bbox", tags=["carte"])
def carte_bbox(
    sud: float, ouest: float, nord: float, est: float,
    pays: str | None = None,
    types: str | None = Query(None, description="catégories séparées par une virgule"),
    limite: int = Query(1200, le=4000),
):
    cats = set(types.split(",")) if types else None
    lieux = donnees.dans_bbox(pays, sud, ouest, nord, est, cats, limite)
    return {"nb": len(lieux), "tronque": len(lieux) >= limite, "lieux": lieux}


@app.get("/api/carte/proches", tags=["carte"])
def carte_proches(
    lat: float, lon: float,
    types: str | None = None,
    n: int = Query(8, le=50),
    rayon_km: float = Query(100, le=400),
):
    cats = set(types.split(",")) if types else None
    return {"origine": {"lat": lat, "lon": lon},
            "resultats": donnees.plus_proches(lat, lon, cats, n, rayon_km)}


@app.get("/api/carte/recherche", tags=["carte"])
def carte_recherche(q: str, pays: str | None = None, limite: int = Query(25, le=100)):
    return {"resultats": donnees.rechercher(q, pays, limite)}


@app.get("/api/carte/stats", tags=["carte"])
def carte_stats():
    total = {}
    for code in donnees.pays_charges():
        for cat, n in donnees.repartition(code).items():
            total[cat] = total.get(cat, 0) + n
    return {
        "structures_total": donnees.total_lieux(),
        "pays": len(donnees.pays_charges()),
        "par_categorie": dict(sorted(total.items(), key=lambda x: -x[1])),
        "source": "OpenStreetMap contributors (ODbL 1.0)",
    }


# --------------------------------------------------------------- VACCINATION

class Naissance(BaseModel):
    date_naissance: date
    pays: str
    deja_faits: list[str] = Field(default_factory=list,
                                  description="clés 'VACCIN|dose' déjà administrées")


@app.get("/api/vaccins/calendrier/{code}", tags=["vaccination"])
def calendrier(code: str):
    cal = donnees.calendriers()["pays"].get(code)
    if not cal:
        raise HTTPException(404, "calendrier indisponible pour ce pays")
    groupes: dict[int, dict] = {}
    for d in cal["doses"]:
        g = groupes.setdefault(d["jours"], {"jours": d["jours"], "age": d["age"],
                                            "vaccins": []})
        g["vaccins"].append({"nom": d["nom"], "dose": d["dose"], "code": d["vaccin"]})
    return {
        "pays": code, "annee": cal["annee"],
        "etapes": [groupes[k] for k in sorted(groupes)],
        "source": donnees.calendriers()["source"],
        "url_source": donnees.calendriers()["url"],
    }


def _calcul_planning(code_pays: str, naissance: date, deja_faits) -> dict:
    """Calcul commun au planning JSON (page Vaccins) et au PDF telechargeable."""
    cal = donnees.calendriers()["pays"].get(code_pays)
    if not cal:
        raise HTTPException(404, "calendrier indisponible pour ce pays")
    aujourd = date.today()
    faits = set(deja_faits)
    etapes, en_retard, a_venir = [], 0, 0
    for d in cal["doses"]:
        prevu = naissance + timedelta(days=d["jours"])
        cle = f"{d['vaccin']}|{d['dose']}"
        fait = cle in faits
        jours_ecart = (prevu - aujourd).days
        if fait:
            etat = "fait"
        elif jours_ecart < -14:
            etat = "retard"
            en_retard += 1
        elif jours_ecart <= 30:
            etat = "bientot"
            a_venir += 1
        else:
            etat = "futur"
        etapes.append({
            "cle": cle, "vaccin": d["nom"], "code": d["vaccin"], "dose": d["dose"],
            "age": d["age"], "date_prevue": prevu.isoformat(),
            "jours_restants": jours_ecart, "etat": etat,
        })
    age_jours = (aujourd - naissance).days
    return {
        "pays": code_pays,
        "date_naissance": naissance.isoformat(),
        "age_jours": age_jours,
        "age_mois": round(age_jours / 30.4375, 1),
        "resume": {"total": len(etapes), "faits": len(faits),
                   "en_retard": en_retard, "dans_le_mois": a_venir},
        "etapes": etapes,
        "message": ("Des doses sont en retard : passez au centre de santé, "
                    "le rattrapage est possible et gratuit dans le PEV."
                    if en_retard else
                    "Le calendrier est à jour. Continuez ainsi."),
        "source": donnees.calendriers()["source"],
        "genere_le": aujourd.isoformat(),
    }


@app.post("/api/vaccins/planning", tags=["vaccination"])
def planning(n: Naissance):
    return _calcul_planning(n.pays, n.date_naissance, n.deja_faits)


@app.get("/api/vaccins/ics", tags=["vaccination"])
def ics(pays: str, date_naissance: date):
    """Calendrier iCalendar téléchargeable (rappels agenda du téléphone)."""
    cal = donnees.calendriers()["pays"].get(pays)
    if not cal:
        raise HTTPException(404, "calendrier indisponible")
    lignes = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BebeCare//FR",
              "CALSCALE:GREGORIAN"]
    for i, d in enumerate(cal["doses"]):
        j = (date_naissance + timedelta(days=d["jours"])).strftime("%Y%m%d")
        lignes += [
            "BEGIN:VEVENT",
            f"UID:bebecare-{pays}-{i}@bebecare",
            f"DTSTART;VALUE=DATE:{j}",
            f"SUMMARY:Vaccination : {d['nom']} (dose {d['dose']})",
            f"DESCRIPTION:Rendez-vous vaccinal prévu à {d['age']}. "
            "Apportez le carnet de santé. Source : calendrier national OMS.",
            "BEGIN:VALARM", "TRIGGER:-P2D", "ACTION:DISPLAY",
            "DESCRIPTION:Vaccination dans 2 jours", "END:VALARM",
            "END:VEVENT",
        ]
    lignes.append("END:VCALENDAR")
    from fastapi.responses import Response
    return Response("\r\n".join(lignes), media_type="text/calendar",
                    headers={"Content-Disposition":
                             f'attachment; filename="bebecare-{pays}.ics"'})


@app.get("/api/vaccins/calendrier.pdf", tags=["vaccination"])
def calendrier_pdf(pays: str, date_naissance: date,
                   prenom: str = "", faits: str = "", langue: str = "fr"):
    """Calendrier vaccinal personnalise en PDF.

    Le PDF remplace le .ics comme document de reference pour les parents :
    il s'ouvre sur tous les telephones, s'imprime au centre de sante et se
    partage sur WhatsApp. `faits` : cles 'VACCIN|dose' separees par virgules.
    """
    from fastapi.responses import Response
    if pays not in PAYS:
        raise HTTPException(404, "pays inconnu")
    if date_naissance > date.today():
        raise HTTPException(422, "la date de naissance est dans le futur")

    liste_faits = [f for f in faits.split(",") if f] if faits else []
    plan = _calcul_planning(pays, date_naissance, liste_faits)

    # Les cases "faites" n'ont de sens que pour les doses de ce pays.
    meta = PAYS[pays]
    nom_pays = meta["nom_en"] if langue == "en" else meta["nom"]
    octets = pdf_vaccins.generer(nom_pays, plan, prenom, langue)
    return Response(
        octets, media_type="application/pdf",
        headers={"Content-Disposition":
                 f'attachment; filename="calendrier-vaccinal-'
                 f'{pays}-{date_naissance.isoformat()}.pdf"'})


# ---------------------------------------------------------------- NUTRITION

class Mesure(BaseModel):
    """Mesures de croissance. Tolere les unites de terrain : une bandelette
    MUAC se lit souvent en cm (13) et pas en mm (130) ; une taille peut
    arriver en metres (0.86). On convertit au lieu de rejeter."""
    age_mois: float = Field(ge=0, le=60)
    sexe: str = Field(pattern="^[mf]$")
    poids_kg: float | None = Field(default=None, gt=0, lt=40)
    taille_cm: float | None = Field(default=None, gt=30, lt=140)
    pb_mm: float | None = Field(default=None, gt=60, lt=300)
    oedemes: bool = False

    @field_validator("sexe", mode="before")
    @classmethod
    def _sexe(cls, v):
        return str(v).strip().lower()[0]

    @field_validator("pb_mm", mode="before")
    @classmethod
    def _pb(cls, v):
        if v in (None, ""):
            return None
        v = float(v)
        # 5-30 : forcement des centimetres (le PB d'un enfant fait 10-20 cm)
        if 5 <= v < 61:
            return v * 10
        return v

    @field_validator("taille_cm", mode="before")
    @classmethod
    def _taille(cls, v):
        if v in (None, ""):
            return None
        v = float(v)
        # 0.3-3 : forcement des metres
        if 0.3 <= v <= 3:
            return v * 100
        return v


@app.post("/api/nutrition/depistage", tags=["nutrition"])
def depistage(m: Mesure):
    return croiss.evaluer(m.age_mois, m.sexe, m.poids_kg, m.taille_cm,
                          m.pb_mm, m.oedemes)


@app.get("/api/nutrition/courbe", tags=["nutrition"])
def courbe(indicateur: str = "wfa", sexe: str = "m",
           xmin: float = 0, xmax: float = 1856, pas: float = 30.4375):
    if indicateur not in ("wfa", "lhfa", "wfl", "wfh"):
        raise HTTPException(400, "indicateur inconnu")
    return {"indicateur": indicateur, "sexe": sexe,
            "points": croiss.courbe(indicateur, sexe, xmin, xmax, pas),
            "source": donnees.tables_croissance()["source"]}


# ------------------------------------------------------------------- TRIAGE

class Triage(BaseModel):
    age_mois: float = Field(ge=0, le=60)
    signes: list[str] = Field(default_factory=list)
    temp_c: float | None = Field(default=None, ge=30, le=45)
    freq_resp: int | None = Field(default=None, ge=5, le=150)
    allaite: bool | None = None
    pays: str | None = None


@app.get("/api/triage/catalogue", tags=["triage"])
def catalogue_triage():
    return moteur_triage.catalogue()


@app.post("/api/triage", tags=["triage"])
def faire_triage(t: Triage):
    return moteur_triage.evaluer(t.age_mois, t.signes, t.temp_c, t.freq_resp,
                                 t.allaite, t.pays)


# -------------------------------------------------------------- OMS / DHIS2

@app.get("/api/oms/couverture", tags=["données"])
def oms_couverture(pays: str | None = None):
    d = donnees.couverture_oms()
    if pays:
        if pays not in d["pays"]:
            raise HTTPException(404, "pays inconnu")
        return {"source": d["source"], "url": d["url"], "pays": {pays: d["pays"][pays]}}
    return d


@app.get("/api/oms/comparaison", tags=["données"])
def oms_comparaison(indicateur: str = "DTP3"):
    d = donnees.couverture_oms()["pays"]
    lignes = []
    for code, p in d.items():
        i = p["indicateurs"].get(indicateur)
        if i:
            lignes.append({"pays": code, "nom": PAYS[code]["nom"],
                           "drapeau": PAYS[code]["drapeau"],
                           "valeur": i["valeur"], "annee": i["annee"]})
    lignes.sort(key=lambda x: -x["valeur"])
    return {"indicateur": indicateur, "lignes": lignes,
            "source": donnees.couverture_oms()["source"]}


@app.get("/api/dhis2/statut", tags=["DHIS2"])
def dhis2_statut():
    return passerelle.statut()


@app.get("/api/dhis2/formations", tags=["DHIS2"])
def dhis2_formations(limite: int = Query(300, le=1200)):
    return passerelle.formations_sanitaires(limite)


@app.get("/api/dhis2/districts", tags=["DHIS2"])
def dhis2_districts():
    return passerelle.districts()


@app.get("/api/dhis2/couverture", tags=["DHIS2"])
def dhis2_couverture(ou: str = "ImspTQPwCqd", periode: str = "LAST_12_MONTHS"):
    return passerelle.couverture(ou, periode)


class ExportDHIS2(BaseModel):
    org_unit: str = "DiszpKrYNg8"
    periode: str | None = None
    vaccins: list[str] = Field(default_factory=list)
    age_mois: float = 0
    nutrition_code: str | None = None


@app.post("/api/dhis2/export", tags=["DHIS2"])
def dhis2_export(e: ExportDHIS2):
    res = passerelle.construire_payload(
        e.org_unit, e.periode, e.vaccins, e.age_mois,
        {"code": e.nutrition_code} if e.nutrition_code else None)
    res["validation"] = passerelle.valider(res["payload"])
    return res


class ConsultationSoignant(BaseModel):
    prenom: str = ""
    age_mois: float = Field(default=0, ge=0, le=60)
    vaccins: list[str] = []
    nutrition_code: str | None = None


class SeanceSoignant(BaseModel):
    org_unit: str
    periode: str | None = None
    consultations: list[ConsultationSoignant]


@app.post("/api/dhis2/seance", tags=["DHIS2"])
def dhis2_seance(s: SeanceSoignant):
    """Mode soignant : agrege une seance de vaccination en un dataValueSets."""
    if not s.consultations:
        raise HTTPException(400, "aucune consultation dans la seance")
    return passerelle.construire_payload_lot(
        s.org_unit, s.periode, [c.model_dump() for c in s.consultations])


@app.post("/api/dhis2/seance/envoyer", tags=["DHIS2"])
def dhis2_seance_envoyer(s: SeanceSoignant):
    """Envoi reel dans DHIS2 (bloque tant que BEBECARE_DHIS2_PUSH != 1)."""
    if not s.consultations:
        raise HTTPException(400, "aucune consultation dans la seance")
    res = passerelle.construire_payload_lot(
        s.org_unit, s.periode, [c.model_dump() for c in s.consultations])
    return {**passerelle.pousser(res["payload"], essai_reel=True), "resume": res["resume"]}


class QuestionLibre(BaseModel):
    question: str = Field(min_length=2, max_length=800)
    pays: str | None = None
    age_mois: float | None = Field(default=None, ge=0, le=60)
    historique: list[dict] = Field(default_factory=list)


@app.post("/api/assistant/question", tags=["assistant IA"])
def assistant_question(q: QuestionLibre):
    """Questions libres des parents (alimentation, sommeil, developpement).

    Distinct du triage : ici il n'y a pas de verdict d'urgence. Mais on passe
    quand meme la question dans le detecteur local de signes de danger, pour
    rattraper un parent qui decrirait une urgence sous forme de question.
    """
    alerte = None
    try:
        lecture = ia_triage.repondre(q.question, q.age_mois, [], [], q.pays)
        if lecture.get("decision", {}).get("niveau") == "rouge":
            alerte = {
                "niveau": "rouge",
                "titre": lecture["decision"]["titre"],
                "raisons": lecture["decision"].get("raisons", []),
                "message": ("Votre question decrit un signe de danger. "
                            "Ouvrez l'onglet Assistant pour le triage complet."),
            }
    except Exception:
        pass

    res = ia_triage.llm.repondre_question(
        q.question, q.pays, q.age_mois, q.historique)

    if res is None:
        st = ia_triage.llm.statut()
        if st.get("actif"):
            # Cle presente mais fournisseur en panne : ne pas accuser l'usager.
            message = ("Le service conversationnel est momentanement "
                       "indisponible (incident chez le fournisseur d'IA). En "
                       "attendant, utilisez l'onglet Triage : decrivez les "
                       "symptomes et BebeCare applique l'algorithme PCIME de "
                       "l'OMS, sans avoir besoin de l'IA.")
        else:
            message = ("Le mode conversation a besoin d'une cle d'API pour "
                       "fonctionner. Sans elle, utilisez l'onglet Triage : "
                       "decrivez les symptomes et BebeCare applique "
                       "l'algorithme PCIME de l'OMS.")
        return {
            "disponible": False,
            "alerte": alerte,
            "reponse": message,
            "statut_llm": st,
        }

    return {
        "disponible": True,
        "alerte": alerte,
        "reponse": res["reponse"],
        "modele": res["modele"],
        "fournisseur": res["fournisseur"],
        "avertissement": ("BebeCare donne des informations, pas un diagnostic. "
                          "En cas de doute, consultez un professionnel de sante."),
    }


@app.get("/api/assistant/statut", tags=["assistant IA"])
def assistant_statut():
    """Transparence : quel etage IA est actif, et avec quel role exact."""
    return ia_triage.llm.statut()


@app.post("/api/dhis2/push", tags=["DHIS2"])
def dhis2_push(e: ExportDHIS2):
    res = passerelle.construire_payload(
        e.org_unit, e.periode, e.vaccins, e.age_mois,
        {"code": e.nutrition_code} if e.nutrition_code else None)
    return passerelle.pousser(res["payload"], essai_reel=True)


# -------------------------------------------------------------- COMPTES
# Le compte est TOUJOURS facultatif : tous les outils cliniques fonctionnent
# sans inscription. Il sert a synchroniser le suivi entre appareils.

def _uid(autorisation: str | None) -> int:
    jeton = (autorisation or "").removeprefix("Bearer ").strip()
    uid = comptes.lire_jeton(jeton)
    if not uid:
        raise HTTPException(401, "session expirée ou invalide")
    return uid


class Inscription(BaseModel):
    identifiant: str
    mot_de_passe: str
    pays: str = "bj"
    langue: str = "fr"
    nom: str | None = None
    role: str = "parent"


class Connexion(BaseModel):
    identifiant: str
    mot_de_passe: str


class MajProfil(BaseModel):
    nom: str | None = None
    pays: str | None = None
    langue: str | None = None
    role: str | None = None


class EnfantEntree(BaseModel):
    prenom: str
    sexe: str = Field(default="m", pattern="^[mf]$")
    date_naissance: date
    pays: str | None = None


class EnfantMaj(BaseModel):
    prenom: str | None = None
    sexe: str | None = None
    date_naissance: date | None = None
    pays: str | None = None
    vaccins_faits: list[str] | None = None


class MesureEntree(BaseModel):
    date_mesure: date
    age_mois: float
    poids_kg: float | None = None
    taille_cm: float | None = None
    pb_mm: float | None = None
    z_pa: float | None = None
    z_ta: float | None = None
    z_pt: float | None = None
    verdict: str | None = None


@app.post("/api/compte/inscription", tags=["compte"])
def inscription(e: Inscription):
    try:
        return comptes.inscrire(e.identifiant, e.mot_de_passe, e.pays, e.langue,
                                e.nom, e.role)
    except ValueError as err:
        raise HTTPException(400, str(err))


@app.post("/api/compte/connexion", tags=["compte"])
def connexion(e: Connexion):
    try:
        return comptes.connecter(e.identifiant, e.mot_de_passe)
    except ValueError as err:
        raise HTTPException(401, str(err))


@app.get("/api/compte/moi", tags=["compte"])
def moi(authorization: str | None = Header(default=None)):
    return comptes.profil(_uid(authorization))


@app.patch("/api/compte/moi", tags=["compte"])
def maj_profil(e: MajProfil, authorization: str | None = Header(default=None)):
    return comptes.modifier_profil(_uid(authorization), **e.model_dump())


@app.get("/api/compte/enfants", tags=["compte"])
def liste_enfants(authorization: str | None = Header(default=None)):
    return comptes.lister_enfants(_uid(authorization))


@app.post("/api/compte/enfants", tags=["compte"])
def ajout_enfant(e: EnfantEntree, authorization: str | None = Header(default=None)):
    return comptes.creer_enfant(_uid(authorization), e.prenom, e.sexe,
                                e.date_naissance.isoformat(), e.pays)


@app.patch("/api/compte/enfants/{eid}", tags=["compte"])
def maj_enfant(eid: int, e: EnfantMaj, authorization: str | None = Header(default=None)):
    d = e.model_dump()
    if d.get("date_naissance"):
        d["date_naissance"] = d["date_naissance"].isoformat()
    r = comptes.modifier_enfant(_uid(authorization), eid, **d)
    if not r:
        raise HTTPException(404, "enfant introuvable")
    return r


@app.delete("/api/compte/enfants/{eid}", tags=["compte"])
def suppr_enfant(eid: int, authorization: str | None = Header(default=None)):
    if not comptes.supprimer_enfant(_uid(authorization), eid):
        raise HTTPException(404, "enfant introuvable")
    return {"supprime": True}


@app.post("/api/compte/enfants/{eid}/mesures", tags=["compte"])
def ajout_mesure(eid: int, m: MesureEntree,
                 authorization: str | None = Header(default=None)):
    d = m.model_dump()
    d["date_mesure"] = m.date_mesure.isoformat()
    r = comptes.ajouter_mesure(_uid(authorization), eid, d)
    if not r:
        raise HTTPException(404, "enfant introuvable")
    return r


@app.get("/api/compte/enfants/{eid}/mesures", tags=["compte"])
def liste_mesures(eid: int, authorization: str | None = Header(default=None)):
    return comptes.historique(_uid(authorization), eid)


# ------------------------------------------------------------- ASSISTANT IA

class QuestionIA(BaseModel):
    texte: str = Field(min_length=2, max_length=1200)
    age_mois: float | None = None
    signes_confirmes: list[str] = Field(default_factory=list)
    deja_posees: list[str] = Field(default_factory=list)
    pays: str | None = None


@app.post("/api/assistant", tags=["assistant IA"])
def assistant(q: QuestionIA):
    """Assistant de triage : comprehension du langage naturel + PCIME."""
    return ia_triage.repondre(q.texte, q.age_mois, q.signes_confirmes,
                              q.deja_posees, q.pays)


@app.post("/api/assistant/analyse", tags=["assistant IA"])
def assistant_analyse(q: QuestionIA):
    """Etage de comprehension seul (utile pour demontrer/deboguer l'extraction)."""
    return ia_triage.analyser(q.texte)


@app.get("/api/sources", tags=["système"])
def sources():
    return {
        "structures_sante": {
            "nom": "OpenStreetMap", "licence": "ODbL 1.0",
            "url": "https://www.openstreetmap.org/copyright",
            "nb": donnees.total_lieux(),
        },
        "calendriers_vaccinaux": {
            "nom": donnees.calendriers()["source"],
            "url": donnees.calendriers()["url"], "licence": "OMS : données ouvertes",
        },
        "couverture_vaccinale": {
            "nom": donnees.couverture_oms()["source"],
            "url": donnees.couverture_oms()["url"], "licence": "OMS GHO : données ouvertes",
        },
        "normes_croissance": {
            "nom": donnees.tables_croissance()["source"],
            "url": donnees.tables_croissance()["url"], "licence": "OMS",
        },
        "triage": {
            "nom": "PCIME : Prise en charge intégrée des maladies de l'enfant (OMS/UNICEF)",
            "url": "https://www.who.int/teams/maternal-newborn-child-adolescent-health-and-ageing",
        },
        "dhis2": {
            "nom": "DHIS2 : instance de démonstration publique (Sierra Leone)",
            "url": passerelle.BASE,
            "note": "Données de démonstration fictives. BébéCare ne se connecte à "
                    "aucune base nationale de production.",
        },
        "meteo": {"nom": "Open-Meteo", "url": "https://open-meteo.com"},
    }


# ----------------------------------------------------------- FRONT STATIQUE

DIST = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")),
              name="assets")

    @app.get("/{chemin:path}", include_in_schema=False)
    def spa(chemin: str):
        f = os.path.join(DIST, chemin)
        if chemin and os.path.isfile(f):
            return FileResponse(f)
        return FileResponse(os.path.join(DIST, "index.html"))
