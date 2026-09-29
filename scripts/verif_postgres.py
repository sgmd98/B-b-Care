"""Verification du chemin PostgreSQL (Neon) sans serveur PostgreSQL.

Render deploie avec DATABASE_URL vers Neon. Aucun PostgreSQL n'est disponible
dans cet environnement de travail, donc on verifie ici ce qui peut l'etre
sans base reelle :

  1. la traduction SQL SQLite -> PostgreSQL (placeholders, datetime('now'),
     suppression des PRAGMA, ajout de RETURNING id) ;
  2. la migration de schema sur PostgreSQL, avec un curseur simule qui renvoie
     les colonnes existantes : aucune instruction ALTER TABLE invalide ne doit
     partir, et une colonne manquante doit etre ajoutee ;
  3. la lecture de la generation de jetons sur une ligne PostgreSQL (dict row).

Ce que ce script ne prouve pas : le comportement du vrai serveur Neon. La
verification finale se fait sur bebecare.onrender.com apres deploiement.
"""
import sys
from contextlib import contextmanager
from unittest import mock

sys.path.insert(0, "/home/user/B-b-Care")

from api import bd, comptes          # noqa: E402

RESULTATS = []


def verifier(nom, condition, detail=""):
    RESULTATS.append((nom, bool(condition)))
    print(("OK   " if condition else "ECHEC") + " : " + nom + (f" -> {detail}" if detail and not condition else ""))


# ------------------------------------------------- 1. traduction SQL

verifier("placeholders traduits",
         bd._sql_pg("SELECT * FROM utilisateurs WHERE id=?") ==
         "SELECT * FROM utilisateurs WHERE id=%s")
verifier("datetime('now') traduit",
         "to_char(now()" in bd._sql_pg("INSERT INTO x (c) VALUES (datetime('now'))"))
verifier("PRAGMA retire",
         "PRAGMA" not in bd._sql_pg("PRAGMA foreign_keys = ON; SELECT 1"))
verifier("auto-increment traduit",
         "SERIAL PRIMARY KEY" in bd._sql_pg("id INTEGER PRIMARY KEY AUTOINCREMENT"))

insert_migration = "ALTER TABLE utilisateurs ADD COLUMN generation INTEGER NOT NULL DEFAULT 0"
verifier("migration acceptee par PostgreSQL",
         bd._sql_pg(insert_migration) == insert_migration)
verifier("increment de generation traduit",
         bd._sql_pg("UPDATE utilisateurs SET generation=generation+1 WHERE id=?")
         == "UPDATE utilisateurs SET generation=generation+1 WHERE id=%s")


# ------------------------------------ 2. connexion PostgreSQL simulee

class FauxCurseur:
    def __init__(self, lignes=None, rowcount=1):
        self._lignes = lignes or []
        self.rowcount = rowcount
        self.lastrowid = None

    def fetchone(self):
        return self._lignes[0] if self._lignes else None

    def fetchall(self):
        return self._lignes


class FausseConnexionPG:
    """Reproduit psycopg avec row_factory=dict_row : les lignes sont des dicts."""

    def __init__(self, colonnes_existantes):
        self.colonnes = colonnes_existantes
        self.requetes = []
        self.commit_appele = False

    def execute(self, sql, params=()):
        self.requetes.append((sql, params))
        if "information_schema.columns" in sql:
            return FauxCurseur([{"n": c} for c in self.colonnes])
        if sql.strip().upper().startswith("INSERT"):
            return FauxCurseur([{"id": 42}])
        if sql.strip().upper().startswith("SELECT GENERATION"):
            return FauxCurseur([{"generation": 1}])
        return FauxCurseur()

    def commit(self):
        self.commit_appele = True

    def close(self):
        pass


def _connexion_simulee(connexion_pg):
    @contextmanager
    def _ctx():
        adaptateur = bd._ConnexionPG(connexion_pg)
        yield adaptateur
        adaptateur.commit()
    return _ctx()


# ---- migration : une colonne existe, deux manquent
fausse = FausseConnexionPG(["id", "identifiant", "consentement_version"])
with mock.patch.object(bd, "POSTGRES", True), \
     mock.patch.object(bd, "connexion", lambda: _connexion_simulee(fausse)), \
     mock.patch.object(comptes, "connexion", lambda: _connexion_simulee(fausse)):
    comptes.initialiser()
    alts = [sql for sql, _ in fausse.requetes if sql.upper().startswith("ALTER TABLE")]
    verifier("colonnes deja presentes non recreees",
             all("consentement_version" not in a for a in alts), str(alts))
    verifier("colonne generation ajoutee",
             any("generation" in a and "ADD COLUMN" in a for a in alts), str(alts))
    verifier("colonne mdp_modifie_le ajoutee",
             any("mdp_modifie_le" in a for a in alts), str(alts))
    verifier("migration sans PRAGMA",
             all("PRAGMA" not in sql.upper() for sql, _ in fausse.requetes))

# ---- insertion : RETURNING id ajoute par l'adaptateur
fausse2 = FausseConnexionPG(["id"])
with mock.patch.object(bd, "POSTGRES", True), \
     mock.patch.object(bd, "connexion", lambda: _connexion_simulee(fausse2)), \
     mock.patch.object(comptes, "connexion", lambda: _connexion_simulee(fausse2)):
    r = comptes.inscrire("parent@exemple.com", "motdepasse123", "bj", "fr",
                         "Awa", "parent", "1.0")
    insertions = [sql for sql, _ in fausse2.requetes if sql.upper().startswith("INSERT")]
    verifier("RETURNING id ajoute sur INSERT", insertions and "RETURNING id" in insertions[0],
             str(insertions))
    verifier("jeton renvoye apres inscription", bool(r.get("jeton")))
    verifier("pas de datetime() non traduit",
             all("datetime('now')" not in sql for sql, _ in fausse2.requetes))
    verifier("generation lue en ligne dict", comptes.generation(1) == 1)
    verifier("jeton de generation 1 accepte",
             comptes.jeton_encore_valide({"uid": 1, "gen": 1, "iat": 0, "exp": 9e9}))
    verifier("jeton de generation 0 refuse",
             not comptes.jeton_encore_valide({"uid": 1, "gen": 0, "iat": 0, "exp": 9e9}))

print()
echecs = [n for n, ok in RESULTATS if not ok]
print(f"{len(RESULTATS) - len(echecs)}/{len(RESULTATS)} controles reussis")
if echecs:
    print("Echecs :", echecs)
    sys.exit(1)
