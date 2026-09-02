"""Extraction des structures de sante OpenStreetMap pour les 15 pays de la CEDEAO.

Source : OpenStreetMap, licence ODbL. Attribution obligatoire dans l'app.
Sortie : data/pays/<code>.json  (+ data/index_pays.json)
"""
import json, os, sys, time, urllib.parse, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "data", "pays")
os.makedirs(SORTIE, exist_ok=True)

# 15 pays CEDEAO + langue officielle dominante
PAYS = [
    ("bj", "BJ", "Benin", "fr"),
    ("bf", "BF", "Burkina Faso", "fr"),
    ("cv", "CV", "Cabo Verde", "pt"),
    ("ci", "CI", "Cote d'Ivoire", "fr"),
    ("gm", "GM", "Gambie", "en"),
    ("gh", "GH", "Ghana", "en"),
    ("gn", "GN", "Guinee", "fr"),
    ("gw", "GW", "Guinee-Bissau", "pt"),
    ("lr", "LR", "Liberia", "en"),
    ("ml", "ML", "Mali", "fr"),
    ("ne", "NE", "Niger", "fr"),
    ("ng", "NG", "Nigeria", "en"),
    ("sn", "SN", "Senegal", "fr"),
    ("sl", "SL", "Sierra Leone", "en"),
    ("tg", "TG", "Togo", "fr"),
]

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

REQUETE = """[out:json][timeout:600];
area["ISO3166-1"="%s"][admin_level=2]->.a;
(
  nwr["amenity"~"^(hospital|clinic|doctors|pharmacy)$"](area.a);
  nwr["healthcare"](area.a);
);
out center tags;"""


def categorie(tags):
    """Classe le lieu en categories utiles a une mere avec un enfant de 0-5 ans."""
    a = tags.get("amenity", "")
    h = tags.get("healthcare", "")
    if a == "pharmacy" or h == "pharmacy":
        return "pharmacie"
    if a == "hospital" or h == "hospital":
        return "hopital"
    if h in ("centre", "center", "health_post", "dispensary") or a == "clinic":
        return "centre_sante"
    if h == "midwife" or tags.get("healthcare:speciality", "").find("obstetrics") >= 0:
        return "maternite"
    if h == "laboratory":
        return "laboratoire"
    if a == "doctors" or h == "doctor":
        return "medecin"
    return "sante_autre"


def vaccination(tags):
    """Indice : le lieu declare-t-il faire de la vaccination ?"""
    champs = " ".join([
        tags.get("healthcare:speciality", ""),
        tags.get("health_specialty:vaccination", ""),
        tags.get("name", "").lower(),
    ]).lower()
    return "vaccination" in champs or "vaccin" in champs


def interroger(iso):
    err = None
    for ep in ENDPOINTS:
        for essai in range(3):
            try:
                req = urllib.request.Request(
                    ep,
                    data=urllib.parse.urlencode({"data": REQUETE % iso}).encode(),
                    headers={"User-Agent": "BebeCare/2.0 (student hackathon project; OSM ODbL)"},
                )
                with urllib.request.urlopen(req, timeout=650) as r:
                    return json.loads(r.read())
            except Exception as e:  # noqa: BLE001
                err = e
                print(f"   ! {ep} essai {essai+1}: {e}", flush=True)
                time.sleep(20)
    raise RuntimeError(f"echec {iso}: {err}")


def main():
    index = []
    for code, iso, nom, langue in PAYS:
        chemin = os.path.join(SORTIE, f"{code}.json")
        if os.path.exists(chemin) and os.path.getsize(chemin) > 200:
            d = json.load(open(chemin))
            print(f"= {nom}: deja fait ({d['nb']})", flush=True)
            index.append({"code": code, "iso": iso, "nom": nom, "langue": langue, "nb": d["nb"]})
            continue
        print(f"> {nom} ({iso}) ...", flush=True)
        t0 = time.time()
        brut = interroger(iso)
        lieux, vus = [], set()
        for el in brut.get("elements", []):
            tags = el.get("tags", {}) or {}
            lat = el.get("lat") or (el.get("center") or {}).get("lat")
            lon = el.get("lon") or (el.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            nom_l = tags.get("name") or tags.get("name:fr") or tags.get("name:en")
            cle = (round(lat, 5), round(lon, 5), (nom_l or "").lower())
            if cle in vus:
                continue
            vus.add(cle)
            lieux.append({
                "id": f"{el['type'][0]}{el['id']}",
                "n": nom_l,
                "c": categorie(tags),
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "tel": tags.get("phone") or tags.get("contact:phone"),
                "v": tags.get("addr:city"),
                "op": tags.get("operator"),
                "h": tags.get("opening_hours"),
                "vac": vaccination(tags),
                "urg": tags.get("emergency") == "yes",
            })
        lieux.sort(key=lambda x: (x["c"], x["n"] or "zzz"))
        json.dump(
            {
                "pays": code, "iso": iso, "nom": nom, "langue": langue,
                "source": "OpenStreetMap contributors (ODbL 1.0)",
                "extrait_le": time.strftime("%Y-%m-%d"),
                "nb": len(lieux), "lieux": lieux,
            },
            open(chemin, "w"), ensure_ascii=False, separators=(",", ":"),
        )
        print(f"  {nom}: {len(lieux)} lieux en {round(time.time()-t0)}s", flush=True)
        index.append({"code": code, "iso": iso, "nom": nom, "langue": langue, "nb": len(lieux)})
        json.dump(index, open(os.path.join(RACINE, "data", "index_pays.json"), "w"),
                  ensure_ascii=False, indent=1)
        time.sleep(8)

    json.dump(index, open(os.path.join(RACINE, "data", "index_pays.json"), "w"),
              ensure_ascii=False, indent=1)
    print("TOTAL", sum(p["nb"] for p in index), flush=True)


if __name__ == "__main__":
    main()
