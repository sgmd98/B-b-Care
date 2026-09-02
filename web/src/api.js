const BASE = ''

/* Extrait un message lisible des erreurs FastAPI (detail en chaine ou liste)
   pour ne jamais afficher de JSON brut a l'ecran. */
async function messageErreur(r) {
  let corps = null
  try { corps = await r.json() } catch { /* pas du JSON */ }
  if (corps) {
    if (typeof corps.detail === 'string') return corps.detail
    if (Array.isArray(corps.detail)) {
      const morceaux = corps.detail.map((e) => {
        if (typeof e === 'string') return e
        if (e?.msg) {
          // traduit les schemas pydantic courants tombes entre les mailles
          if (e.msg.includes('greater than or equal')) return `${e.loc?.slice(-1)[0]} : valeur trop petite`
          if (e.msg.includes('greater than')) return `${e.loc?.slice(-1)[0]} : valeur trop petite`
          if (e.msg.includes('less than')) return `${e.loc?.slice(-1)[0]} : valeur trop grande`
          return e.msg
        }
        return JSON.stringify(e)
      })
      return morceaux.join(' · ')
    }
    return JSON.stringify(corps)
  }
  return `Erreur reseau (${r.status}). Verifiez votre connexion et reessayez.`
}

async function req(chemin, options) {
  let r
  try {
    r = await fetch(BASE + chemin, options)
  } catch {
    throw new Error(`Impossible de joindre le serveur. Verifiez votre connexion et reessayez.`)
  }
  if (!r.ok) throw new Error(await messageErreur(r))
  return r.json()
}

export const api = {
  sante: () => req('/api/sante'),
  pays: () => req('/api/pays'),
  detailPays: (c) => req(`/api/pays/${c}`),
  categories: () => req('/api/categories'),
  stats: () => req('/api/carte/stats'),

  bbox: (b, pays, types, limite = 1500) => {
    const p = new URLSearchParams({
      sud: b.sud, ouest: b.ouest, nord: b.nord, est: b.est, limite,
    })
    if (pays) p.set('pays', pays)
    if (types && types.length) p.set('types', types.join(','))
    return req(`/api/carte/bbox?${p}`)
  },
  proches: (lat, lon, types, n = 8) => {
    const p = new URLSearchParams({ lat, lon, n })
    if (types && types.length) p.set('types', types.join(','))
    return req(`/api/carte/proches?${p}`)
  },
  recherche: (q, pays) =>
    req(`/api/carte/recherche?q=${encodeURIComponent(q)}${pays ? `&pays=${pays}` : ''}`),

  calendrier: (c) => req(`/api/vaccins/calendrier/${c}`),
  planning: (corps) => req('/api/vaccins/planning', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(corps),
  }),
  urlIcs: (pays, dn) => `/api/vaccins/ics?pays=${pays}&date_naissance=${dn}`,

  depistage: (corps) => req('/api/nutrition/depistage', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(corps),
  }),
  courbe: (indicateur, sexe, xmin, xmax, pas) =>
    req(`/api/nutrition/courbe?indicateur=${indicateur}&sexe=${sexe}&xmin=${xmin}&xmax=${xmax}&pas=${pas}`),

  catalogueTriage: () => req('/api/triage/catalogue'),
  triage: (corps) => req('/api/triage', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(corps),
  }),

  omsComparaison: (i) => req(`/api/oms/comparaison?indicateur=${i}`),
  dhis2Statut: () => req('/api/dhis2/statut'),
  dhis2Couverture: (ou) => req(`/api/dhis2/couverture${ou ? `?ou=${ou}` : ''}`),
  dhis2Districts: () => req('/api/dhis2/districts'),
  dhis2Formations: (n = 300) => req(`/api/dhis2/formations?limite=${n}`),
  dhis2Export: (corps) => req('/api/dhis2/export', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(corps),
  }),
  // ---------------------------------------------------------- comptes
  inscription: (c) => req('/api/compte/inscription', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(c),
  }),
  connexion: (c) => req('/api/compte/connexion', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(c),
  }),
  moi: (j) => req('/api/compte/moi', { headers: { authorization: `Bearer ${j}` } }),
  majProfil: (j, c) => req('/api/compte/moi', {
    method: 'PATCH',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${j}` },
    body: JSON.stringify(c),
  }),
  enfants: (j) => req('/api/compte/enfants', { headers: { authorization: `Bearer ${j}` } }),
  ajouterEnfant: (j, e) => req('/api/compte/enfants', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${j}` },
    body: JSON.stringify(e),
  }),
  majEnfant: (j, id, e) => req(`/api/compte/enfants/${id}`, {
    method: 'PATCH',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${j}` },
    body: JSON.stringify(e),
  }),
  supprimerEnfant: (j, id) => req(`/api/compte/enfants/${id}`, {
    method: 'DELETE', headers: { authorization: `Bearer ${j}` },
  }),
  ajouterMesure: (j, id, m) => req(`/api/compte/enfants/${id}/mesures`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${j}` },
    body: JSON.stringify(m),
  }),
  mesures: (j, id) => req(`/api/compte/enfants/${id}/mesures`, {
    headers: { authorization: `Bearer ${j}` },
  }),

  // ------------------------------------------------------- assistant IA
  assistant: (c) => req('/api/assistant', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(c),
  }),

  sources: () => req('/api/sources'),

  // ---- mode soignant DHIS2 ----
  dhis2Seance: (c) => req('/api/dhis2/seance', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(c),
  }),
  dhis2SeanceEnvoyer: (c) => req('/api/dhis2/seance/envoyer', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(c),
  }),
  assistantQuestion: (c) => req('/api/assistant/question', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(c),
  }),
  assistantStatut: () => req('/api/assistant/statut'),
}
