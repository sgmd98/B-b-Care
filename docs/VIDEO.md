# Script vidéo — 3 min 30

Format : capture d'écran + ta voix. Pas de musique forte, pas de slides de code.
Tourne en 1080p, parle lentement. **Sous-titres anglais obligatoires** : les deux
juges (Jonathan Chang, Yaokai Jiang) sont anglophones.

---

## 0:00 – 0:20 · Toi, en visage, 15 secondes

> « Je m'appelle [ton nom]. Je suis infirmier-puériculteur à Cotonou, au Bénin.
> Chaque semaine, je vois arriver un enfant qui a manqué trois doses de vaccin, ou
> qui a maigri depuis deux mois sans que personne l'ait vu. À chaque fois,
> l'information qui aurait évité ça existait déjà. Elle était juste inaccessible. »

*Pourquoi : la légitimité en premier. Aucun autre participant ne peut dire ça.*

## 0:20 – 0:45 · Le problème, chiffré

Plein écran, gros chiffres à l'image :

- **49 %** — couverture rougeole 1re dose au Bénin (OMS, 2025)
- **100 ‰** — mortalité des moins de 5 ans au Niger

> « Ce ne sont pas mes chiffres, ce sont ceux de l'OMS, 2025. Le calendrier
> vaccinal est un PDF sur un site ministériel. Les normes de croissance de l'OMS,
> un tableur de 1 857 lignes. Et les vraies données de couverture sont dans DHIS2,
> la base nationale, à laquelle aucune mère n'aura jamais accès. »

## 0:45 – 1:30 · La carte (le moment « waouh »)

Écran : ouvrir l'app, la carte des 15 pays, dézoomer pour montrer la densité.

> « Voici BébéCare. 23 568 structures de santé, dans les 15 pays de la CEDEAO,
> sur une seule carte. »

Puis : cliquer « Autour de moi », montrer les résultats triés par distance,
ouvrir une fiche, montrer l'itinéraire.

> « Une mère appuie sur un bouton et sait où aller, à quelle distance, avec
> l'itinéraire et le numéro. »

## 1:30 – 2:05 · Le carnet vaccinal

Écran : saisir une date de naissance. Le planning apparaît avec des doses en rouge.

> « Je saisis la date de naissance. BébéCare applique le calendrier national
> officiel du Bénin — pas un calendrier générique, celui du jeu de données OMS,
> version 2025. Il calcule chaque rendez-vous et repère les retards. »

Cliquer sur l'export `.ics`.

> « Et il envoie tous les rappels dans l'agenda du téléphone. »

## 2:05 – 2:35 · Le dépistage nutritionnel

Écran : saisir 18 mois, garçon, 7,2 kg, 76 cm, PB 112 mm → alerte rouge + courbe.

> « Poids, taille, périmètre brachial. BébéCare calcule les z-scores avec les
> tables officielles de l'OMS et classe l'enfant : ici, malnutrition aiguë sévère.
> Ce sont exactement les critères qu'utilisent les agents de santé communautaires. »

## 2:35 – 3:10 · DHIS2 — le passage qui gagne les points techniques

Écran : onglet Données & DHIS2. Montrer la pastille verte « en ligne, v2.42.6 »,
changer de district, le graphique se recharge.

> « DHIS2 est le système d'information sanitaire national de 14 des 15 pays que
> je couvre. BébéCare lit ses indicateurs de couverture en direct — je change de
> district, la requête part vraiment. »

Cliquer « Générer le payload DHIS2 », montrer le JSON et la validation verte.

> « Et dans l'autre sens : aujourd'hui un agent note les vaccinations sur papier
> et quelqu'un les ressaisit dans DHIS2 des semaines plus tard. BébéCare traduit
> le carnet en un document DHIS2 conforme, prêt à être envoyé. Pour être clair :
> je ne me connecte à aucune base nationale de production, c'est l'instance de
> démonstration publique de DHIS2, et l'écriture est désactivée par défaut. Un
> ministère change trois variables d'environnement, et c'est branché sur son
> propre système. »

## 3:10 – 3:30 · Clôture, en visage

> « Aucun chiffre n'est inventé : tout vient de l'OMS, d'OpenStreetMap et de
> DHIS2, avec les sources citées. Aucune donnée de l'enfant ne quitte le
> téléphone. C'est gratuit, sans compte, et ça marche sur un téléphone d'entrée
> de gamme. BébéCare. Merci. »

---

## Check-list avant publication

- [ ] Vidéo en **non répertoriée ou publique** sur YouTube (pas « privée » — erreur classique qui invalide la soumission)
- [ ] Sous-titres anglais
- [ ] Durée < 5 min
- [ ] L'app est réveillée pendant le tournage (Render s'endort au bout de 15 min)
- [ ] Aucune donnée réelle de patient à l'écran
- [ ] Le lien du dépôt GitHub apparaît dans la description
