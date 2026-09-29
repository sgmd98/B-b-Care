"""Verification de bout en bout de la couche securite v2.17 (sans navigateur).

Lance l'application en memoire avec fastapi.testclient et controle :
en-tetes de securite, fermeture de la documentation, traversee de repertoire,
consentement obligatoire, droits des personnes (export, changement de mot de
passe, suppression), acces DHIS2 reserve aux soignants, et limitation de debit.
"""
import os, sys, tempfile

os.environ["BEBECARE_DB"] = os.path.join(tempfile.mkdtemp(), "verif.db")
os.environ["BEBECARE_SECRET"] = "secret-de-test"
os.environ["BEBECARE_DOCS"] = "0"
os.environ.pop("DATABASE_URL", None)
sys.path.insert(0, "/home/user/B-b-Care")

from fastapi.testclient import TestClient          # noqa: E402
from api.main import app                           # noqa: E402

resultats = []


def verifier(nom, condition, detail=""):
    resultats.append((nom, bool(condition), detail))
    print(("OK   " if condition else "ECHEC") + " : " + nom + (" -> " + detail if detail and not condition else ""))


with TestClient(app) as c:
    # ------------------------------------------------------- en-tetes
    r = c.get("/api/sante")
    verifier("sante repond", r.status_code == 200)
    verifier("version 2.17", r.json().get("version") == "2.17", str(r.json().get("version")))
    for entete, attendu in [
        ("x-content-type-options", "nosniff"),
        ("x-frame-options", "SAMEORIGIN"),
        ("referrer-policy", "strict-origin-when-cross-origin"),
        ("cross-origin-opener-policy", "same-origin"),
    ]:
        verifier(f"en-tete {entete}", r.headers.get(entete) == attendu, str(r.headers.get(entete)))
    csp = r.headers.get("content-security-policy", "")
    verifier("CSP presente", "default-src 'self'" in csp)
    verifier("CSP interdit object-src", "object-src 'none'" in csp)
    verifier("CSP limite frame-ancestors", "frame-ancestors" in csp)

    # ---------------------------------------------- documentation fermee
    verifier("/docs ferme", c.get("/docs").status_code == 404)
    verifier("/openapi.json ferme", c.get("/openapi.json").status_code == 404)

    # ---------------------------------------- traversee de repertoire
    for chemin in ["/../api/bd.py", "/..%2F..%2Fapi%2Fbd.py", "/%2e%2e/%2e%2e/api/main.py",
                   "/../../requirements.txt"]:
        r = c.get(chemin)
        fuite = "import" in r.text and ("fastapi" in r.text or "sqlite3" in r.text)
        verifier(f"pas de fuite sur {chemin}", not fuite, r.text[:60])

    # ---------------------------- outils cliniques libres sans compte
    r = c.post("/api/nutrition/depistage", json={"age_mois": 18, "sexe": "m", "poids_kg": 9.5})
    verifier("depistage nutrition sans compte", r.status_code == 200)
    r = c.post("/api/triage", json={"age_mois": 6, "signes": []})
    verifier("triage sans compte", r.status_code == 200)

    # ---------------------------------------------------- consentement
    r = c.post("/api/compte/inscription", json={
        "identifiant": "parent@exemple.com", "mot_de_passe": "motdepasse123",
        "pays": "bj", "langue": "fr", "role": "parent"})
    verifier("inscription sans consentement refusee", r.status_code == 422, str(r.status_code))

    r = c.post("/api/compte/inscription", json={
        "identifiant": "parent@exemple.com", "mot_de_passe": "motdepasse123",
        "pays": "bj", "langue": "fr", "role": "parent",
        "consentement": False, "version_politique": "1.0"})
    verifier("consentement false refuse", r.status_code == 422, str(r.status_code))

    r = c.post("/api/compte/inscription", json={
        "identifiant": "parent@exemple.com", "mot_de_passe": "motdepasse123",
        "pays": "bj", "langue": "fr", "role": "parent",
        "consentement": True, "version_politique": "1.0"})
    verifier("inscription avec consentement acceptee", r.status_code == 200, r.text[:120])
    jeton = r.json().get("jeton")
    verifier("version de politique enregistree",
             r.json()["utilisateur"].get("consentement_version") == "1.0",
             str(r.json()["utilisateur"].get("consentement_version")))

    r = c.post("/api/compte/inscription", json={
        "identifiant": "parent@exemple.com", "mot_de_passe": "motdepasse123",
        "pays": "bj", "consentement": True, "version_politique": "1.0"})
    verifier("doublon refuse", r.status_code == 400, str(r.status_code))

    r = c.post("/api/compte/inscription", json={
        "identifiant": "<script>alert(1)</script>", "mot_de_passe": "motdepasse123",
        "pays": "bj", "consentement": True, "version_politique": "1.0"})
    verifier("identifiant avec balise refuse", r.status_code in (400, 422), str(r.status_code))
    r = c.get("/api/route-inexistante")
    verifier("route API inconnue rend un 404", r.status_code == 404, str(r.status_code))

    # ------------------------------------------------------ connexion
    r = c.post("/api/compte/connexion", json={"identifiant": "parent@exemple.com",
                                              "mot_de_passe": "mauvais-mdp"})
    verifier("mauvais mot de passe refuse", r.status_code == 401)
    r = c.post("/api/compte/connexion", json={"identifiant": "parent@exemple.com",
                                              "mot_de_passe": "motdepasse123"})
    verifier("connexion correcte", r.status_code == 200)

    # -------------------------------------------------- donnees de suivi
    h = {"authorization": f"Bearer {jeton}"}
    r = c.post("/api/compte/enfants", headers=h, json={
        "prenom": "Awa", "sexe": "f", "date_naissance": "2024-05-01"})
    verifier("creation enfant", r.status_code == 200, r.text[:120])
    eid = r.json()["id"]
    r = c.post(f"/api/compte/enfants/{eid}/mesures", headers=h, json={
        "date_mesure": "2026-01-15", "age_mois": 20, "poids_kg": 10.4,
        "taille_cm": 80.2, "pb_mm": 145, "z_pa": -1.2})
    verifier("ajout d'une mesure", r.status_code == 200, r.text[:120])
    r = c.post(f"/api/compte/enfants/{eid}/mesures", headers=h, json={
        "date_mesure": "2027-01-15", "age_mois": 20})
    verifier("date de mesure future refusee", r.status_code == 422, str(r.status_code))

    # --------------------------------------------------- temps prives
    r = c.get("/api/compte/moi", headers=h)
    verifier("cache interdit sur les donnees de compte",
             r.headers.get("cache-control") == "no-store", str(r.headers.get("cache-control")))
    r = c.get("/api/pays")
    verifier("pas de no-store sur les donnees publiques",
             r.headers.get("cache-control") != "no-store", str(r.headers.get("cache-control")))

    # ------------------------------------------------------------ export
    r = c.get("/api/compte/export", headers=h)
    verifier("export des donnees", r.status_code == 200 and r.json()["enfants"][0]["mesures"],
             r.text[:120])
    verifier("export sans mot de passe", "empreinte" not in r.text)

    # ------------------------------------------- acces DHIS2 soignant
    r = c.post("/api/dhis2/seance/envoyer", json={
        "org_unit": "DiszpKrYNg8", "periode": "202609",
        "consultations": [{"prenom": "Awa", "age_mois": 20, "vaccins": ["BCG"]}]})
    verifier("envoi DHIS2 sans compte refuse", r.status_code == 401, str(r.status_code))
    r = c.post("/api/dhis2/seance/envoyer", headers=h, json={
        "org_unit": "DiszpKrYNg8", "periode": "202609",
        "consultations": [{"prenom": "Awa", "age_mois": 20, "vaccins": ["BCG"]}]})
    verifier("envoi DHIS2 refuse a un parent", r.status_code == 403, str(r.status_code))
    r = c.post("/api/dhis2/seance", json={
        "org_unit": "DiszpKrYNg8", "periode": "202609",
        "consultations": [{"prenom": "Awa", "age_mois": 20, "vaccins": ["BCG"]}]})
    verifier("preparation du document DHIS2 reste libre",
             r.status_code == 200 and r.json()["payload"]["dataValues"], r.text[:120])

    # ----------------------------------------- changement de mot de passe
    r = c.post("/api/compte/mot-de-passe", headers=h, json={
        "mot_de_passe_actuel": "mauvais", "nouveau_mot_de_passe": "nouveaumdp123"})
    verifier("changement avec mauvais mot de passe refuse", r.status_code == 400)
    r = c.post("/api/compte/mot-de-passe", headers=h, json={
        "mot_de_passe_actuel": "motdepasse123", "nouveau_mot_de_passe": "nouveaumdp123"})
    verifier("changement de mot de passe accepte", r.status_code == 200, r.text[:120])
    r = c.get("/api/compte/moi", headers=h)
    verifier("ancien jeton invalide apres changement", r.status_code == 401, str(r.status_code))
    r = c.post("/api/compte/connexion", json={"identifiant": "parent@exemple.com",
                                              "mot_de_passe": "nouveaumdp123"})
    verifier("connexion avec le nouveau mot de passe", r.status_code == 200)
    jeton2 = r.json()["jeton"]

    # ------------------------------------------------- informations legales
    r = c.get("/api/legal")
    legal = r.json()
    verifier("/api/legal repond", r.status_code == 200)
    verifier("editeur identifie", "SOSSA" in legal["editeur"]["nom"])
    verifier("version de politique publiee", legal["politique"]["version"] == "1.0")
    verifier("droits listes", "portabilité" in legal["droits"])
    r = c.get("/api/legal/version")
    verifier("/api/legal/version", r.json()["version"] == "1.0")

    # ---------------------------------------------------- suppression
    h2 = {"authorization": f"Bearer {jeton2}"}
    r = c.request("DELETE", "/api/compte/moi", headers=h2,
                  json={"mot_de_passe": "mauvais", "confirmation": "supprimer"})
    verifier("suppression avec mauvais mot de passe refusee", r.status_code == 400, str(r.status_code))
    r = c.request("DELETE", "/api/compte/moi", headers=h2,
                  json={"mot_de_passe": "nouveaumdp123", "confirmation": "supprimer"})
    verifier("suppression du compte acceptee", r.status_code == 200, r.text[:140])
    r = c.get("/api/compte/moi", headers=h2)
    verifier("jeton mort apres suppression", r.status_code == 401, str(r.status_code))
    r = c.post("/api/compte/connexion", json={"identifiant": "parent@exemple.com",
                                              "mot_de_passe": "nouveaumdp123"})
    verifier("compte reellement supprime", r.status_code == 401, str(r.status_code))

    # --------------------------------------------- limitation de debit
    dernier = None
    for i in range(20):
        dernier = c.post("/api/compte/connexion", json={
            "identifiant": "inconnu@exemple.com", "mot_de_passe": "faux"})
        if dernier.status_code == 429:
            break
    verifier("force brute bloquee (429)", dernier.status_code == 429, str(dernier.status_code))
    verifier("message d'attente en clair",
             "Reessayez" in dernier.json().get("detail", ""), dernier.text[:120])
    verifier("en-tete Retry-After", "retry-after" in dernier.headers)

print()
echecs = [n for n, ok, _ in resultats if not ok]
print(f"{len(resultats) - len(echecs)}/{len(resultats)} controles reussis")
if echecs:
    print("Echecs :", echecs)
    sys.exit(1)
