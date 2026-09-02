"""Recupere les donnees officielles OMS (Global Health Observatory, WUENIC)
pour les 15 pays CEDEAO -> data/who_couverture.json

Licence : OMS GHO, donnees ouvertes, attribution requise.
"""
import json, os, urllib.request, time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO3 = {
    "bj": "BEN", "bf": "BFA", "cv": "CPV", "ci": "CIV", "gm": "GMB",
    "gh": "GHA", "gn": "GIN", "gw": "GNB", "lr": "LBR", "ml": "MLI",
    "ne": "NER", "ng": "NGA", "sn": "SEN", "sl": "SLE", "tg": "TGO",
}

INDICATEURS = {
    "WHS4_543": ("BCG", "Couverture BCG chez les enfants de 1 an (%)"),
    "WHS4_100": ("DTP3", "Couverture DTC3 / Pentavalent 3 chez les 1 an (%)"),
    "VACCINECOVERAGE_DTP1": ("DTP1", "Couverture DTC1 chez les 1 an (%)"),
    "WHS8_110": ("MCV1", "Couverture rougeole 1re dose chez les 1 an (%)"),
    "MCV2": ("MCV2", "Couverture rougeole 2e dose (%)"),
    "PCV3": ("PCV3", "Couverture pneumocoque 3 doses (%)"),
    "ROTAC": ("ROTA", "Couverture rotavirus schema complet (%)"),
    "VACCINECOVERAGE_YFV": ("YFV", "Couverture fievre jaune (%)"),
    "MDG_0000000007": ("U5MR", "Mortalite des moins de 5 ans (p. 1000 naissances vivantes)"),
    "NUTRITION_WH_2": ("WASTING", "Emaciation chez les moins de 5 ans (%)"),
    "NUTRITION_HA_2": ("STUNTING", "Retard de croissance chez les moins de 5 ans (%)"),
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BebeCare/2.0 (student project)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def main():
    sortie = {c: {"iso3": i, "indicateurs": {}} for c, i in ISO3.items()}
    for code, (court, libelle) in INDICATEURS.items():
        url = f"https://ghoapi.azureedge.net/api/{code}"
        try:
            data = get(url)["value"]
        except Exception as e:  # noqa: BLE001
            print("! echec", code, e)
            continue
        par_pays = {}
        for row in data:
            if row.get("SpatialDimType") != "COUNTRY":
                continue
            if row.get("Dim1") not in (None, "BTSX", "SEX_BTSX", "TOTL"):
                continue
            sp, an, val = row.get("SpatialDim"), row.get("TimeDim"), row.get("NumericValue")
            if val is None or an is None:
                continue
            prec = par_pays.get(sp)
            if prec is None or an > prec[0]:
                par_pays[sp] = (an, float(val))
        n = 0
        for c, iso3 in ISO3.items():
            if iso3 in par_pays:
                an, val = par_pays[iso3]
                sortie[c]["indicateurs"][court] = {
                    "libelle": libelle, "annee": an, "valeur": round(val, 1),
                    "code_oms": code,
                }
                n += 1
        print(f"{court:8s} {n}/15 pays")
        time.sleep(1)

    json.dump({
        "source": "Organisation mondiale de la Sante - Global Health Observatory (WUENIC / UNICEF-WHO)",
        "url": "https://www.who.int/data/gho",
        "recupere_le": time.strftime("%Y-%m-%d"),
        "pays": sortie,
    }, open(os.path.join(RACINE, "data", "who_couverture.json"), "w"),
        ensure_ascii=False, indent=1)
    print("ecrit data/who_couverture.json")


if __name__ == "__main__":
    main()
