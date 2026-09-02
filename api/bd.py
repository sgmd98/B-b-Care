"""Couche d'acces base de donnees : SQLite en local, PostgreSQL (Neon) en ligne.

Pourquoi cette couche ?
  Le code metier de comptes.py est ecrit en SQL standard avec des placeholders
  SQLite (`?`). Plutot que de le reecrire, ce module traduit a la volee vers
  PostgreSQL. On garde ainsi UN SEUL jeu de requetes, testable en local sans
  serveur, et deployable sur Neon sans rien changer.

Choix du moteur : variable d'environnement DATABASE_URL.
  - absente                  -> SQLite (fichier data/bebecare.db)
  - postgres://... / postgresql://...  -> PostgreSQL via psycopg 3

Neon fournit une chaine du type :
  postgresql://user:motdepasse@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
"""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = os.environ.get("DATABASE_URL", "").strip()
FICHIER = os.environ.get("BEBECARE_DB", os.path.join(RACINE, "data", "bebecare.db"))
POSTGRES = URL.startswith(("postgres://", "postgresql://"))

if POSTGRES:
    import psycopg
    from psycopg.rows import dict_row


def moteur() -> str:
    return "postgresql" if POSTGRES else "sqlite"


# --------------------------------------------------------------- TRADUCTION

def _sql_pg(sql: str) -> str:
    """Traduit une requete ecrite pour SQLite vers PostgreSQL."""
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace("datetime('now')", "to_char(now(), 'YYYY-MM-DD\"T\"HH24:MI:SS')")
    sql = re.sub(r"\bPRAGMA[^;]*;?", "", sql, flags=re.I)
    # placeholders : ? -> %s (en ignorant ceux a l'interieur des chaines)
    out, dans_chaine = [], False
    for c in sql:
        if c == "'":
            dans_chaine = not dans_chaine
        if c == "?" and not dans_chaine:
            out.append("%s")
        else:
            out.append(c)
    return "".join(out)


class _Curseur:
    """Curseur unifie : expose fetchone/fetchall/lastrowid/rowcount."""

    def __init__(self, curseur, lastrowid=None):
        self._c = curseur
        self._lastrowid = lastrowid

    def fetchone(self):
        return self._c.fetchone()

    def fetchall(self):
        return self._c.fetchall()

    @property
    def lastrowid(self):
        return self._lastrowid if self._lastrowid is not None else self._c.lastrowid

    @property
    def rowcount(self):
        return self._c.rowcount


class _ConnexionPG:
    """Adaptateur PostgreSQL presentant l'interface de sqlite3.Connection."""

    def __init__(self, con):
        self._con = con

    def execute(self, sql: str, params=()):
        req = _sql_pg(sql)
        dernier = None
        # Pour recuperer l'equivalent de lastrowid, on ajoute RETURNING id.
        if req.lstrip().upper().startswith("INSERT") and "RETURNING" not in req.upper():
            req = req.rstrip().rstrip(";") + " RETURNING id"
            cur = self._con.execute(req, tuple(params))
            ligne = cur.fetchone()
            dernier = ligne["id"] if ligne else None
            return _Curseur(cur, dernier)
        cur = self._con.execute(req, tuple(params))
        return _Curseur(cur)

    def executescript(self, sql: str):
        for bloc in _sql_pg(sql).split(";"):
            if bloc.strip():
                self._con.execute(bloc)

    def commit(self):
        self._con.commit()

    def close(self):
        self._con.close()


@contextmanager
def connexion():
    if POSTGRES:
        con = psycopg.connect(URL, row_factory=dict_row, connect_timeout=15)
        adaptateur = _ConnexionPG(con)
        try:
            yield adaptateur
            adaptateur.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            adaptateur.close()
    else:
        dossier = os.path.dirname(FICHIER)
        if dossier:
            os.makedirs(dossier, exist_ok=True)
        con = sqlite3.connect(FICHIER, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        finally:
            con.close()


def description() -> dict:
    """Renseigne /api/sante sans jamais exposer les identifiants."""
    if POSTGRES:
        hote = URL.split("@")[-1].split("/")[0] if "@" in URL else "postgres"
        return {"moteur": "postgresql", "hote": hote, "persistant": True}
    return {"moteur": "sqlite", "fichier": os.path.basename(FICHIER), "persistant": False}
