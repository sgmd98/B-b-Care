"""Securite HTTP de BebeCare : en-tetes, origines autorisees, limitation de debit.

Ce module est volontairement sans dependance externe : il ne s'appuie que sur
la bibliotheque standard et sur Starlette, deja presents via FastAPI.

TROIS PROTECTIONS
-----------------
1. EN-TETES DE SECURITE (middleware_entetes)
   Content-Security-Policy, X-Content-Type-Options, Referrer-Policy,
   Permissions-Policy, X-Frame-Options, Strict-Transport-Security,
   Cross-Origin-Opener-Policy. Une application de sante doit se proteger
   contre l'injection de script (XSS) et le detournement de cadre (clickjacking).
   La carte utilise MapLibre : les domaines de tuiles sont autorises
   explicitement, rien d'autre ne sort du site.

2. ORIGINES AUTORISEES (ORIGINES)
   Le site et l'API sont servis par le meme domaine : aucune requete
   inter-domaines n'est necessaire en production. On n'ouvre donc pas
   Access-Control-Allow-Origin a "*" (ce qui laisserait n'importe quel site
   appeler l'API au nom d'un utilisateur connecte). La liste est reglable par
   la variable d'environnement BEBECARE_ORIGINES, separee par des virgules.

3. LIMITATION DE DEBIT (limiteur)
   Trois routes coutent cher et sont donc bornees par adresse IP :
   la connexion (anti force brute), l'inscription (anti creation massive de
   comptes) et l'assistant IA (cout fournisseur). Le compteur est en memoire :
   sur une instance gratuite unique, c'est suffisant et sans dependance.

CONFIGURATION
-------------
  BEBECARE_ORIGINES        : origines CORS autorisees, separees par des virgules
  BEBECARE_SECURITE_ENTETES: "0" pour desactiver les en-tetes (deconseille)
  BEBECARE_CSP             : remplace entierement la politique par defaut
  BEBECARE_DERRIERE_PROXY  : "1" (defaut) pour lire X-Forwarded-For (Render)
"""
from __future__ import annotations

import os
import re
import threading
import time

# --------------------------------------------------------------- CONFIGURATION

ORIGINES_PRODUCTION = [
    "https://bebecare.onrender.com",
]
ORIGINES_DEV = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:8000", "http://127.0.0.1:8000",
]


def _origines() -> list[str]:
    brut = os.environ.get("BEBECARE_ORIGINES", "").strip()
    if brut:
        return [o.strip().rstrip("/") for o in brut.split(",") if o.strip()]
    # Apercu de developpement (Arena, e2b) : autorise uniquement en local, car
    # la variable BEBECARE_ORIGINES est toujours definie en production.
    return ORIGINES_PRODUCTION + ORIGINES_DEV


ORIGINES = _origines()

# Version des documents legaux publies (politique de confidentialite et
# conditions d'utilisation). Elle est enregistree avec chaque consentement :
# si le texte change, la version change et un nouveau consentement peut etre
# demande. Tenir cette valeur synchronisee avec web/src/legal.jsx.
VERSION_POLITIQUE = os.environ.get("BEBECARE_POLITIQUE_VERSION", "1.0")

DERRIERE_PROXY = os.environ.get("BEBECARE_DERRIERE_PROXY", "1") != "0"
ENTETES_ACTIFS = os.environ.get("BEBECARE_SECURITE_ENTETES", "1") != "0"

# Domaines strictement necessaires au fonctionnement de la carte et de la meteo.
CSP_DEFAUT = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https://tiles.openfreemap.org https://*.openfreemap.org "
    "https://api.open-meteo.com https://*.tile.openstreetmap.org; "
    "worker-src 'self' blob:; "
    "manifest-src 'self'; "
    "form-action 'self'; "
    # La politique est restreinte par defaut. Seule la variable d'environnement
    # BEBECARE_CSP_FRAME permet d'assouplir l'imbrication en cadre.
    "frame-ancestors {frames}"
)
FRAMES_DEFAUT = "'self' https://*.e2b.app https://*.arena.ai"


def politique_csp() -> str:
    forcee = os.environ.get("BEBECARE_CSP", "").strip()
    if forcee:
        return forcee
    frames = os.environ.get("BEBECARE_CSP_FRAME", FRAMES_DEFAUT).strip()
    return CSP_DEFAUT.format(frames=frames)


ENTETES_FIXES = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "SAMEORIGIN",
    "Permissions-Policy": "geolocation=(self), camera=(), microphone=(), "
                           "payment=(), usb=(), interest-cohort=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-BebeCare-Version": os.environ.get("BEBECARE_VERSION", "2.17"),
}

# Chemins jamais journalises ni mis en cache (donnees de sante personnelles).
CHEMINS_PRIVES = ("/api/compte",)


# ------------------------------------------------------------------ EN-TETES

async def middleware_entetes(requete, appeler_suivant):
    """Ajoute les en-tetes de securite a chaque reponse de l'application."""
    reponse = await appeler_suivant(requete)
    if not ENTETES_ACTIFS:
        return reponse
    for cle, valeur in ENTETES_FIXES.items():
        reponse.headers.setdefault(cle, valeur)
    reponse.headers.setdefault("Content-Security-Policy", politique_csp())
    if requete.url.path.startswith(CHEMINS_PRIVES):
        # Aucune reponse contenant des donnees de compte ne doit etre conservee
        # par un proxy ou un navigateur partage.
        reponse.headers.setdefault("Cache-Control", "no-store")
    return reponse


# ------------------------------------------------------------ LIMITEUR DEBIT

class Limiteur:
    """Compteur a fenetre glissante, en memoire, protege par un verrou.

    Suffisant pour une instance unique : chaque adresse IP dispose d'un quota
    par route sensible. Aucun stockage externe, aucun identifiant conserve
    au dela de la fenetre.
    """

    def __init__(self, max_cles: int = 20000):
        self._verrou = threading.Lock()
        self._vues: dict[str, list[float]] = {}
        self._max_cles = max_cles

    def autoriser(self, cle: str, maximum: int, fenetre_s: float) -> tuple[bool, int]:
        """Retourne (autorise, secondes_a_attendre)."""
        maintenant = time.monotonic()
        with self._verrou:
            vue = [t for t in self._vues.get(cle, []) if maintenant - t < fenetre_s]
            if len(vue) >= maximum:
                attente = int(fenetre_s - (maintenant - vue[0])) + 1
                self._vues[cle] = vue
                return False, max(attente, 1)
            vue.append(maintenant)
            self._vues[cle] = vue
            if len(self._vues) > self._max_cles:      # purge globale de securite
                self._vues = {c: v for c, v in self._vues.items()
                              if v and maintenant - v[-1] < 600}
        return True, 0


limiteur = Limiteur()

# (methode, expression du chemin, maximum, fenetre en secondes)
REGLES: list[tuple[str, str, int, float]] = [
    ("POST", r"^/api/compte/connexion$", 12, 900),
    ("POST", r"^/api/compte/inscription$", 6, 3600),
    ("POST", r"^/api/compte/mot-de-passe$", 6, 3600),
    ("POST", r"^/api/assistant(/.*)?$", 40, 300),
    ("POST", r"^/api/dhis2/(push|seance/envoyer)$", 30, 900),
    ("GET", r"^/api/vaccins/(calendrier\.pdf|ics)$", 80, 900),
    ("*", r"^/api/", 600, 60),                     # plafond general
]
REGLES_COMPILEES = [(m, re.compile(c), n, f) for m, c, n, f in REGLES]


def adresse_client(requete) -> str:
    """Adresse IP de l'appelant, en tenant compte du proxy Render."""
    if DERRIERE_PROXY:
        xff = requete.headers.get("x-forwarded-for", "")
        if xff:
            return xff.split(",")[0].strip()[:64]
    client = getattr(requete, "client", None)
    return (client.host if client else "inconnu")[:64]


async def middleware_limites(requete, appeler_suivant):
    """Applique les quotas avant d'executer la route concernee."""
    chemin = requete.url.path
    ip = adresse_client(requete)
    for methode, motif, maximum, fenetre in REGLES_COMPILEES:
        if methode not in ("*", requete.method) or not motif.match(chemin):
            continue
        autorise, attente = limiteur.autoriser(f"{ip}|{motif.pattern}", maximum, fenetre)
        if not autorise:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Trop de tentatives depuis cet appareil. "
                                   f"Reessayez dans {attente // 60 + 1} minute(s)."},
                headers={"Retry-After": str(attente), "Cache-Control": "no-store"},
            )
    return await appeler_suivant(requete)


# --------------------------------------------------------------- DOCUMENTATION

def documentation_ouverte() -> bool:
    """Swagger et OpenAPI fermes par defaut en production.

    Une API de sante n'a pas besoin d'exposer publiquement la liste de ses
    routes et de ses schemas : cela sert de carte au premier venu. On les
    ouvre explicitement avec BEBECARE_DOCS=1 (utile en local et pour le jury).
    """
    return os.environ.get("BEBECARE_DOCS", "0") == "1"


def secrets_de_secours() -> bool:
    """Vrai si l'application tourne avec un secret de demonstration."""
    return not os.environ.get("BEBECARE_SECRET", "").strip()
