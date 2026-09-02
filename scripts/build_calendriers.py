"""Construit les calendriers vaccinaux officiels des 15 pays CEDEAO
a partir du jeu de donnees OMS/UNICEF WIISE "Vaccine schedule".

Source : WHO Immunization Data portal (immunizationdata.who.int),
fichier vaccine-schedule-data.xlsx, mis a jour annuellement.
Sortie : data/calendriers.json
"""
import json, os, re, urllib.request
import openpyxl

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = ("https://srhdpeuwpubsa-geecgzbpd5h0fueu.z01.azurefd.net/"
       "whdh/WIISE/export/vaccine-schedule-data.xlsx")
XLSX = "/tmp/vaccine-schedule-data.xlsx"

ISO3 = {"BEN": "bj", "BFA": "bf", "CPV": "cv", "CIV": "ci", "GMB": "gm",
        "GHA": "gh", "GIN": "gn", "GNB": "gw", "LBR": "lr", "MLI": "ml",
        "NER": "ne", "NGA": "ng", "SEN": "sn", "SLE": "sl", "TGO": "tg"}

# Traduction FR des vaccins les plus courants (affichage parent)
FR = {
    "BCG": "BCG (tuberculose)",
    "HEPB": "Hepatite B",
    "HEPB_BD": "Hepatite B (dose de naissance)",
    "OPV": "Polio oral (VPO)",
    "IPV": "Polio injectable (VPI)",
    "DTPCV": "DTC (diphterie-tetanos-coqueluche)",
    "PENTA": "Pentavalent (DTC-HepB-Hib)",
    "PCV": "Pneumocoque",
    "ROTA": "Rotavirus",
    "MCV": "Rougeole",
    "MR": "Rougeole-Rubeole (RR)",
    "MMR": "ROR (rougeole-oreillons-rubeole)",
    "YFV": "Fievre jaune",
    "YF": "Fievre jaune",
    "MEASLES": "Rougeole",
    "MEN": "Meningite A",
    "MENA": "Meningite A",
    "MENACWY": "Meningite ACWY",
    "HPV": "HPV (papillomavirus)",
    "TT": "Tetanos",
    "TD": "Tetanos-diphterie",
    "VITA": "Vitamine A",
    "MALARIA": "Paludisme (R21 / RTS,S)",
    "TYPHOID": "Typhoide",
    "COVID19": "COVID-19",
    "RABIES": "Rage",
    "CHOLERA": "Cholera",
    "JE": "Encephalite japonaise",
}


def libelle_fr(code, description):
    c = (code or "").upper()
    # cas composites d'abord (le plus specifique gagne)
    if "DTWP" in c or "DTAP" in c or c.startswith("DTP"):
        if "HIB" in c and "HEPB" in c and "IPV" in c:
            return "Hexavalent (DTC-HepB-Hib-VPI)"
        if "HIB" in c and "HEPB" in c:
            return "Pentavalent (DTC-HepB-Hib)"
        if "HIB" in c:
            return "Tetravalent (DTC-Hib)"
        return "DTC (diphterie-tetanos-coqueluche)"
    for cle, val in FR.items():
        if c.startswith(cle):
            return val
    return description or code


def parse_age(a):
    """'B' naissance, 'W6' 6 semaines, 'M9' 9 mois, 'Y2' 2 ans -> (jours, libelle FR)."""
    if not a:
        return None, "non precise"
    a = str(a).strip().upper()
    if a in ("B", "BIRTH"):
        return 0, "A la naissance"
    m = re.match(r"^([BWMYD])[\s\-]?(\d+(?:\.\d+)?)", a)
    if not m:
        return None, a
    unite, n = m.group(1), float(m.group(2))
    if unite == "D":
        return int(n), f"{int(n)} jour(s)"
    if unite == "W":
        return int(n * 7), f"{int(n)} semaines"
    if unite == "M":
        return int(n * 30.4375), f"{int(n)} mois"
    if unite == "Y":
        return int(n * 365.25), f"{int(n)} an(s)"
    return None, a


def main():
    if not os.path.exists(XLSX):
        req = urllib.request.Request(URL, headers={"User-Agent": "BebeCare/2.0 (student project)"})
        with urllib.request.urlopen(req, timeout=180) as r, open(XLSX, "wb") as f:
            f.write(r.read())

    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Data"]
    lignes = ws.iter_rows(values_only=True)
    entete = [str(c) for c in next(lignes)]
    idx = {c: i for i, c in enumerate(entete)}
    n_col = len(entete)

    def cell(row, nom):
        i = idx[nom]
        return row[i] if i < len(row) else None

    brut = {c: [] for c in ISO3.values()}
    annees = {}
    for row in lignes:
        iso = cell(row, "ISO_3_CODE")
        if iso not in ISO3:
            continue
        code_pays = ISO3[iso]
        an = cell(row, "YEAR")
        annees[code_pays] = max(annees.get(code_pays, 0), an or 0)
        brut[code_pays].append(row)

    calendriers = {}
    for code_pays, lignes_pays in brut.items():
        an_max = annees.get(code_pays, 0)
        doses = []
        for row in lignes_pays:
            if cell(row, "YEAR") != an_max:
                continue
            cible = (cell(row, "TARGETPOP_DESCRIPTION") or "").lower()
            if "risk" in cible or "campaign" in cible:
                continue  # on garde le calendrier de routine
            jours, lib_age = parse_age(cell(row, "AGEADMINISTERED"))
            if jours is None or jours > 6 * 365:
                continue
            vcode = str(cell(row, "VACCINECODE") or "")
            doses.append({
                "vaccin": vcode,
                "nom": libelle_fr(vcode, cell(row, "VACCINE_DESCRIPTION")),
                "dose": cell(row, "SCHEDULEROUNDS") or 1,
                "jours": jours,
                "age": lib_age,
                "zone": cell(row, "GEOAREA") or "NATIONAL",
            })
        doses.sort(key=lambda d: (d["jours"], d["nom"], d["dose"]))
        calendriers[code_pays] = {
            "annee": an_max,
            "nb_doses": len(doses),
            "doses": doses,
        }
        print(f"{code_pays}: {len(doses)} doses (schema {an_max})")

    json.dump({
        "source": "OMS/UNICEF - WHO Immunization Data portal, jeu de donnees "
                  "\"Vaccine schedule\" (WIISE)",
        "url": "https://immunizationdata.who.int/global?topic=Vaccination-schedule",
        "note": "Calendrier national de routine, doses jusqu'a 6 ans. "
                "Les campagnes et groupes a risque sont exclus.",
        "pays": calendriers,
    }, open(os.path.join(RACINE, "data", "calendriers.json"), "w"),
        ensure_ascii=False, separators=(",", ":"))
    print("ecrit data/calendriers.json")


if __name__ == "__main__":
    main()
