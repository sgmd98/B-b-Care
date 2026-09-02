"""Passerelle DHIS2.

DHIS2 est le systeme national d'information sanitaire (SNIS/DHIS2) de plus de
80 pays, dont 14 des 15 pays couverts par BebeCare. BebeCare ne se connecte
PAS aux instances nationales de production (donnees sensibles, acces reserve
aux ministeres) : il se branche sur l'instance de demonstration publique
officielle de DHIS2 (base Sierra Leone, donnees fictives, identifiants publies
par DHIS2 : admin/district).

Ce que ca demontre :
  1. LECTURE   : les indicateurs de couverture vaccinale et l'arbre des
                 formations sanitaires sont lus en direct via l'API DHIS2.
  2. ECRITURE  : le carnet de vaccination et le depistage nutritionnel sont
                 traduits en un payload `dataValueSets` conforme, pret a etre
                 pousse dans le SNIS d'un pays (POST desactive par defaut).

Un ministere n'a donc qu'a changer BEBECARE_DHIS2_URL et les identifiants
pour brancher BebeCare sur son propre DHIS2.
"""
from __future__ import annotations

import base64
import json
import os
import time
from datetime import date

import httpx

BASE = os.environ.get("BEBECARE_DHIS2_URL", "https://play.im.dhis2.org/stable-2-42-6")
USER = os.environ.get("BEBECARE_DHIS2_USER", "admin")
MDP = os.environ.get("BEBECARE_DHIS2_PASSWORD", "district")
AUTORISER_PUSH = os.environ.get("BEBECARE_DHIS2_PUSH", "0") == "1"

_AUTH = "Basic " + base64.b64encode(f"{USER}:{MDP}".encode()).decode()
_ENTETES = {"Authorization": _AUTH, "Accept": "application/json",
            "User-Agent": "BebeCare/2.0"}

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FICHIER = os.path.join(RACINE, "data", "dhis2_cache.json")

# --- Cartographie BebeCare -> metadonnees DHIS2 (dataset "Child Health") ---
DATASET = "BfMAe6Itzgt"          # Child Health, periodType Monthly
COC_FIXE_MOINS_1AN = "Prlt0C1RF0s"   # "Fixed, <1y"
COC_FIXE_PLUS_1AN = "psbwp3CQEhs"    # "Fixed, >1y"

VACCIN_VERS_DE = {
    "BCG": "s46m5MS0hxu",
    "OPV0": "x3Do5e7g4Qo",
    "OPV1": "pikOziyCXbM",
    "OPV2": "O05mAByOgAv",
    "OPV3": "vI2csg55S9C",
    "PENTA1": "fClA2Erf6IO",
    "PENTA2": "I78gJm4KBo7",
    "PENTA3": "n6aMJNLdvep",
    "PCV1": "xc8gmAKfO95",
    "PCV2": "mGN1az8Xub6",
    "PCV3": "L2kxa2IA2cs",
    "MEASLES": "YtbsuPPo010",
    "YF": "l6byfWFUGaP",
    "VITA": "tU7GixyHhsv",
    "COMPLET": "UOlfIjgN8X6",
}

NUTRITION_VERS_DE = {
    "pa_rouge": "bTcRDVjC66S",    # Weight for age below lower line (red)
    "pa_jaune": "ldGXl6SEdqf",    # between middle and lower line (yellow)
    "pa_vert": "NLnXLV5YpZF",     # on or above middle line (green)
    "pt_severe": "lVsbKXoF0zX",   # Weight for height below 70 percent
    "pt_modere": "pnL2VG8Bn7N",   # Weight for height 70-79 percent
    "pt_normal": "qPVDd87kS9Z",   # Weight for height 80 percent and above
}

INDICATEURS_COUVERTURE = {
    "FnYCr2EAzWS": "Couverture BCG (< 1 an)",
    "i7WSgSJpnfu": "Couverture Penta 1 (< 1 an)",
    "tUIlpyeeX9N": "Couverture Penta 3 (< 1 an)",
    "FbKK4ofIv5R": "Couverture rougeole (< 1 an)",
    "JoEzWYGdX7s": "Couverture VPO 3 (< 1 an)",
}

_memo: dict[str, tuple[float, object]] = {}
TTL = 900  # 15 min


def _cache_get(cle):
    v = _memo.get(cle)
    if v and time.time() - v[0] < TTL:
        return v[1]
    return None


def _cache_set(cle, valeur):
    _memo[cle] = (time.time(), valeur)
    return valeur


def _cache_disque() -> dict:
    if os.path.isfile(CACHE_FICHIER):
        try:
            with open(CACHE_FICHIER, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _ecrire_cache_disque(cle: str, valeur):
    d = _cache_disque()
    d[cle] = valeur
    try:
        with open(CACHE_FICHIER, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:  # noqa: BLE001
        pass


def _get(chemin: str, params: dict | None = None, timeout: float = 20.0):
    url = f"{BASE}/api/{chemin.lstrip('/')}"
    r = httpx.get(url, params=params, headers=_ENTETES, timeout=timeout,
                  follow_redirects=True)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------- LECTURE


def statut() -> dict:
    cle = "statut"
    if (v := _cache_get(cle)) is not None:
        return v
    try:
        info = _get("system/info", timeout=15)
        res = {
            "connecte": True,
            "instance": BASE,
            "version": info.get("version"),
            "revision": info.get("revision"),
            "base_demo": "Sierra Leone (données de démonstration officielles DHIS2)",
            "derniere_analyse": info.get("lastAnalyticsTableSuccess"),
            "mode_ecriture": "activé" if AUTORISER_PUSH else "désactivé (sécurité)",
        }
        _ecrire_cache_disque(cle, res)
        return _cache_set(cle, res)
    except Exception as e:  # noqa: BLE001
        secours = _cache_disque().get(cle)
        return {"connecte": False, "instance": BASE, "erreur": str(e),
                "secours": secours}


def formations_sanitaires(limite: int = 400) -> dict:
    """Formations sanitaires DHIS2 (niveau 4) avec leurs coordonnees."""
    cle = f"ou:{limite}"
    if (v := _cache_get(cle)) is not None:
        return v
    try:
        d = _get("organisationUnits.json", {
            "level": 4,
            "fields": "id,name,level,geometry,parent[id,name,parent[id,name]]",
            "pageSize": limite, "paging": "true",
        }, timeout=40)
        out = []
        for ou in d.get("organisationUnits", []):
            g = ou.get("geometry") or {}
            coords = g.get("coordinates") if g.get("type") == "Point" else None
            parent = ou.get("parent") or {}
            out.append({
                "id": ou["id"], "nom": ou["name"],
                "lon": coords[0] if coords else None,
                "lat": coords[1] if coords else None,
                "district": parent.get("name"),
                "region": (parent.get("parent") or {}).get("name"),
            })
        res = {"total": d.get("pager", {}).get("total"), "formations": out}
        _ecrire_cache_disque(cle, res)
        return _cache_set(cle, res)
    except Exception as e:  # noqa: BLE001
        return _cache_disque().get(cle) or {"erreur": str(e), "formations": []}


def couverture(ou: str = "ImspTQPwCqd", periode: str = "LAST_12_MONTHS") -> dict:
    """Couverture vaccinale mensuelle lue en direct dans DHIS2 (analytics)."""
    cle = f"cov:{ou}:{periode}"
    if (v := _cache_get(cle)) is not None:
        return v
    try:
        d = _get("analytics.json", {
            "dimension": [f"dx:{';'.join(INDICATEURS_COUVERTURE)}", f"pe:{periode}"],
            "filter": f"ou:{ou}",
            "displayProperty": "NAME",
            "skipMeta": "false",
        }, timeout=45)
        items = d.get("metaData", {}).get("items", {})
        entetes = [h["name"] for h in d["headers"]]
        i_dx, i_pe, i_val = entetes.index("dx"), entetes.index("pe"), entetes.index("value")
        series: dict[str, dict] = {}
        for ligne in d.get("rows", []):
            dx = ligne[i_dx]
            s = series.setdefault(dx, {
                "id": dx,
                "nom": INDICATEURS_COUVERTURE.get(dx, items.get(dx, {}).get("name", dx)),
                "points": [],
            })
            s["points"].append({
                "periode": ligne[i_pe],
                "libelle": items.get(ligne[i_pe], {}).get("name", ligne[i_pe]),
                "valeur": round(float(ligne[i_val]), 1),
            })
        for s in series.values():
            s["points"].sort(key=lambda p: p["periode"])
        res = {
            "unite_org": items.get(ou, {}).get("name", ou),
            "periode": periode,
            "series": list(series.values()),
            "source": f"DHIS2 analytics live : {BASE}",
        }
        _ecrire_cache_disque(cle, res)
        return _cache_set(cle, res)
    except Exception as e:  # noqa: BLE001
        secours = _cache_disque().get(cle)
        if secours:
            return {**secours, "hors_ligne": True}
        return {"erreur": str(e), "series": []}


def districts() -> list[dict]:
    cle = "districts"
    if (v := _cache_get(cle)) is not None:
        return v
    try:
        d = _get("organisationUnits.json", {
            "level": 2, "fields": "id,name", "paging": "false"}, timeout=30)
        res = [{"id": o["id"], "nom": o["name"]} for o in d.get("organisationUnits", [])]
        _ecrire_cache_disque(cle, res)
        return _cache_set(cle, res)
    except Exception:  # noqa: BLE001
        return _cache_disque().get("districts") or []


# ---------------------------------------------------------------- ECRITURE


def construire_payload(org_unit: str, periode: str | None,
                       vaccins_administres: list[str],
                       age_mois: float = 0,
                       nutrition: dict | None = None) -> dict:
    """Traduit un carnet BebeCare en payload DHIS2 `dataValueSets` conforme.

    C'est le pont d'interoperabilite : un agent de sante communautaire saisit
    une fois dans BebeCare, et la donnee remonte au SNIS national sans
    double saisie.
    """
    periode = periode or date.today().strftime("%Y%m")
    coc = COC_FIXE_MOINS_1AN if age_mois < 12 else COC_FIXE_PLUS_1AN
    valeurs = []
    inconnus = []
    for v in vaccins_administres:
        de = VACCIN_VERS_DE.get(v.upper())
        if not de:
            inconnus.append(v)
            continue
        valeurs.append({
            "dataElement": de,
            "categoryOptionCombo": coc,
            "value": "1",
            "comment": f"BébéCare : {v.upper()}",
        })
    if nutrition:
        de = NUTRITION_VERS_DE.get(nutrition.get("code", ""))
        if de:
            valeurs.append({
                "dataElement": de,
                "categoryOptionCombo": coc,
                "value": "1",
                "comment": "BébéCare : dépistage nutritionnel (z-score OMS)",
            })

    return {
        "payload": {
            "dataSet": DATASET,
            "completeDate": date.today().isoformat(),
            "period": periode,
            "orgUnit": org_unit,
            "dataValues": valeurs,
        },
        "endpoint": f"{BASE}/api/dataValueSets",
        "methode": "POST",
        "entetes": {"Content-Type": "application/json"},
        "vaccins_non_mappes": inconnus,
        "explication": (
            "Ce document JSON est exactement ce que BébéCare enverrait au "
            "système national d'information sanitaire. Le schéma dataValueSets "
            "est celui de DHIS2 : dataSet, période (AAAAMM), unité "
            "d'organisation, puis une valeur par élément de donnée avec sa "
            "combinaison de catégories (ici « Fixed, <1y »)."
        ),
        "ecriture_activee": AUTORISER_PUSH,
    }


def pousser(payload: dict, essai_reel: bool = False) -> dict:
    """Envoie reellement le payload (uniquement si BEBECARE_DHIS2_PUSH=1)."""
    if not (AUTORISER_PUSH and essai_reel):
        return {
            "envoye": False,
            "raison": "Écriture désactivée. BébéCare ne modifie jamais une base "
                      "de démonstration publique sans activation explicite "
                      "(variable BEBECARE_DHIS2_PUSH=1).",
            "payload_valide": bool(payload.get("dataValues")),
        }
    r = httpx.post(f"{BASE}/api/dataValueSets", json=payload,
                   headers={**_ENTETES, "Content-Type": "application/json"},
                   timeout=60)
    return {"envoye": True, "statut_http": r.status_code, "reponse": r.json()}


def valider(payload: dict) -> dict:
    """Validation locale du payload avant envoi (schema DHIS2)."""
    erreurs = []
    for champ in ("dataSet", "period", "orgUnit", "dataValues"):
        if not payload.get(champ):
            erreurs.append(f"champ obligatoire manquant : {champ}")
    p = str(payload.get("period", ""))
    if p and (len(p) != 6 or not p.isdigit()):
        erreurs.append("période invalide : format attendu AAAAMM (ex. 202609)")
    for i, dv in enumerate(payload.get("dataValues", [])):
        if not dv.get("dataElement"):
            erreurs.append(f"dataValues[{i}] : dataElement manquant")
        if dv.get("value") in (None, ""):
            erreurs.append(f"dataValues[{i}] : value manquante")
    return {"valide": not erreurs, "erreurs": erreurs,
            "nb_valeurs": len(payload.get("dataValues", []))}


# ---------------------------------------------------------- MODE SOIGNANT
# Un DHIS2 agrege ne stocke PAS un enregistrement par enfant : il stocke un
# EFFECTIF par element de donnee, periode et unite d'organisation. Envoyer
# value="1" pour chaque enfant ecraserait la valeur precedente au lieu de
# l'incrementer. Le mode soignant agrege donc une seance de vaccination
# complete (plusieurs enfants) en UN seul document dataValueSets.

def construire_payload_lot(org_unit: str, periode: str | None,
                           consultations: list[dict]) -> dict:
    """Agrege une seance de consultations en un unique dataValueSets DHIS2.

    consultations : [{"prenom": str, "age_mois": float,
                      "vaccins": [str], "nutrition_code": str | None}, ...]

    La cle d'agregation est (dataElement, categoryOptionCombo) : DHIS2
    distingue les moins de 1 an des plus de 1 an, donc un meme vaccin
    administre a un nourrisson et a un enfant de 2 ans produit deux lignes.
    """
    periode = periode or date.today().strftime("%Y%m")
    compteurs: dict[tuple[str, str], int] = {}
    detail: dict[str, int] = {}
    inconnus: set[str] = set()
    enfants_moins_1an = 0

    for c in consultations:
        age = float(c.get("age_mois") or 0)
        coc = COC_FIXE_MOINS_1AN if age < 12 else COC_FIXE_PLUS_1AN
        if age < 12:
            enfants_moins_1an += 1
        for v in c.get("vaccins") or []:
            de = VACCIN_VERS_DE.get(str(v).upper())
            if not de:
                inconnus.add(str(v).upper())
                continue
            compteurs[(de, coc)] = compteurs.get((de, coc), 0) + 1
            detail[str(v).upper()] = detail.get(str(v).upper(), 0) + 1
        code_nut = c.get("nutrition_code")
        if code_nut:
            de = NUTRITION_VERS_DE.get(code_nut)
            if de:
                compteurs[(de, coc)] = compteurs.get((de, coc), 0) + 1
                detail[f"NUTRITION_{code_nut}"] = detail.get(f"NUTRITION_{code_nut}", 0) + 1

    valeurs = [
        {"dataElement": de, "categoryOptionCombo": coc, "value": str(n),
         "comment": f"BebeCare : {n} enfant(s) sur la periode"}
        for (de, coc), n in sorted(compteurs.items())
    ]

    payload = {
        "dataSet": DATASET,
        "completeDate": date.today().isoformat(),
        "period": periode,
        "orgUnit": org_unit,
        "dataValues": valeurs,
    }
    return {
        "payload": payload,
        "endpoint": f"{BASE}/api/dataValueSets",
        "methode": "POST",
        "entetes": {"Content-Type": "application/json"},
        "resume": {
            "nb_consultations": len(consultations),
            "nb_enfants_moins_1an": enfants_moins_1an,
            "nb_enfants_1an_et_plus": len(consultations) - enfants_moins_1an,
            "doses_par_vaccin": dict(sorted(detail.items())),
            "nb_lignes_dhis2": len(valeurs),
        },
        "vaccins_non_mappes": sorted(inconnus),
        "validation": valider(payload),
        "explication": (
            "Une seance de vaccination saisie une seule fois dans BebeCare "
            "devient un document dataValueSets agrege, pret pour le SNIS "
            "national. Les effectifs sont separes entre moins de 1 an et "
            "1 an et plus, comme l'exige la combinaison de categories DHIS2. "
            "C'est cette saisie unique qui supprime la double saisie "
            "papier puis DHIS2."
        ),
        "ecriture_activee": AUTORISER_PUSH,
    }
