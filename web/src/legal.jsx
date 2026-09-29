/* Documents légaux de BébéCare : politique de confidentialité, conditions
   d'utilisation et mentions légales, en français et en anglais.

   Règles de rédaction :
   - Aucun tiret cadratin ni demi-cadratin dans les textes affichés.
   - Chaque section reste courte et lisible par un parent, pas par un juriste.
   - La version est enregistrée avec chaque consentement côté serveur
     (api/securite.py, VERSION_POLITIQUE) : les deux valeurs doivent rester
     identiques.

   Ces documents décrivent ce que le logiciel fait réellement : aucun cookie
   de mesure d'audience, aucune revente, aucune publicité, suppression réelle
   du compte et des données de suivi depuis Mon espace. */

export const VERSION_POLITIQUE = '1.0'
export const DATE_POLITIQUE = { fr: '29 septembre 2026', en: '29 September 2026' }

export const EDITEUR = {
  nom: 'SOSSA Gninazé Mingnissê Darius',
  fr: "Infirmier diplômé d'État, développeur web et étudiant en Master 1 Puériculture-Pédiatrie, Cotonou, Bénin.",
  en: 'State-certified nurse, web developer and Master 1 student in Childcare and Pediatrics, Cotonou, Benin.',
  email: 'sante.infantile.benin@gmail.com',
  ville: { fr: 'Cotonou, Bénin', en: 'Cotonou, Benin' },
}

export const LEGAL = {
  fr: {
    onglet_confidentialite: 'Confidentialité',
    onglet_conditions: "Conditions d'utilisation",
    onglet_mentions: 'Mentions légales',
    version_label: 'Version',
    maj_label: 'Dernière mise à jour',
    retour_haut: 'Haut de page',
    imprimer: 'Imprimer ou enregistrer en PDF',

    confidentialite: {
      titre: 'Politique de confidentialité',
      chapeau:
        "BébéCare traite des données de santé d'enfants de moins de 5 ans. " +
        "C'est une responsabilité, pas une formalité. Cette page explique, en " +
        "clair et sans jargon, quelles données sont conservées, pourquoi, " +
        "pendant combien de temps, et comment les faire supprimer.",
      sections: [
        {
          t: "1. Qui est responsable du traitement",
          p: [
            EDITEUR.nom + ', ' + EDITEUR.fr,
            "Contact pour toute question ou pour exercer vos droits : " +
              EDITEUR.email + ' (réponse sous 30 jours).',
            "BébéCare est un projet indépendant, sans but lucratif et sans " +
              "publicité. Il n'appartient à aucune entreprise, à aucune " +
              "assurance et à aucun laboratoire.",
          ],
        },
        {
          t: '2. Quelles données sont conservées',
          p: [
            "Compte (facultatif) : identifiant, qui est un email ou un numéro " +
              'de téléphone, un nom affiché si vous le renseignez, le pays, la ' +
              'langue, votre profil (parent ou soignant) et votre mot de passe.',
            "Mot de passe : jamais conservé en clair. Il est transformé par " +
              'PBKDF2-HMAC-SHA256 avec 240 000 itérations et un sel unique ' +
              'par compte. Personne, pas même l\'éditeur, ne peut le relire.',
            "Suivi de l'enfant : prénom, sexe, date de naissance, pays, " +
              'vaccins cochés, et pour chaque mesure la date, l\'âge, le ' +
              'poids, la taille, le périmètre brachial et les z-scores ' +
              'calculés selon les normes OMS.',
            'Données techniques : votre adresse IP est utilisée au moment de ' +
              'la requête pour limiter les abus (tentatives de connexion ' +
              'répétées, appels massifs), puis oubliée. Aucune adresse IP ' +
              "n'est conservée avec votre dossier.",
          ],
        },
        {
          t: '3. Pourquoi ces données sont traitées',
          p: [
            'Afficher le calendrier vaccinal correspondant à votre pays et à ' +
              "l'âge de votre enfant.",
            'Calculer les z-scores de croissance et signaler une malnutrition ' +
              'aiguë ou chronique selon les seuils OMS.',
            'Synchroniser le suivi entre vos appareils, si vous créez un compte.',
            'Sécuriser le service : limiter les tentatives de connexion ' +
              'abusives et protéger les comptes.',
            "Aucun profilage, aucune décision automatisée produisant un effet " +
              "juridique, aucune exploitation commerciale.",
          ],
        },
        {
          t: '4. Ce que BébéCare ne fait jamais',
          p: [
            'Aucune revente ni location de données, à personne.',
            'Aucune publicité et aucun traceur publicitaire.',
            'Aucun cookie de mesure d\'audience ni de réseau social.',
            'Aucune transmission à un assureur, un employeur ou un courtier.',
            'Aucune publication de données permettant d\'identifier un enfant.',
            'Aucune utilisation de vos données pour entraîner un modèle d\'IA.',
          ],
        },
        {
          t: '5. Qui voit les données',
          p: [
            'Vous uniquement, pour les données de votre compte et de vos enfants.',
            "Hébergement : Render (Francfort, Allemagne) pour le site et l'API, " +
              'et une base PostgreSQL gérée par Neon (Union européenne) pour ' +
              'les comptes.',
            "Assistant IA : lorsque vous posez une question en langage libre, " +
              'le texte de la question et l\'âge de l\'enfant sont envoyés au ' +
              "fournisseur de modèle de langage. Ni votre nom, ni votre " +
              "identifiant, ni le nom de l'enfant ne sont transmis. Si vous " +
              'préférez ne rien envoyer, cochez la liste des signes : la ' +
              'décision PCIME se prend entièrement sur votre appareil et sur ' +
              'le serveur de BébéCare, sans IA.',
            'DHIS2 : la passerelle est connectée à une instance de ' +
              "démonstration publique. Aucune donnée d'enfant n'y est " +
              'transmise, et l\'écriture est désactivée par défaut.',
            "Aucun autre destinataire. Aucun transfert à des fins commerciales.",
          ],
        },
        {
          t: '6. Combien de temps les données sont conservées',
          p: [
            'Le suivi est conservé tant que votre compte existe.',
            'Vous pouvez supprimer un enfant à tout moment : ses mesures sont ' +
              'effacées en même temps.',
            'Vous pouvez supprimer votre compte à tout moment depuis Mon ' +
              "espace : le compte, les enfants et toutes les mesures sont " +
              'effacés immédiatement, sans copie conservée.',
            "Les comptes inutilisés depuis plus de 24 mois pourront être " +
              'supprimés après un courriel de rappel.',
          ],
        },
        {
          t: '7. Vos droits',
          p: [
            'Accès : voir tout ce qui est conservé sur vous.',
            'Rectification : corriger un prénom, une date de naissance, une mesure.',
            'Effacement : supprimer un enfant ou tout le compte.',
            'Portabilité : télécharger vos données dans un fichier JSON lisible, ' +
              'depuis Mon espace.',
            'Opposition et retrait du consentement : vous pouvez retirer votre ' +
              'consentement à tout moment, ce qui revient à supprimer le compte.',
            'Pour exercer ces droits : les boutons de Mon espace, ou un email à ' +
              EDITEUR.email + '. Une réponse vous est apportée sous 30 jours.',
            "Vous pouvez également saisir l'Autorité de protection des données " +
              'personnelles (APDP) du Bénin si vous estimez que vos droits ne ' +
              'sont pas respectés.',
          ],
        },
        {
          t: "8. Données d'un enfant de moins de 5 ans",
          p: [
            "Le compte est créé et utilisé par un parent, un tuteur ou un " +
              'professionnel de santé, qui fournit les données de l\'enfant ' +
              'sous sa responsabilité.',
            "L'enfant ne peut pas créer de compte et ne reçoit aucune " +
              'communication.',
            'Si vous constatez qu\'un compte a été créé avec les données d\'un ' +
              'enfant sans l\'accord de son représentant légal, écrivez à ' +
              EDITEUR.email + ' : le compte est supprimé.',
          ],
        },
        {
          t: '9. Sécurité',
          p: [
            'Le site est servi en HTTPS. Les mots de passe sont hachés avec ' +
              'PBKDF2 (240 000 itérations, sel unique par compte).',
            "Les en-têtes de sécurité sont activés : politique de sécurité du " +
              'contenu, interdiction du reniflage de type, restriction du ' +
              'référent, permissions minimales.',
            'Les tentatives de connexion et les appels coûteux sont limités ' +
              'par adresse IP. Les jetons de session expirent au bout de 30 ' +
              'jours et sont invalidés dès que le mot de passe change.',
            'Les données de compte ne sont jamais mises en cache par un ' +
              'navigateur partagé ou un proxy.',
            'En cas de violation de données susceptible d\'entraîner un risque ' +
              'élevé, les personnes concernées sont informées sans délai, ' +
              'ainsi que l\'APDP.',
          ],
        },
        {
          t: '10. Cookies et stockage local',
          p: [
            'BébéCare ne dépose aucun cookie.',
            "Le navigateur conserve uniquement, dans son stockage local, votre " +
              'jeton de session, votre pays et votre langue. Ces informations ' +
              'ne quittent pas votre appareil et ne servent à aucun suivi ' +
              'publicitaire. Se déconnecter efface le jeton.',
          ],
        },
        {
          t: '11. Cadre juridique',
          p: [
            'BébéCare applique les principes du Règlement général sur la ' +
              'protection des données (minimisation, finalité déterminée, ' +
              'durée limitée, droits des personnes).',
            'Au Bénin, le traitement des données personnelles relève du Code du ' +
              'numérique (loi n° 2017-20) et du contrôle de l\'APDP.',
          ],
        },
        {
          t: '12. Modifications de cette politique',
          p: [
            'Toute modification est datée et sa version change. Si la ' +
              'modification est importante, elle est annoncée à la connexion ' +
              'et un nouveau consentement vous est demandé avant de poursuivre.',
          ],
        },
      ],
    },

    conditions: {
      titre: "Conditions d'utilisation",
      chapeau:
        "BébéCare aide à orienter, à suivre la vaccination et à dépister la " +
        "malnutrition. Ce n'est ni un médecin, ni un service d'urgence. Ces " +
        "conditions disent précisément ce que le service fait et ce qu'il ne " +
        "fait pas.",
      sections: [
        {
          t: '1. Objet du service',
          p: [
            'BébéCare est un outil d\'information et d\'orientation en santé ' +
              "de l'enfant de 0 à 5 ans, destiné aux 15 pays de la CEDEAO.",
            'Le service applique des règles publiques : l\'algorithme PCIME de ' +
              "l'OMS et de l'UNICEF pour le triage des signes de danger, les " +
              'normes de croissance OMS pour les z-scores, les calendriers ' +
              'vaccinaux nationaux pour les rappels.',
            "L'accès aux outils cliniques est gratuit et ne nécessite aucun compte.",
          ],
        },
        {
          t: "2. Ce que BébéCare n'est pas",
          p: [
            "Ce n'est pas un dispositif médical et il ne pose aucun diagnostic.",
            "Ce n'est pas un service d'urgence. En cas de danger immédiat, " +
              "appelez le numéro d'urgence de votre pays, affiché dans " +
              "l'application, ou rendez-vous au centre de santé le plus proche.",
            "Ce n'est pas de la télémédecine : aucune consultation à distance " +
              "n'est réalisée, aucun professionnel ne vous répond dans " +
              "l'application.",
            "Les résultats sont des aides à la décision. Un professionnel de " +
              "santé reste seul juge de la conduite à tenir.",
          ],
        },
        {
          t: '3. Usage autorisé',
          p: [
            'Vous pouvez utiliser BébéCare pour vous-même, pour un enfant dont ' +
              'vous êtes responsable, ou dans le cadre de votre activité de ' +
              'soin, sans but commercial.',
            'Vous vous engagez à saisir des informations exactes et à ne pas ' +
              "enregistrer les données d'un enfant dont vous n'avez pas la " +
              'responsabilité.',
          ],
        },
        {
          t: '4. Usage interdit',
          p: [
            "Extraire massivement les données du site (aspiration automatisée, " +
              'robot de téléchargement) ou contourner les limites d\'appel.',
            'Revendre, sous-licencier ou redistribuer le service ou ses données.',
            "Tenter d'accéder au compte d'une autre personne, de deviner un mot " +
              'de passe ou de perturber le service.',
            "Usurper l'identité de l'éditeur, d'un ministère de la Santé, de " +
              "l'OMS ou d'un centre de santé.",
            'Présenter les résultats du site comme un avis médical signé.',
          ],
        },
        {
          t: '5. Comptes et sécurité',
          p: [
            'Vous êtes responsable de la confidentialité de votre mot de passe ' +
              'et de l\'usage fait depuis votre compte.',
            'Choisissez un mot de passe d\'au moins 8 caractères, unique, et ' +
              'changez-le si vous pensez qu\'il a été divulgué : le changement ' +
              'déconnecte toutes les sessions ouvertes.',
            'Le compte est facultatif : tous les outils fonctionnent sans ' +
              'inscription, seul le suivi dans le temps a besoin d\'un compte.',
          ],
        },
        {
          t: '6. Sources et licences',
          p: [
            'Centres de santé : OpenStreetMap, licence ODbL 1.0, mention ' +
              '© les contributeurs OpenStreetMap.',
            'Couverture vaccinale et normes de croissance : Organisation ' +
              'mondiale de la Santé, données ouvertes.',
            'Calendriers vaccinaux : programmes nationaux de vaccination, ' +
              'compilés et datés.',
            'Triage : algorithme PCIME (Prise en charge intégrée des maladies ' +
              'de l\'enfant) de l\'OMS et de l\'UNICEF.',
            'Fonds de carte : OpenFreeMap, données OpenStreetMap.',
            'Chaque écran de données indique sa source et sa date. Une ' +
              'information sans source datée n\'est pas une information de ' +
              'référence.',
          ],
        },
        {
          t: '7. Exactitude et limites',
          p: [
            'Les données cartographiques sont participatives : un centre de ' +
              'santé peut être fermé, déplacé ou non répertorié.',
            'Les calendriers vaccinaux peuvent évoluer : le calendrier national ' +
              'et le carnet de l\'enfant, au centre de santé, font foi.',
            'Les tables de croissance OMS sont interpolées : une mesure isolée ' +
              'ne remplace pas une courbe suivie dans le temps.',
          ],
        },
        {
          t: '8. Responsabilité',
          p: [
            "BébéCare est fourni en l'état, sans garantie d'exactitude " +
              'permanente ni de disponibilité continue.',
            "L'éditeur ne peut être tenu responsable d'une décision prise sur " +
              "la seule base d'un résultat affiché, ni d'une indisponibilité " +
              'du service, ni de l\'usage fait par un tiers des données ' +
              'ouvertes qu\'il rediffuse.',
            "La responsabilité de l'éditeur ne peut être engagée au delà de ce " +
              'que le droit applicable autorise pour un service gratuit ' +
              "d'information en santé.",
          ],
        },
        {
          t: '9. Propriété intellectuelle',
          p: [
            'Le code de BébéCare, son interface et ses textes sont protégés.',
            'Vous pouvez citer BébéCare en indiquant la source et le lien, ' +
              'notamment dans un travail universitaire ou un article de presse.',
            'La réutilisation commerciale du service ou d\'une partie de son ' +
              'contenu nécessite un accord écrit de l\'éditeur.',
          ],
        },
        {
          t: '10. Suspension et résiliation',
          p: [
            'Vous pouvez supprimer votre compte à tout moment, depuis Mon espace.',
            "L'éditeur peut suspendre un compte utilisé pour un usage interdit, " +
              'après notification, hors cas de danger immédiat pour le service ' +
              'ou pour des personnes.',
          ],
        },
        {
          t: '11. Droit applicable',
          p: [
            'Ces conditions sont régies par le droit béninois.',
            'En cas de litige, une solution amiable est recherchée d\'abord, ' +
              'par email à ' + EDITEUR.email + '. À défaut, les tribunaux de ' +
              'Cotonou sont compétents.',
          ],
        },
      ],
    },

    mentions: {
      titre: 'Mentions légales',
      chapeau:
        "Informations d'identification de l'éditeur du site, de l'hébergeur " +
        'et des sources utilisées.',
      sections: [
        {
          t: 'Éditeur du site',
          p: [
            EDITEUR.nom,
            EDITEUR.fr,
            EDITEUR.ville.fr,
            'Contact : ' + EDITEUR.email,
          ],
        },
        {
          t: 'Hébergement',
          p: [
            'Site et API : Render, région de Francfort, Allemagne, Union européenne.',
            'Base de données des comptes : PostgreSQL géré par Neon, Union européenne.',
            'Instance DHIS2 de démonstration : play.im.dhis2.org (Sierra Leone). ' +
              "Il s'agit de données fictives de démonstration, aucune base " +
              'nationale de production n\'est connectée.',
          ],
        },
        {
          t: 'Responsable de traitement',
          p: [
            'Le responsable du traitement des données est l\'éditeur du site, ' +
              'identifié ci dessus, joignable à ' + EDITEUR.email + '.',
            'Voir la politique de confidentialité pour le détail des données, ' +
              'des durées de conservation et des droits.',
          ],
        },
        {
          t: 'Propriété et crédits',
          p: [
            'BébéCare : conception, développement et contenu par ' + EDITEUR.nom + '.',
            'Cartographie : © les contributeurs OpenStreetMap (ODbL 1.0).',
            'Fonds de carte : OpenFreeMap.',
            'Normes de croissance et couverture vaccinale : Organisation ' +
              'mondiale de la Santé (données ouvertes).',
            'Algorithme de triage : OMS et UNICEF, PCIME.',
            'Météo locale : Open-Meteo.',
          ],
        },
        {
          t: 'Signalement',
          p: [
            'Une erreur de donnée, un centre de santé manquant, un texte à ' +
              'corriger, un problème d\'accès ? Écrivez à ' + EDITEUR.email +
              ' en précisant la page et ce que vous observez. Chaque ' +
              'signalement est examiné et corrigé avec sa source.',
          ],
        },
        {
          t: 'Accessibilité',
          p: [
            'Le site vise le niveau AA des règles pour l\'accessibilité des ' +
              'contenus web (WCAG 2.2) : navigation au clavier, contrastes ' +
              'suffisants, libellés de formulaires, textes redimensionnables, ' +
              'respect du réglage de réduction des animations.',
            'Si un écran reste difficile à utiliser, signalez le : il sera ' +
              'corrigé en priorité.',
          ],
        },
      ],
    },
  },

  en: {
    onglet_confidentialite: 'Privacy',
    onglet_conditions: 'Terms of use',
    onglet_mentions: 'Legal notice',
    version_label: 'Version',
    maj_label: 'Last updated',
    retour_haut: 'Back to top',
    imprimer: 'Print or save as PDF',

    confidentialite: {
      titre: 'Privacy policy',
      chapeau:
        'BébéCare processes health data of children under five. That is a ' +
        'responsibility, not a formality. This page explains, plainly, what ' +
        'data is kept, why, for how long, and how to have it deleted.',
      sections: [
        {
          t: '1. Who is responsible',
          p: [
            EDITEUR.nom + ', ' + EDITEUR.en,
            'Contact for any question or to exercise your rights: ' +
              EDITEUR.email + ' (reply within 30 days).',
            'BébéCare is an independent, non-profit project with no ' +
              'advertising. It belongs to no company, insurer or laboratory.',
          ],
        },
        {
          t: '2. What data is kept',
          p: [
            'Account (optional): an identifier, which is an email address or ' +
              'a phone number, a display name if you provide one, the ' +
              'country, the language, your profile (parent or health worker) ' +
              'and your password.',
            'Password: never stored in clear text. It is processed with ' +
              'PBKDF2-HMAC-SHA256, 240,000 iterations and a unique salt per ' +
              'account. Nobody, including the editor, can read it back.',
            'Child follow-up: first name, sex, date of birth, country, ' +
              'vaccines ticked, and for each measurement the date, age, ' +
              'weight, height, mid-upper arm circumference and the z-scores ' +
              'computed from WHO standards.',
            'Technical data: your IP address is used at request time to limit ' +
              'abuse (repeated sign-in attempts, bulk calls) and is not kept ' +
              'with your record.',
          ],
        },
        {
          t: '3. Why this data is processed',
          p: [
            'To show the vaccination schedule matching your country and your ' +
              "child's age.",
            'To compute growth z-scores and flag acute or chronic malnutrition ' +
              'using WHO thresholds.',
            'To synchronise the follow-up across your devices, if you create ' +
              'an account.',
            'To keep the service secure: limiting abusive sign-in attempts and ' +
              'protecting accounts.',
            'No profiling, no automated decision with legal effect, no ' +
              'commercial use.',
          ],
        },
        {
          t: '4. What BébéCare never does',
          p: [
            'No sale or rental of data, to anyone.',
            'No advertising and no advertising tracker.',
            'No analytics cookie and no social network cookie.',
            'No transfer to an insurer, an employer or a broker.',
            'No publication of data that could identify a child.',
            'No use of your data to train an AI model.',
          ],
        },
        {
          t: '5. Who can see the data',
          p: [
            'You only, for your account and your children.',
            'Hosting: Render (Frankfurt, Germany) for the site and the API, ' +
              'and a PostgreSQL database managed by Neon (European Union) for ' +
              'the accounts.',
            'AI assistant: when you ask a question in free text, the question ' +
              "text and the child's age are sent to the language model " +
              'provider. Your name, your identifier and the child name are ' +
              'never sent. If you prefer to send nothing, tick the checklist: ' +
              'the IMCI decision is taken entirely without AI.',
            'DHIS2: the gateway is connected to a public demonstration ' +
              'instance. No child data is sent to it, and writing is disabled ' +
              'by default.',
            'No other recipient. No transfer for commercial purposes.',
          ],
        },
        {
          t: '6. How long data is kept',
          p: [
            'The follow-up is kept as long as your account exists.',
            'You can delete a child at any time: the measurements are erased ' +
              'at the same time.',
            'You can delete your account at any time from My space: the ' +
              'account, the children and all measurements are erased ' +
              'immediately, with no copy kept.',
            'Accounts unused for more than 24 months may be deleted after a ' +
              'reminder email.',
          ],
        },
        {
          t: '7. Your rights',
          p: [
            'Access: see everything kept about you.',
            'Rectification: correct a first name, a date of birth, a measurement.',
            'Erasure: delete a child or the whole account.',
            'Portability: download your data as a readable JSON file from My space.',
            'Objection and withdrawal of consent: you may withdraw consent at ' +
              'any time, which amounts to deleting the account.',
            'To exercise these rights: the buttons in My space, or an email to ' +
              EDITEUR.email + '. You receive an answer within 30 days.',
            'You may also contact the Personal Data Protection Authority ' +
              '(APDP) of Benin if you consider your rights are not respected.',
          ],
        },
        {
          t: '8. Data of a child under five',
          p: [
            'The account is created and used by a parent, a guardian or a ' +
              'health professional, who provides the child data under their ' +
              'responsibility.',
            'The child cannot create an account and receives no message.',
            'If you notice an account created with a child data without the ' +
              'legal guardian agreement, write to ' + EDITEUR.email + ' and ' +
              'the account is deleted.',
          ],
        },
        {
          t: '9. Security',
          p: [
            'The site is served over HTTPS. Passwords are hashed with PBKDF2 ' +
              '(240,000 iterations, unique salt per account).',
            'Security headers are enabled: content security policy, MIME ' +
              'sniffing protection, referrer restriction, minimal permissions.',
            'Sign-in attempts and costly calls are rate limited per IP ' +
              'address. Session tokens expire after 30 days and are ' +
              'invalidated as soon as the password changes.',
            'Account responses are never cached by a shared browser or proxy.',
            'In the event of a data breach likely to create a high risk, the ' +
              'people concerned are informed without delay, as well as the APDP.',
          ],
        },
        {
          t: '10. Cookies and local storage',
          p: [
            'BébéCare sets no cookie.',
            'The browser only keeps your session token, your country and your ' +
              'language in local storage. This information never leaves your ' +
              'device and is not used for advertising. Signing out clears the ' +
              'token.',
          ],
        },
        {
          t: '11. Legal framework',
          p: [
            'BébéCare applies the principles of the General Data Protection ' +
              'Regulation (minimisation, defined purpose, limited retention, ' +
              'data subject rights).',
            'In Benin, personal data processing falls under the Digital Code ' +
              '(Law 2017-20) and the supervision of the APDP.',
          ],
        },
        {
          t: '12. Changes to this policy',
          p: [
            'Any change is dated and its version number changes. If the change ' +
              'is significant, it is announced at sign-in and a new consent ' +
              'is requested before continuing.',
          ],
        },
      ],
    },

    conditions: {
      titre: 'Terms of use',
      chapeau:
        'BébéCare helps to orient, to track vaccination and to screen for ' +
        'malnutrition. It is not a doctor and not an emergency service. These ' +
        'terms state exactly what the service does and does not do.',
      sections: [
        {
          t: '1. Purpose',
          p: [
            'BébéCare is an information and orientation tool for child health ' +
              'from 0 to 5 years, covering the 15 ECOWAS countries.',
            'The service applies public rules: the WHO and UNICEF IMCI ' +
              'algorithm for danger sign triage, WHO growth standards for ' +
              'z-scores, national immunisation schedules for reminders.',
            'Clinical tools are free and require no account.',
          ],
        },
        {
          t: '2. What BébéCare is not',
          p: [
            'It is not a medical device and it makes no diagnosis.',
            'It is not an emergency service. In immediate danger, call your ' +
              'country emergency number, shown in the application, or go to ' +
              'the nearest health centre.',
            'It is not telemedicine: no remote consultation takes place and no ' +
              'professional answers you inside the application.',
            'Results are decision aids. A health professional remains the only ' +
              'judge of what to do.',
          ],
        },
        {
          t: '3. Permitted use',
          p: [
            'You may use BébéCare for yourself, for a child you are ' +
              'responsible for, or as part of your health work, without ' +
              'commercial purpose.',
            'You agree to enter accurate information and not to record data of ' +
              'a child you are not responsible for.',
          ],
        },
        {
          t: '4. Prohibited use',
          p: [
            'Bulk extraction of site data (automated scraping, download bot) ' +
              'or bypassing rate limits.',
            'Reselling, sub-licensing or redistributing the service or its data.',
            'Attempting to access another person account, guess a password or ' +
              'disturb the service.',
            'Impersonating the editor, a Ministry of Health, WHO or a health ' +
              'centre.',
            'Presenting the results of the site as signed medical advice.',
          ],
        },
        {
          t: '5. Accounts and security',
          p: [
            'You are responsible for keeping your password confidential and ' +
              'for use made from your account.',
            'Choose a password of at least 8 characters, unique, and change it ' +
              'if you think it was disclosed: the change signs out every open ' +
              'session.',
            'The account is optional: all tools work without registration, ' +
              'only longitudinal follow-up needs an account.',
          ],
        },
        {
          t: '6. Sources and licences',
          p: [
            'Health facilities: OpenStreetMap, ODbL 1.0 licence, credit ' +
              '© OpenStreetMap contributors.',
            'Vaccination coverage and growth standards: World Health ' +
              'Organization, open data.',
            'Immunisation schedules: national immunisation programmes, ' +
              'compiled and dated.',
            'Triage: IMCI algorithm (Integrated Management of Childhood ' +
              'Illness) from WHO and UNICEF.',
            'Basemaps: OpenFreeMap, OpenStreetMap data.',
            'Every data screen states its source and date. Information without ' +
              'a dated source is not reference information.',
          ],
        },
        {
          t: '7. Accuracy and limits',
          p: [
            'Map data is crowd sourced: a health centre may be closed, moved ' +
              'or not listed.',
            'Immunisation schedules may change: the national schedule and the ' +
              "child's vaccination card at the health centre prevail.",
            'WHO growth tables are interpolated: a single measurement does not ' +
              'replace a curve followed over time.',
          ],
        },
        {
          t: '8. Liability',
          p: [
            'BébéCare is provided as is, without warranty of permanent ' +
              'accuracy or continuous availability.',
            'The editor cannot be held liable for a decision taken on the sole ' +
              'basis of a displayed result, nor for unavailability of the ' +
              'service, nor for a third party use of the open data it ' +
              'redistributes.',
            'The editor liability cannot exceed what applicable law allows for ' +
              'a free health information service.',
          ],
        },
        {
          t: '9. Intellectual property',
          p: [
            'The BébéCare code, interface and texts are protected.',
            'You may cite BébéCare stating the source and the link, for ' +
              'instance in academic work or a press article.',
            'Commercial reuse of the service or part of its content requires ' +
              'written agreement from the editor.',
          ],
        },
        {
          t: '10. Suspension and termination',
          p: [
            'You can delete your account at any time, from My space.',
            'The editor may suspend an account used for prohibited purposes, ' +
              'after notification, except where there is immediate danger for ' +
              'the service or for people.',
          ],
        },
        {
          t: '11. Applicable law',
          p: [
            'These terms are governed by Beninese law.',
            'In case of dispute, an amicable solution is sought first, by ' +
              'email to ' + EDITEUR.email + '. Failing that, the courts of ' +
              'Cotonou have jurisdiction.',
          ],
        },
      ],
    },

    mentions: {
      titre: 'Legal notice',
      chapeau:
        'Identifying information about the site editor, the host and the ' +
        'sources used.',
      sections: [
        {
          t: 'Site editor',
          p: [
            EDITEUR.nom,
            EDITEUR.en,
            EDITEUR.ville.en,
            'Contact: ' + EDITEUR.email,
          ],
        },
        {
          t: 'Hosting',
          p: [
            'Site and API: Render, Frankfurt region, Germany, European Union.',
            'Account database: PostgreSQL managed by Neon, European Union.',
            'DHIS2 demonstration instance: play.im.dhis2.org (Sierra Leone). ' +
              'This is fictional demonstration data, no national production ' +
              'database is connected.',
          ],
        },
        {
          t: 'Data controller',
          p: [
            'The data controller is the site editor identified above, ' +
              'reachable at ' + EDITEUR.email + '.',
            'See the privacy policy for the detail of data, retention periods ' +
              'and rights.',
          ],
        },
        {
          t: 'Ownership and credits',
          p: [
            'BébéCare: design, development and content by ' + EDITEUR.nom + '.',
            'Mapping: © OpenStreetMap contributors (ODbL 1.0).',
            'Basemaps: OpenFreeMap.',
            'Growth standards and vaccination coverage: World Health ' +
              'Organization (open data).',
            'Triage algorithm: WHO and UNICEF, IMCI.',
            'Local weather: Open-Meteo.',
          ],
        },
        {
          t: 'Reporting',
          p: [
            'A data error, a missing health centre, a text to fix, an access ' +
              'problem? Write to ' + EDITEUR.email + ' stating the page and ' +
              'what you observe. Every report is reviewed and corrected with ' +
              'its source.',
          ],
        },
        {
          t: 'Accessibility',
          p: [
            'The site targets level AA of the Web Content Accessibility ' +
              'Guidelines (WCAG 2.2): keyboard navigation, sufficient ' +
              'contrast, labelled form fields, resizable text, respect for the ' +
              'reduced motion setting.',
            'If a screen remains difficult to use, report it: it will be fixed ' +
              'as a priority.',
          ],
        },
      ],
    },
  },
}

/* Couples de libellés utilisés par la page légale et par la modale
   d'inscription, dans les deux langues. */
export const ONGLETS_LEGAUX = ['confidentialite', 'conditions', 'mentions']
