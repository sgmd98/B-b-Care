"""Chargement des donnees et index spatial en memoire.

Toutes les donnees sont statiques : on les charge une fois au demarrage
et on construit une grille spatiale (0,25 deg) pour les requetes carte.
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache

from .pays_meta import PAYS

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RACINE, "data")

_lieux: dict[str, list[dict]] = {}
_grille: dict[str, dict[tuple[int, int], list[int]]] = {}
_meta_pays: dict[str, dict] = {}
PAS = 0.25  # degres


def _cellule(lat: float, lon: float) -> tuple[int, int]:
    return int(math.floor(lat / PAS)), int(math.floor(lon / PAS))


def charger():
    """Charge les fichiers pays et construit l'index spatial."""
    for code in PAYS:
        chemin = os.path.join(DATA, "pays", f"{code}.json")
        if not os.path.isfile(chemin):
            continue
        with open(chemin, encoding="utf-8") as f:
            d = json.load(f)
        lieux = d.get("lieux", [])
        for i, l in enumerate(lieux):
            l["p"] = code
            l["i"] = i
        _lieux[code] = lieux
        g: dict[tuple[int, int], list[int]] = {}
        for i, l in enumerate(lieux):
            g.setdefault(_cellule(l["lat"], l["lon"]), []).append(i)
        _grille[code] = g
        _meta_pays[code] = {
            "nb": d.get("nb", len(lieux)),
            "extrait_le": d.get("extrait_le"),
            "source": d.get("source"),
        }
    return _lieux


def pays_charges() -> list[str]:
    return list(_lieux)


def lieux_de(code: str) -> list[dict]:
    return _lieux.get(code, [])


def meta_donnees(code: str) -> dict:
    return _meta_pays.get(code, {})


def total_lieux() -> int:
    return sum(len(v) for v in _lieux.values())


def repartition(code: str) -> dict[str, int]:
    r: dict[str, int] = {}
    for l in _lieux.get(code, []):
        r[l["c"]] = r.get(l["c"], 0) + 1
    return dict(sorted(r.items(), key=lambda x: -x[1]))


def dans_bbox(code: str | None, sud: float, ouest: float, nord: float, est: float,
              categories: set[str] | None = None, limite: int = 1200) -> list[dict]:
    """Lieux dans une bbox, via la grille spatiale."""
    res: list[dict] = []
    codes = [code] if code else list(_lieux)
    c0, c1 = _cellule(sud, ouest)
    c2, c3 = _cellule(nord, est)
    for cp in codes:
        g = _grille.get(cp, {})
        lieux = _lieux.get(cp, [])
        for ci in range(c0, c2 + 1):
            for cj in range(c1, c3 + 1):
                for i in g.get((ci, cj), ()):
                    l = lieux[i]
                    if not (sud <= l["lat"] <= nord and ouest <= l["lon"] <= est):
                        continue
                    if categories and l["c"] not in categories:
                        continue
                    res.append(l)
                    if len(res) >= limite:
                        return res
    return res


def distance_km(lat1, lon1, lat2, lon2) -> float:
    """Haversine."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def plus_proches(lat: float, lon: float, categories: set[str] | None = None,
                 n: int = 10, rayon_max_km: float = 150) -> list[dict]:
    """Recherche par anneaux de cellules croissants autour du point."""
    ci, cj = _cellule(lat, lon)
    trouves: list[tuple[float, dict]] = []
    anneau = 0
    while anneau <= int(rayon_max_km / (PAS * 111)) + 1:
        cellules = [
            (ci + di, cj + dj)
            for di in range(-anneau, anneau + 1)
            for dj in range(-anneau, anneau + 1)
            if max(abs(di), abs(dj)) == anneau
        ]
        for cp, g in _grille.items():
            lieux = _lieux[cp]
            for cell in cellules:
                for i in g.get(cell, ()):
                    l = lieux[i]
                    if categories and l["c"] not in categories:
                        continue
                    d = distance_km(lat, lon, l["lat"], l["lon"])
                    if d <= rayon_max_km:
                        trouves.append((d, l))
        # on continue un anneau de plus apres avoir atteint n resultats
        if len(trouves) >= n and anneau >= 2:
            break
        anneau += 1
    trouves.sort(key=lambda x: x[0])
    out = []
    for d, l in trouves[:n]:
        out.append({**l, "distance_km": round(d, 2)})
    return out


def rechercher(texte: str, code: str | None = None, limite: int = 30) -> list[dict]:
    t = texte.strip().lower()
    if len(t) < 2:
        return []
    res = []
    for cp in ([code] if code else list(_lieux)):
        for l in _lieux.get(cp, []):
            nom = (l.get("n") or "").lower()
            if t in nom:
                res.append(l)
                if len(res) >= limite:
                    return res
    return res


@lru_cache(maxsize=1)
def calendriers() -> dict:
    with open(os.path.join(DATA, "calendriers.json"), encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def couverture_oms() -> dict:
    with open(os.path.join(DATA, "who_couverture.json"), encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def tables_croissance() -> dict:
    with open(os.path.join(DATA, "who", "croissance.json"), encoding="utf-8") as f:
        return json.load(f)
