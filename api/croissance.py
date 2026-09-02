"""Depistage nutritionnel : z-scores OMS (LMS) + classification OMS/PCIMA.

Indicateurs calcules :
  - P/A  (poids-pour-age)    -> insuffisance ponderale
  - T/A  (taille-pour-age)   -> retard de croissance (malnutrition chronique)
  - P/T  (poids-pour-taille) -> emaciation (malnutrition aigue)  <- le plus urgent
  - PB   (perimetre brachial) -> seuils OMS 115 / 125 mm

Reference : WHO Child Growth Standards (2006) + WHO/UNICEF 2009
"Standards de croissance et identification de la malnutrition aigue severe".
"""
from __future__ import annotations

import bisect
from typing import Literal

from .donnees import tables_croissance


def _interp(table: list[list[float]], x: float) -> tuple[float, float, float] | None:
    """Renvoie (L, M, S) interpole lineairement pour l'abscisse x."""
    if not table:
        return None
    xs = [r[0] for r in table]
    if x < xs[0] or x > xs[-1]:
        return None
    i = bisect.bisect_left(xs, x)
    if i < len(xs) and xs[i] == x:
        r = table[i]
        return r[1], r[2], r[3]
    a, b = table[i - 1], table[i]
    t = (x - a[0]) / (b[0] - a[0])
    return (a[1] + t * (b[1] - a[1]),
            a[2] + t * (b[2] - a[2]),
            a[3] + t * (b[3] - a[3]))


def zscore(valeur: float, L: float, M: float, S: float) -> float:
    """Formule LMS de Cole. Les queues (|z|>3) sont ajustees selon la
    methode officielle OMS (igrowup) pour eviter les z-scores aberrants."""
    if L == 0:
        z = (valeur / M) ** 0.0
        z = (valeur - M) / (M * S)
    else:
        z = ((valeur / M) ** L - 1) / (L * S)

    def val_a_z(zz: float) -> float:
        if L == 0:
            return M * (1 + S * zz)
        return M * (1 + L * S * zz) ** (1 / L)

    if z > 3:
        sd3, sd2 = val_a_z(3), val_a_z(2)
        z = 3 + (valeur - sd3) / (sd3 - sd2)
    elif z < -3:
        sdm3, sdm2 = val_a_z(-3), val_a_z(-2)
        z = -3 + (valeur - sdm3) / (sdm2 - sdm3)
    return z


def _calc(indicateur: str, sexe: str, x: float, valeur: float) -> float | None:
    t = tables_croissance()["tables"].get(indicateur, {}).get(sexe)
    lms = _interp(t, x) if t else None
    if lms is None:
        return None
    return round(zscore(valeur, *lms), 2)


def evaluer(age_mois: float, sexe: Literal["m", "f"], poids_kg: float | None = None,
            taille_cm: float | None = None, pb_mm: float | None = None,
            oedemes: bool = False) -> dict:
    jours = age_mois * 30.4375
    res: dict = {"age_mois": round(age_mois, 1), "sexe": sexe, "indicateurs": {}}
    alertes: list[dict] = []

    # --- Poids pour age ---
    if poids_kg:
        z = _calc("wfa", sexe, jours, poids_kg)
        if z is not None:
            res["indicateurs"]["poids_age"] = {
                "z": z, "libelle": "Poids-pour-âge (insuffisance pondérale)",
                "classe": _classe_pa(z),
            }

    # --- Taille pour age ---
    if taille_cm:
        z = _calc("lhfa", sexe, jours, taille_cm)
        if z is not None:
            res["indicateurs"]["taille_age"] = {
                "z": z, "libelle": "Taille-pour-âge (retard de croissance)",
                "classe": _classe_ta(z),
            }

    # --- Poids pour taille : LE marqueur de malnutrition aigue ---
    if poids_kg and taille_cm:
        indic = "wfl" if age_mois < 24 else "wfh"
        z = _calc(indic, sexe, round(taille_cm, 1), poids_kg)
        if z is None:  # hors plage de la table choisie, on tente l'autre
            autre = "wfh" if indic == "wfl" else "wfl"
            z = _calc(autre, sexe, round(taille_cm, 1), poids_kg)
            indic = autre
        if z is not None:
            res["indicateurs"]["poids_taille"] = {
                "z": z,
                "libelle": "Poids-pour-taille (émaciation / malnutrition aiguë)",
                "table": indic,
                "classe": _classe_pt(z),
            }
            if z < -3:
                alertes.append({
                    "niveau": "rouge",
                    "titre": "Malnutrition aiguë SÉVÈRE probable",
                    "action": "Rendez-vous en urgence dans un centre de santé "
                              "pour une prise en charge nutritionnelle (PCIMA/URENAS).",
                })
            elif z < -2:
                alertes.append({
                    "niveau": "orange",
                    "titre": "Malnutrition aiguë MODÉRÉE probable",
                    "action": "Consultez un centre de santé cette semaine pour un "
                              "suivi nutritionnel.",
                })

    # --- Perimetre brachial (PB / MUAC) : 6-59 mois ---
    if pb_mm and 6 <= age_mois <= 59:
        if pb_mm < 115:
            classe, niveau = "MAS (rouge)", "rouge"
            alertes.append({
                "niveau": "rouge",
                "titre": f"Périmètre brachial {pb_mm:.0f} mm : malnutrition aiguë sévère",
                "action": "Urgence nutritionnelle : allez au centre de santé aujourd'hui.",
            })
        elif pb_mm < 125:
            classe, niveau = "MAM (jaune)", "orange"
            alertes.append({
                "niveau": "orange",
                "titre": f"Périmètre brachial {pb_mm:.0f} mm : malnutrition aiguë modérée",
                "action": "Consultez un centre de santé cette semaine.",
            })
        else:
            classe, niveau = "Normal (vert)", "vert"
        res["indicateurs"]["pb"] = {
            "valeur_mm": pb_mm, "classe": classe, "niveau": niveau,
            "libelle": "Périmètre brachial (bandelette MUAC)",
            "seuils": {"MAS": "< 115 mm", "MAM": "115-124 mm", "normal": "≥ 125 mm"},
        }

    if oedemes:
        alertes.insert(0, {
            "niveau": "rouge",
            "titre": "Œdèmes bilatéraux des pieds",
            "action": "Signe de malnutrition aiguë sévère (kwashiorkor) quel que soit "
                      "le poids. Allez au centre de santé IMMÉDIATEMENT.",
        })

    niveaux = [a["niveau"] for a in alertes]
    res["verdict"] = "rouge" if "rouge" in niveaux else ("orange" if "orange" in niveaux else "vert")
    res["alertes"] = alertes or [{
        "niveau": "vert",
        "titre": "Aucun signe de malnutrition aiguë détecté",
        "action": "Poursuivez le suivi mensuel et l'alimentation variée. "
                  "Refaites la mesure dans 1 mois.",
    }]
    res["source"] = "Normes OMS de croissance de l'enfant (WHO Child Growth Standards, 2006)"
    res["avertissement"] = ("Outil de dépistage, pas un diagnostic. Seul un professionnel "
                            "de santé peut confirmer et prendre en charge.")
    return res


def _classe_pa(z: float) -> str:
    if z < -3:
        return "Insuffisance pondérale sévère"
    if z < -2:
        return "Insuffisance pondérale modérée"
    if z > 2:
        return "Poids élevé pour l'âge"
    return "Normal"


def _classe_ta(z: float) -> str:
    if z < -3:
        return "Retard de croissance sévère"
    if z < -2:
        return "Retard de croissance modéré"
    return "Normal"


def _classe_pt(z: float) -> str:
    if z < -3:
        return "Émaciation sévère (MAS)"
    if z < -2:
        return "Émaciation modérée (MAM)"
    if z > 3:
        return "Obésité"
    if z > 2:
        return "Surpoids"
    return "Normal"


def courbe(indicateur: str, sexe: str, xmin: float, xmax: float, pas: float = 1.0) -> dict:
    """Points -3/-2/0/+2 pour tracer les couloirs de la courbe OMS."""
    table = tables_croissance()["tables"].get(indicateur, {}).get(sexe, [])
    pts = {"x": [], "z_moins3": [], "z_moins2": [], "median": [], "z_plus2": []}
    x = xmin
    while x <= xmax:
        lms = _interp(table, round(x, 1))
        if lms:
            L, M, S = lms

            def v(z):
                return round(M * (1 + L * S * z) ** (1 / L) if L else M * (1 + S * z), 2)
            pts["x"].append(round(x, 1))
            pts["z_moins3"].append(v(-3))
            pts["z_moins2"].append(v(-2))
            pts["median"].append(round(M, 2))
            pts["z_plus2"].append(v(2))
        x += pas
    return pts
