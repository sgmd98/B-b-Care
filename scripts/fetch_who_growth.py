"""Telecharge les tables officielles OMS Child Growth Standards (LMS)
et les compacte en JSON -> data/who/croissance.json

Indicateurs :
  wfa  poids-pour-age      (insuffisance ponderale)   0-1856 jours
  lhfa taille-pour-age     (retard de croissance)     0-1856 jours
  wfl  poids-pour-taille   (emaciation, 45-110 cm couche)
  wfh  poids-pour-taille   (emaciation, 65-120 cm debout)

Source : WHO Child Growth Standards, https://www.who.int/tools/child-growth-standards
"""
import json, os, urllib.request
import openpyxl

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(RACINE, "data", "who")
os.makedirs(DEST, exist_ok=True)
TMP = "/tmp/who_tables"
os.makedirs(TMP, exist_ok=True)

BASE = ("https://cdn.who.int/media/docs/default-source/child-growth/"
        "child-growth-standards/indicators")

FICHIERS = {
    ("wfa", "m"): "weight-for-age/expanded-tables/wfa-boys-zscore-expanded-tables.xlsx",
    ("wfa", "f"): "weight-for-age/expanded-tables/wfa-girls-zscore-expanded-tables.xlsx",
    ("lhfa", "m"): "length-height-for-age/expandable-tables/lhfa-boys-zscore-expanded-tables.xlsx",
    ("lhfa", "f"): "length-height-for-age/expandable-tables/lhfa-girls-zscore-expanded-tables.xlsx",
    ("wfl", "m"): "weight-for-length-height/expanded-tables/wfl-boys-zscore-expanded-table.xlsx",
    ("wfl", "f"): "weight-for-length-height/expanded-tables/wfl-girls-zscore-expanded-table.xlsx",
    ("wfh", "m"): "weight-for-length-height/expanded-tables/wfh-boys-zscore-expanded-tables.xlsx",
    ("wfh", "f"): "weight-for-length-height/expanded-tables/wfh-girls-zscore-expanded-tables.xlsx",
}


def telecharger(rel):
    nom = os.path.join(TMP, rel.replace("/", "_"))
    if not os.path.exists(nom):
        req = urllib.request.Request(f"{BASE}/{rel}",
                                     headers={"User-Agent": "BebeCare/2.0 (student project)"})
        with urllib.request.urlopen(req, timeout=120) as r, open(nom, "wb") as f:
            f.write(r.read())
    return nom


def lire(chemin):
    wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    ws = wb.active
    lignes = ws.iter_rows(values_only=True)
    entete = [str(c).strip().lower() if c is not None else "" for c in next(lignes)]
    i_x, i_l, i_m, i_s = 0, entete.index("l"), entete.index("m"), entete.index("s")
    out = []
    for row in lignes:
        if row[i_x] is None or row[i_l] is None:
            continue
        out.append([
            round(float(row[i_x]), 1),
            round(float(row[i_l]), 4),
            round(float(row[i_m]), 4),
            round(float(row[i_s]), 5),
        ])
    wb.close()
    return out


def main():
    total = {}
    for (indic, sexe), rel in FICHIERS.items():
        print("...", indic, sexe, flush=True)
        table = lire(telecharger(rel))
        total.setdefault(indic, {})[sexe] = table
        print(f"  {indic}/{sexe}: {len(table)} lignes ({table[0][0]} -> {table[-1][0]})")

    json.dump({
        "source": "WHO Child Growth Standards (OMS) - tables LMS officielles",
        "url": "https://www.who.int/tools/child-growth-standards/standards",
        "cles": {
            "wfa": "poids-pour-age, x = jours",
            "lhfa": "taille-pour-age, x = jours",
            "wfl": "poids-pour-taille couche (<24 mois), x = cm",
            "wfh": "poids-pour-taille debout (>=24 mois), x = cm",
        },
        "format": "[x, L, M, S]",
        "tables": total,
    }, open(os.path.join(DEST, "croissance.json"), "w"), separators=(",", ":"))
    taille = os.path.getsize(os.path.join(DEST, "croissance.json")) / 1024
    print(f"ecrit data/who/croissance.json ({taille:.0f} Ko)")


if __name__ == "__main__":
    main()
