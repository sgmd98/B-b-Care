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
import secrets
import time
from contextlib import contextmanager

try:
    from . import bd
except ImportError:
    import bd

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BDD = os.environ.get("BEBECARE_DB", os.path.join(RACINE, "data", "bebecare.db"))
SECRET = os.environ.get("BEBECARE_SECRET", "dev-secret-a-changer-en-production").encode()
DUREE_JETON = 30 * 24 * 3600
ITERATIONS = 240_000


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
  vu_le         TEXT
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


# La connexion est deleguee a api/bd.py : SQLite en local, PostgreSQL (Neon)
# des que DATABASE_URL est definie. Aucune requete de ce fichier ne change.
connexion = bd.connexion


def initialiser():
    with connexion() as con:
        con.executescript(SCHEMA)


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


def creer_jeton(utilisateur_id: int) -> str:
    charge = _b64(json.dumps({"uid": utilisateur_id,
                              "exp": int(time.time()) + DUREE_JETON}).encode())
    signature = _b64(hmac.new(SECRET, charge.encode(), hashlib.sha256).digest())
    return f"{charge}.{signature}"


def lire_jeton(jeton: str | None) -> int | None:
    if not jeton:
        return None
    try:
        charge, signature = jeton.split(".")
        attendu = _b64(hmac.new(SECRET, charge.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, attendu):
            return None
        d = json.loads(_deb64(charge))
        if d["exp"] < time.time():
            return None
        return int(d["uid"])
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------ UTILISATEURS

def normaliser(identifiant: str) -> str:
    return identifiant.strip().lower().replace(" ", "")


def inscrire(identifiant: str, mdp: str, pays: str, langue: str,
             nom: str | None = None, role: str = "parent") -> dict:
    identifiant = normaliser(identifiant)
    if len(identifiant) < 5:
        raise ValueError("identifiant trop court (email ou numéro de téléphone)")
    if len(mdp) < 8:
        raise ValueError("le mot de passe doit faire au moins 8 caractères")
    sel, emp = hacher(mdp)
    with connexion() as con:
        if con.execute("SELECT 1 FROM utilisateurs WHERE identifiant=?",
                       (identifiant,)).fetchone():
            raise ValueError("un compte existe déjà avec cet identifiant")
        cur = con.execute(
            "INSERT INTO utilisateurs (identifiant, nom, pays, langue, role, sel,"
            " empreinte, cree_le) VALUES (?,?,?,?,?,?,?,datetime('now'))",
            (identifiant, nom, pays, langue, role, sel, emp))
        uid = cur.lastrowid
    return {"jeton": creer_jeton(uid), "utilisateur": profil(uid)}


def connecter(identifiant: str, mdp: str) -> dict:
    identifiant = normaliser(identifiant)
    with connexion() as con:
        u = con.execute("SELECT * FROM utilisateurs WHERE identifiant=?",
                        (identifiant,)).fetchone()
        if not u or not verifier_mdp(mdp, u["sel"], u["empreinte"]):
            raise ValueError("identifiant ou mot de passe incorrect")
        con.execute("UPDATE utilisateurs SET vu_le=datetime('now') WHERE id=?", (u["id"],))
    return {"jeton": creer_jeton(u["id"]), "utilisateur": profil(u["id"])}


def profil(uid: int) -> dict | None:
    with connexion() as con:
        u = con.execute(
            "SELECT id, identifiant, nom, pays, langue, role, cree_le"
            " FROM utilisateurs WHERE id=?", (uid,)).fetchone()
    return dict(u) if u else None


def modifier_profil(uid: int, **champs) -> dict:
    permis = {k: v for k, v in champs.items()
              if k in ("nom", "pays", "langue", "role") and v is not None}
    if permis:
        with connexion() as con:
            con.execute(
                f"UPDATE utilisateurs SET {','.join(f'{k}=?' for k in permis)} WHERE id=?",
                (*permis.values(), uid))
    return profil(uid)


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
