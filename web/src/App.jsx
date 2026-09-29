import { useEffect, useState } from 'react'
import { api } from './api'
import { useLangue } from './i18n'
import { FournisseurAuth, useAuth } from './auth'
import { EDITEUR } from './legal'
import Accueil from './pages/Accueil'
import Carte from './pages/Carte'
import Assistant from './pages/Assistant'
import Vaccins from './pages/Vaccins'
import Nutrition from './pages/Nutrition'
import Donnees from './pages/Donnees'
import APropos from './pages/APropos'
import Bouclier from './Bouclier'
import Soignant from './pages/Soignant'
import Legal from './pages/Legal'
import Compte, { ModaleAuth } from './pages/Compte'

// [clé, libellé nav, titre de bandeau, sous-titre de bandeau]
const cles = ['accueil', 'carte', 'assistant', 'vaccins', 'nutrition',
              'soignant', 'donnees', 'apropos', 'compte', 'legal']

// [libellé nav, titre de bandeau, sous-titre] ; null = pas de bandeau (accueil, carte)
const construirePages = (t) => Object.fromEntries(cles.map((c) => [
  c,
  (c === 'accueil' || c === 'carte' || c === 'legal')
    ? [t(`nav_${c}`), null, null]
    : [t(`nav_${c}`) || c, t(`t_${c}`), t(`s_${c}`)],
]))

const NAV = ['accueil', 'carte', 'assistant', 'vaccins', 'nutrition', 'soignant', 'donnees', 'apropos']

// Adresses directes : une page légale est citable telle quelle.
const PAR_HASH = {
  '#confidentialite': ['legal', 'confidentialite'],
  '#conditions': ['legal', 'conditions'],
  '#mentions': ['legal', 'mentions'],
  '#carte': ['carte', null],
  '#assistant': ['assistant', null],
  '#vaccins': ['vaccins', null],
  '#nutrition': ['nutrition', null],
  '#donnees': ['donnees', null],
  '#apropos': ['apropos', null],
  '#compte': ['compte', null],
}

function Interieur() {
  const { t, langue, changer } = useLangue()
  const PAGES = construirePages(t)
  const { connecte, utilisateur, deconnecter } = useAuth()
  const [onglet, setOnglet] = useState(() => (PAR_HASH[window.location.hash] || ['accueil'])[0])
  const [docLegal, setDocLegal] = useState(
    () => (PAR_HASH[window.location.hash] || [null, 'confidentialite'])[1] || 'confidentialite')
  const [menu, setMenu] = useState(false)
  const [listePays, setListePays] = useState([])
  const [pays, setPays] = useState(() => localStorage.getItem('bebecare.pays') || 'bj')
  const [categories, setCategories] = useState({})
  const [dhis2, setDhis2] = useState(null)
  const [modale, setModale] = useState(false)

  const dossier = listePays.find((p) => p.code === pays)

  useEffect(() => {
    api.pays().then(setListePays).catch(() => {})
    api.categories().then(setCategories).catch(() => {})
    api.dhis2Statut().then(setDhis2).catch(() => setDhis2({ connecte: false }))
  }, [])

  useEffect(() => {
    if (utilisateur) {
      if (utilisateur.pays) setPays(utilisateur.pays)
      if (utilisateur.langue && utilisateur.langue !== langue) changer(utilisateur.langue)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [utilisateur])

  useEffect(() => { localStorage.setItem('bebecare.pays', pays) }, [pays])

  // La langue annoncée au navigateur et aux lecteurs d'écran suit le choix.
  useEffect(() => { document.documentElement.lang = langue }, [langue])

  // Titre et description de l'onglet : utiles au partage et au référencement.
  useEffect(() => {
    const titre = onglet === 'legal'
      ? t('pied_legal')
      : PAGES[onglet]?.[1] || PAGES[onglet]?.[0] || 'BébéCare'
    document.title = `${titre} · BébéCare`
    const resume = onglet === 'legal'
      ? t('s_apropos')
      : PAGES[onglet]?.[2] || t('pied_texte')
    const meta = document.querySelector('meta[name="description"]')
    if (meta && resume) meta.setAttribute('content', resume)
  }, [onglet, t, PAGES])

  // Adresse directe : #confidentialite, #conditions, #mentions.
  useEffect(() => {
    function surHash() {
      const cible = PAR_HASH[window.location.hash]
      if (!cible) return
      setOnglet(cible[0])
      if (cible[1]) setDocLegal(cible[1])
    }
    window.addEventListener('hashchange', surHash)
    return () => window.removeEventListener('hashchange', surHash)
  }, [])

  // La langue de l'interface suit le pays choisi (Nigeria -> anglais, Bénin -> français).
  // Le choix manuel dans le sélecteur FR/EN reste prioritaire jusqu'au prochain changement de pays.
  function changerPays(code) {
    setPays(code)
    const p = listePays.find((x) => x.code === code)
    if (p) {
      const cible = p.langue === 'en' ? 'en' : 'fr'   // pt (Cabo Verde, Guinée-Bissau) -> français
      if (cible !== langue) changer(cible)
    }
  }
  useEffect(() => { window.scrollTo(0, 0); setMenu(false) }, [onglet])

  // Fermeture de la fenêtre d'inscription au clavier (touche Échap).
  useEffect(() => {
    if (!modale) return undefined
    const surTouche = (e) => { if (e.key === 'Escape') setModale(false) }
    window.addEventListener('keydown', surTouche)
    return () => window.removeEventListener('keydown', surTouche)
  }, [modale])

  function ouvrirLegal(cle = 'confidentialite') {
    setDocLegal(cle)
    setOnglet('legal')
    if (window.location.hash !== `#${cle}`) window.location.hash = cle
  }

  const props = { pays, listePays, categories, t, aller: setOnglet,
                  ouvrirAuth: () => setModale(true), ouvrirLegal }
  const [, titre, soustitre] = PAGES[onglet]
  const pleinEcran = onglet === 'carte'

  const page = (
    <Bouclier key={onglet}>
      {onglet === 'accueil' && <Accueil {...props} />}
      {onglet === 'carte' && <Carte {...props} />}
      {onglet === 'assistant' && <Assistant {...props} />}
      {onglet === 'vaccins' && <Vaccins {...props} />}
      {onglet === 'nutrition' && <Nutrition {...props} />}
      {onglet === 'soignant' && <Soignant {...props} />}
      {onglet === 'donnees' && <Donnees {...props} />}
      {onglet === 'apropos' && <APropos {...props} />}
      {onglet === 'compte' && <Compte {...props} />}
      {onglet === 'legal' && <Legal ongletInitial={docLegal} />}
    </Bouclier>
  )

  const lienErreur = `mailto:${EDITEUR.email}?subject=${encodeURIComponent('Signalement BébéCare')}`

  return (
    <>
      <a className="lien-evitement" href="#contenu">{t('contenu_principal')}</a>

      <header>
      <nav className={`sib-nav ${menu ? 'open' : ''}`} aria-label={t('navigation_principale')}>
        <div className="container nav-inner">
          <a className="sib-brand" href="#accueil" aria-label="BébéCare, accueil"
             onClick={(e) => { e.preventDefault(); setOnglet('accueil') }}>
            <img src="/logo-bebecare.png" alt="BébéCare" width="295" height="97" />
          </a>
          <button className="nav-toggler" type="button" aria-label={t('menu')}
                  aria-expanded={menu} aria-controls="menu-principal"
                  onClick={() => setMenu(!menu)}>☰</button>
          <div className="nav-links" id="menu-principal">
            {NAV.map((k) => (
              <button key={k} className={onglet === k ? 'active' : ''}
                      aria-current={onglet === k ? 'page' : undefined}
                      onClick={() => { setOnglet(k); setMenu(false) }}>
                {PAGES[k][0]}
              </button>
            ))}
            {!connecte && (
              <button className="lien-menu-connexion"
                      onClick={() => { setModale(true); setMenu(false) }}>
                {t('connexion')}
              </button>
            )}
          </div>
          <div className="nav-cta">
            <select className="nav-select" aria-label={t('pays')} value={pays} onChange={(e) => changerPays(e.target.value)}>
              {listePays.map((p) => (
                <option key={p.code} value={p.code}>{p.drapeau} {p.code.toUpperCase()}</option>
              ))}
            </select>
            <select className="nav-select" aria-label={t('langue')} value={langue} onChange={(e) => changer(e.target.value)}>
              <option value="fr">FR</option><option value="en">EN</option>
            </select>
            {connecte ? (
              <>
                <button className="btn btn-ghost btn-sm" onClick={() => setOnglet('compte')}>{t('mon_espace')}</button>
                <button className="btn btn-primary btn-sm" onClick={deconnecter}>{t('deconnexion')}</button>
              </>
            ) : (
              <>
                <button className="btn btn-ghost btn-sm" onClick={() => setModale(true)}>{t('connexion')}</button>
                <button className="btn btn-primary btn-sm btn-inscription" onClick={() => setModale(true)}>{t('creer_compte')}</button>
              </>
            )}
          </div>
        </div>
      </nav>
      </header>

      <main id="contenu" tabIndex={-1}>
      {pleinEcran ? page : (
        <>
          {titre && (
            <div className="page-head">
              <div className="container">
                <h1>{titre}</h1>
                <p>{soustitre}</p>
              </div>
            </div>
          )}
          {titre ? <div className="page-body"><div className="container">{page}</div></div> : page}
        </>
      )}
      {onglet !== 'accueil' && !pleinEcran && (
        <div className="container" style={{ paddingBottom: 10 }}>
          <p className="fil-pays">
            {dossier && <>{t('pays')} : <b>{dossier.drapeau} {dossier.nom}</b> · </>}
            {t('pied_identite')}
          </p>
        </div>
      )}
      </main>

      {!pleinEcran && (
        <footer className="site-footer">
          <div className="container">
            <div className="foot-grid">
              <div>
                <a className="sib-brand" href="#accueil"
                   onClick={(e) => { e.preventDefault(); setOnglet('accueil') }}>
                  <img src="/logo-bebecare.png" alt="BébéCare" width="295" height="97" />
                </a>
                <p>{t('pied_texte')}</p>
                <p className="pied-identite">{t('pied_identite')}</p>
              </div>
              <div>
                <h5>{t('pied_outils')}</h5>
                <ul>
                  <li><a href="#carte" onClick={(e) => { e.preventDefault(); setOnglet('carte') }}>{t('pied_carte')}</a></li>
                  <li><a href="#nutrition" onClick={(e) => { e.preventDefault(); setOnglet('nutrition') }}>{t('pied_nutrition')}</a></li>
                  <li><a href="#vaccins" onClick={(e) => { e.preventDefault(); setOnglet('vaccins') }}>{t('pied_vaccins')}</a></li>
                  <li><a href="#assistant" onClick={(e) => { e.preventDefault(); setOnglet('assistant') }}>{t('pied_assistant')}</a></li>
                  <li><a href="#donnees" onClick={(e) => { e.preventDefault(); setOnglet('donnees') }}>{t('pied_sources')}</a></li>
                </ul>
              </div>
              <div>
                <h5>{t('pied_legal')}</h5>
                <ul>
                  <li><a href="#confidentialite" onClick={(e) => { e.preventDefault(); ouvrirLegal('confidentialite') }}>{t('pied_confidentialite')}</a></li>
                  <li><a href="#conditions" onClick={(e) => { e.preventDefault(); ouvrirLegal('conditions') }}>{t('pied_conditions')}</a></li>
                  <li><a href="#mentions" onClick={(e) => { e.preventDefault(); ouvrirLegal('mentions') }}>{t('pied_mentions')}</a></li>
                </ul>
              </div>
              <div>
                <h5>{t('pied_contact')}</h5>
                <ul>
                  <li><a href={`mailto:${EDITEUR.email}`}>{EDITEUR.email}</a></li>
                  <li>
                    <a href="https://wa.me/2290198419240?text=Bonjour%2C%20je%20vous%20contacte%20depuis%20B%C3%A9b%C3%A9Care"
                       target="_blank" rel="noopener noreferrer" style={{ fontWeight: 700 }}>
                      {'💬 WhatsApp'}
                    </a>
                  </li>
                  <li>{EDITEUR.ville[langue] || EDITEUR.ville.fr}</li>
                  <li><a href={lienErreur}>{t('pied_signaler')}</a></li>
                  <li><a href="https://www.linkedin.com/in/gninaz%C3%A9-mingniss%C3%AA-darius-sossa-743721376"
                         target="_blank" rel="noopener noreferrer">LinkedIn</a></li>
                  <li><a href="https://github.com/sgmd98" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                </ul>
              </div>
            </div>
            <div className="foot-bottom">
              <span>
                © 2026 BébéCare : {t('pied_droits')}
                {dhis2 && (
                  <span className={`dhis2-dot ${dhis2.connecte ? 'on' : 'off'}`}
                        style={{ marginLeft: 12 }} title={dhis2.instance}>
                    <i />DHIS2 {dhis2.connecte ? `v${dhis2.version}` : t('pied_hors_ligne')}
                  </span>
                )}
              </span>
              <span>
                {t('pied_confidentialite')} · {t('pied_conditions')} · v2.17
              </span>
            </div>
          </div>
        </footer>
      )}

      {modale && (
        <ModaleAuth listePays={listePays} paysDefaut={pays} langueDefaut={langue}
                    fermer={() => setModale(false)} ouvrirLegal={ouvrirLegal} />
      )}
    </>
  )
}

export default function App() {
  return <FournisseurAuth><Interieur /></FournisseurAuth>
}
