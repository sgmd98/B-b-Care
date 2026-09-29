"""Comptes utilisateurs, enfants et suivi longitudinal.

Choix d'architecture :
  - SQLite (module standard sqlite3) : aucune dependance externe, un seul
    fichier, suffisant pour un prototype et deployable sur une instance gratuite.
  - Mots de passe : PBKDF2-HMAC-SHA256, 240 000 iterations, sel aleatoire par
    utilisateur (recommandation OWASP).
  - Jetons : jeton signe HMAC-SHA256 (meme principe qu'un JWT, sans dependance),
    duree de vie 30 jours.

IMPORTANT : le compte est TOUJOURS facultatif. Tous les outils cliniques
(carte, calendrier, depistage, triage) fonctionnent sans inscription. Le compte
sert uniquement a synchroniser le suivi d'un enfant entre plusieurs appareils.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
from contextlib import contextmanager

try:
    from . import bd
except ImportError:
    import bd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BDD = os.environ.get("BEBECARE_DB", os.path.join(RACINE, "data", "bebecare.db"))
DUREE_JETON = 30 * 24 * 3600
ITERATIONS = 240_000

# Bornes de saisie : elles evitent qu'un mot de passe de 10 Mo fasse tourner
# PBKDF2 pendant des minutes (deni de service par le calcul).
IDENT_MIN, IDENT_MAX = 5, 190
MDP_MIN, MDP_MAX = 8, 200
NOM_MAX = 120

# ------------------------------------------------------------------- SECRET
# Sans BEBECARE_SECRET, l'application genere un secret aleatoire par processus
# au lieu d'utiliser un secret de demonstration connu de tous (avec lequel
# n'importe qui pourrait fabriquer un jeton valide). Consequence : les sessions
# ne survivent pas a un redemarrage, ce qui est le bon compromis.
_SECRET_ENV = os.environ.get("BEBECARE_SECRET", "").strip()
if _SECRET_ENV:
    SECRET = _SECRET_ENV.encode()
else:
    SECRET = secrets.token_bytes(48)
    print("[bebecare] ATTENTION : BEBECARE_SECRET n'est pas definie. Un secret "
          "aleatoire a ete genere pour ce processus : les sessions en cours "
          "seront invalidees au redemarrage. Definissez la variable pour un "
          "service en production.", file=sys.stderr)


# ------------------------------------------------------------------ SCHEMA

SCHEMA = """
CREATE TABLE IF NOT EXISTS utilisateurs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  identifiant   TEXT UNIQUE NOT NULL,      -- email ou numero de telephone
  nom           TEXT,
  pays          TEXT NOT NULL DEFAULT 'bj',
  langue        TEXT NOT NULL DEFAULT 'fr',
  role          TEXT NOT NULL DEFAULT 'parent',  -- parent | soignant
  sel           TEXT NOT NULL,
  empreinte     TEXT NOT NULL,
  cree_le       TEXT NOT NULL,
  vu_le         TEXT,
  consentement_version TEXT,               -- version de la politique acceptee
  consentement_le      TEXT,               -- horodatage du consentement
  mdp_modifie_le       TEXT,               -- date du dernier changement (audit)
  generation           INTEGER NOT NULL DEFAULT 0  -- incrementee a chaque
                                           -- changement : invalide les jetons
);

CREATE TABLE IF NOT EXISTS enfants (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  utilisateur_id    INTEGER NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
  prenom            TEXT NOT NULL,
  sexe              TEXT NOT NULL DEFAULT 'm',
  date_naissance    TEXT NOT NULL,
  pays              TEXT,
  vaccins_faits     TEXT NOT NULL DEFAULT '[]',
  cree_le           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mesures (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  enfant_id    INTEGER NOT NULL REFERENCES enfants(id) ON DELETE CASCADE,
  date_mesure  TEXT NOT NULL,
  age_mois     REAL NOT NULL,
  poids_kg     REAL,
  taille_cm    REAL,
  pb_mm        REAL,
  z_pa         REAL,
  z_ta         REAL,
  z_pt         REAL,
  verdict      TEXT,
  cree_le      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_enfants_user ON enfants(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_mesures_enfant ON mesures(enfant_id);
"""

# Colonnes ajoutees apres la premiere mise en ligne : la migration est
# idempotente et fonctionne a l'identique en SQLite et en PostgreSQL.
MIGRATIONS = {
    "utilisateurs": [
        ("consentement_version", "TEXT"),
        ("consentement_le", "TEXT"),
        ("mdp_modifie_le", "TEXT"),
        ("generation", "INTEGER NOT NULL DEFAULT 0"),
    ],
}


def _colonnes(con, table: str) -> set[str]:
    """Noms des colonnes existantes, sans jamais provoquer d'erreur SQL.

    Indispensable sur PostgreSQL : une instruction en echec annule toute la
    transaction en cours, donc on interroge le catalogue au lieu de tenter
    un ALTER TABLE a l'aveugle.
    """
    if bd.moteur() == "postgresql":
        lignes = con.execute(
            "SELECT column_name AS n FROM information_schema.columns"
            " WHERE table_name=?", (table,)).fetchall()
        return {l["n"] for l in lignes}
    return {l[1] for l in con.execute(f"PRAGMA table_info({table})").fetchall()}


def _migrer(con):
    for table, colonnes in MIGRATIONS.items():
        existantes = _colonnes(con, table)
        for nom, type_sql in colonnes:
            if nom not in existantes:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {nom} {type_sql}")


# La connexion est deleguee a api/bd.py : SQLite en local, PostgreSQL (Neon)
# des que DATABASE_URL est definie. Aucune requete de ce fichier ne change.
connexion = bd.connexion


def initialiser():
    with connexion() as con:
        con.executescript(SCHEMA)
        _migrer(con)


# ------------------------------------------------------------- MOTS DE PASSE

def hacher(mdp: str, sel: str | None = None) -> tuple[str, str]:
    sel = sel or secrets.token_hex(16)
    emp = hashlib.pbkdf2_hmac("sha256", mdp.encode(), sel.encode(), ITERATIONS)
    return sel, base64.b64encode(emp).decode()


def verifier_mdp(mdp: str, sel: str, empreinte: str) -> bool:
    _, calc = hacher(mdp, sel)
    return hmac.compare_digest(calc, empreinte)


# ------------------------------------------------------------------ JETONS

def _b64(donnees: bytes) -> str:
    return base64.urlsafe_b64encode(donnees).decode().rstrip("=")


def _deb64(texte: str) -> bytes:
    return base64.urlsafe_b64decode(texte + "=" * (-len(texte) % 4))


def generation(uid: int) -> int:
    """Numero de generation des jetons de ce compte.

    Il est incremente a chaque changement de mot de passe : tous les jetons
    emis avant portent une generation plus ancienne et deviennent inutilisables,
    sans dependre d'une comparaison d'horloges (toujours fragile).
    """
    with connexion() as con:
        ligne = con.execute("SELECT generation FROM utilisateurs WHERE id=?",
                            (uid,)).fetchone()
    if not ligne:
        return 0
    valeur = ligne["generation"]
    return int(valeur or 0)


def creer_jeton(utilisateur_id: int, gen: int | None = None) -> str:
    maintenant = int(time.time())
    charge = _b64(json.dumps({"uid": utilisateur_id, "iat": maintenant,
                              "gen": generation(utilisateur_id) if gen is None else gen,
                              "exp": maintenant + DUREE_JETON}).encode())
    signature = _b64(hmac.new(SECRET, charge.encode(), hashlib.sha256).digest())
    return f"{charge}.{signature}"


def lire_jeton_complet(jeton: str | None) -> dict | None:
    """Verifie la signature et l'expiration, puis renvoie la charge utile."""
    if not jeton or len(jeton) > 4000:
        return None
    try:
        charge, signature = jeton.split(".")
        attendu = _b64(hmac.new(SECRET, charge.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, attendu):
            return None
        d = json.loads(_deb64(charge))
        if int(d["exp"]) < time.time():
            return None
        if int(d.get("iat", 0)) > time.time() + 300:      # horloge incoherente
            return None
        return {"uid": int(d["uid"]), "iat": int(d.get("iat", 0)),
                "gen": int(d.get("gen", 0)), "exp": int(d["exp"])}
    except Exception:  # noqa: BLE001
        return None


def lire_jeton(jeton: str | None) -> int | None:
    charge = lire_jeton_complet(jeton)
    return int(charge["uid"]) if charge else None


def jeton_encore_valide(charge: dict | None) -> bool:
    """Un jeton emis avant un changement de mot de passe, ou appartenant a un
    compte supprime, ne doit plus donner acces a quoi que ce soit."""
    if not charge:
        return False
    with connexion() as con:
        u = con.execute("SELECT generation FROM utilisateurs WHERE id=?",
                        (charge["uid"],)).fetchone()
    if not u:
        return False
    return int(u["generation"] or 0) == charge.get("gen", 0)


# ------------------------------------------------------------ UTILISATEURS

def normaliser(identifiant: str) -> str:
    return identifiant.strip().lower().replace(" ", "")


def _valider_identifiant(identifiant: str) -> str:
    identifiant = normaliser(identifiant)
    if not (IDENT_MIN <= len(identifiant) <= IDENT_MAX):
        raise ValueError("identifiant trop court (email ou numéro de téléphone)")
    # Lettres, chiffres et ponctuation d'adresse ou de numero uniquement :
    # rien qui puisse servir a injecter du contenu ou a tromper l'affichage.
    if not re.fullmatch(r"[a-z0-9._+@\-]+", identifiant):
        raise ValueError("identifiant invalide : utilisez un email ou un "
                         "numéro de téléphone, sans espace ni symbole")
    return identifiant


def _valider_mdp(mdp: str) -> str:
    if not isinstance(mdp, str) or len(mdp) < MDP_MIN:
        raise ValueError("le mot de passe doit faire au moins 8 caractères")
    if len(mdp) > MDP_MAX:
        raise ValueError("le mot de passe ne peut pas dépasser 200 caractères")
    return mdp


def inscrire(identifiant: str, mdp: str, pays: str, langue: str,
             nom: str | None = None, role: str = "parent",
             consentement_version: str | None = None) -> dict:
    identifiant = _valider_identifiant(identifiant)
    mdp = _valider_mdp(mdp)
    if role not in ("parent", "soignant"):
        raise ValueError("profil inconnu")
    if langue not in ("fr", "en"):
        raise ValueError("langue inconnue")
    nom = (nom or "").strip()[:NOM_MAX] or None
    sel, emp = hacher(mdp)
    version = (consentement_version or "").strip()[:40] or None
    with connexion() as con:
        if con.execute("SELECT 1 FROM utilisateurs WHERE identifiant=?",
                       (identifiant,)).fetchone():
            raise ValueError("un compte existe déjà avec cet identifiant")
        cur = con.execute(
            "INSERT INTO utilisateurs (identifiant, nom, pays, langue, role, sel,"
            " empreinte, cree_le, consentement_version, consentement_le)"
            " VALUES (?,?,?,?,?,?,?,datetime('now'),?,datetime('now'))",
            (identifiant, nom, pays, langue, role, sel, emp, version))
        uid = cur.lastrowid
    return {"jeton": creer_jeton(uid), "utilisateur": profil(uid)}


def connecter(identifiant: str, mdp: str) -> dict:
    identifiant = normaliser(identifiant)[:IDENT_MAX]
    if not isinstance(mdp, str) or not (0 < len(mdp) <= MDP_MAX):
        raise ValueError("identifiant ou mot de passe incorrect")
    with connexion() as con:
        u = con.execute("SELECT * FROM utilisateurs WHERE identifiant=?",
                        (identifiant,)).fetchone()
        if not u or not verifier_mdp(mdp, u["sel"], u["empreinte"]):
            raise ValueError("identifiant ou mot de passe incorrect")
        con.execute("UPDATE utilisateurs SET vu_le=datetime('now') WHERE id=?",
                    (u["id"],))
    return {"jeton": creer_jeton(u["id"]), "utilisateur": profil(u["id"])}


def profil(uid: int) -> dict | None:
    with connexion() as con:
        u = con.execute(
            "SELECT id, identifiant, nom, pays, langue, role, cree_le,"
            " consentement_version, consentement_le"
            " FROM utilisateurs WHERE id=?", (uid,)).fetchone()
    return dict(u) if u else None


def modifier_profil(uid: int, **champs) -> dict:
    """Mise a jour du profil. Les valeurs sont bornees et verifiees : le role
    et la langue ne peuvent prendre qu'une valeur connue."""
    permis = {}
    for k in ("nom", "pays", "langue", "role"):
        v = champs.get(k)
        if v is None:
            continue
        if k == "role" and v not in ("parent", "soignant"):
            raise ValueError("profil inconnu")
        if k == "langue" and v not in ("fr", "en"):
            raise ValueError("langue inconnue")
        if k == "nom":
            v = str(v).strip()[:NOM_MAX]
        if k == "pays":
            v = str(v).strip().lower()[:4]
        permis[k] = v
    if permis:
        with connexion() as con:
            con.execute(
                f"UPDATE utilisateurs SET {','.join(f'{k}=?' for k in permis)} WHERE id=?",
                (*permis.values(), uid))
    return profil(uid)


def changer_mot_de_passe(uid: int, ancien: str, nouveau: str) -> bool:
    """Change le mot de passe et invalide toutes les sessions anterieures."""
    nouveau = _valider_mdp(nouveau)
    with connexion() as con:
        u = con.execute("SELECT sel, empreinte FROM utilisateurs WHERE id=?",
                        (uid,)).fetchone()
        if not u or not verifier_mdp(ancien, u["sel"], u["empreinte"]):
            raise ValueError("mot de passe actuel incorrect")
        sel, emp = hacher(nouveau)
        con.execute("UPDATE utilisateurs SET sel=?, empreinte=?,"
                    " mdp_modifie_le=datetime('now'), generation=generation+1"
                    " WHERE id=?", (sel, emp, uid))
    return True


def enregistrer_consentement(uid: int, version: str) -> dict:
    with connexion() as con:
        con.execute("UPDATE utilisateurs SET consentement_version=?,"
                    " consentement_le=datetime('now') WHERE id=?",
                    (version.strip()[:40], uid))
    return profil(uid)


# ---------------------------------------------------- DROITS DES PERSONNES

def exporter(uid: int) -> dict:
    """Droit a la portabilite : tout ce qui est conserve, en clair et lisible."""
    p = profil(uid)
    if not p:
        return {}
    enfants = lister_enfants(uid)
    for e in enfants:
        e["mesures"] = historique(uid, e["id"])
    return {
        "exporte_le": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "format": "BebeCare, export des donnees personnelles (v1)",
        "compte": p,
        "enfants": enfants,
    }


def supprimer_compte(uid: int, mot_de_passe: str) -> bool:
    """Droit a l'effacement : supprime le compte et tout ce qui en depend."""
    with connexion() as con:
        u = con.execute("SELECT sel, empreinte FROM utilisateurs WHERE id=?",
                        (uid,)).fetchone()
        if not u or not verifier_mdp(mot_de_passe, u["sel"], u["empreinte"]):
            raise ValueError("mot de passe incorrect")
        con.execute("DELETE FROM enfants WHERE utilisateur_id=?", (uid,))
        con.execute("DELETE FROM utilisateurs WHERE id=?", (uid,))
    return True


# ---------------------------------------------------------------- ENFANTS

def lister_enfants(uid: int) -> list[dict]:
    with connexion() as con:
        lignes = con.execute(
            "SELECT * FROM enfants WHERE utilisateur_id=? ORDER BY cree_le",
            (uid,)).fetchall()
    out = []
    for l in lignes:
        d = dict(l)
        d["vaccins_faits"] = json.loads(d["vaccins_faits"])
        out.append(d)
    return out


def creer_enfant(uid: int, prenom: str, sexe: str, date_naissance: str,
                 pays: str | None = None) -> dict:
    with connexion() as con:
        cur = con.execute(
            "INSERT INTO enfants (utilisateur_id, prenom, sexe, date_naissance,"
            " pays, cree_le) VALUES (?,?,?,?,?,datetime('now'))",
            (uid, prenom.strip(), sexe, date_naissance, pays))
        eid = cur.lastrowid
    return obtenir_enfant(uid, eid)


def obtenir_enfant(uid: int, eid: int) -> dict | None:
    with connexion() as con:
        l = con.execute("SELECT * FROM enfants WHERE id=? AND utilisateur_id=?",
                        (eid, uid)).fetchone()
    if not l:
        return None
    d = dict(l)
    d["vaccins_faits"] = json.loads(d["vaccins_faits"])
    return d


def modifier_enfant(uid: int, eid: int, **champs) -> dict | None:
    if not obtenir_enfant(uid, eid):
        return None
    permis = {}
    for k in ("prenom", "sexe", "date_naissance", "pays"):
        if champs.get(k) is not None:
            permis[k] = champs[k]
    if champs.get("vaccins_faits") is not None:
        permis["vaccins_faits"] = json.dumps(champs["vaccins_faits"])
    if permis:
        with connexion() as con:
            con.execute(
                f"UPDATE enfants SET {','.join(f'{k}=?' for k in permis)}"
                " WHERE id=? AND utilisateur_id=?",
                (*permis.values(), eid, uid))
    return obtenir_enfant(uid, eid)


def supprimer_enfant(uid: int, eid: int) -> bool:
    with connexion() as con:
        cur = con.execute("DELETE FROM enfants WHERE id=? AND utilisateur_id=?",
                          (eid, uid))
    return cur.rowcount > 0


# ---------------------------------------------------------------- MESURES

def ajouter_mesure(uid: int, eid: int, mesure: dict) -> dict | None:
    if not obtenir_enfant(uid, eid):
        return None
    with connexion() as con:
        con.execute(
            "INSERT INTO mesures (enfant_id, date_mesure, age_mois, poids_kg,"
            " taille_cm, pb_mm, z_pa, z_ta, z_pt, verdict, cree_le)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))",
            (eid, mesure.get("date_mesure"), mesure.get("age_mois"),
             mesure.get("poids_kg"), mesure.get("taille_cm"), mesure.get("pb_mm"),
             mesure.get("z_pa"), mesure.get("z_ta"), mesure.get("z_pt"),
             mesure.get("verdict")))
    return {"ok": True}


def historique(uid: int, eid: int) -> list[dict]:
    if not obtenir_enfant(uid, eid):
        return []
    with connexion() as con:
        lignes = con.execute(
            "SELECT * FROM mesures WHERE enfant_id=? ORDER BY date_mesure",
            (eid,)).fetchall()
    return [dict(l) for l in lignes]


def statistiques() -> dict:
    with connexion() as con:
        u = con.execute("SELECT COUNT(*) c FROM utilisateurs").fetchone()["c"]
        e = con.execute("SELECT COUNT(*) c FROM enfants").fetchone()["c"]
        m = con.execute("SELECT COUNT(*) c FROM mesures").fetchone()["c"]
    return {"utilisateurs": u, "enfants": e, "mesures": m}
