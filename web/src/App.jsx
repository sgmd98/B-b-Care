import { useEffect, useState } from 'react'
import { api } from './api'
import { useLangue } from './i18n'
import { FournisseurAuth, useAuth } from './auth'
import Accueil from './pages/Accueil'
import Carte from './pages/Carte'
import Assistant from './pages/Assistant'
import Vaccins from './pages/Vaccins'
import Nutrition from './pages/Nutrition'
import Donnees from './pages/Donnees'
import APropos from './pages/APropos'
import Bouclier from './Bouclier'
import Soignant from './pages/Soignant'
import Compte, { ModaleAuth } from './pages/Compte'

// [clé, libellé nav, titre de bandeau, sous-titre de bandeau]
const cles = ['accueil', 'carte', 'assistant', 'vaccins', 'nutrition',
              'soignant', 'donnees', 'apropos', 'compte']

// [libellé nav, titre de bandeau, sous-titre] ; null = pas de bandeau (accueil, carte)
const construirePages = (t) => Object.fromEntries(cles.map((c) => [
  c,
  (c === 'accueil' || c === 'carte')
    ? [t(`nav_${c}`), null, null]
    : [t(`nav_${c}`) || c, t(`t_${c}`), t(`s_${c}`)],
]))

const NAV = ['accueil', 'carte', 'assistant', 'vaccins', 'nutrition', 'soignant', 'donnees', 'apropos']

function Interieur() {
  const { t, langue, changer } = useLangue()
  const PAGES = construirePages(t)
  const { connecte, utilisateur, deconnecter } = useAuth()
  const [onglet, setOnglet] = useState('accueil')
  const [menu, setMenu] = useState(false)
  const [listePays, setListePays] = useState([])
  const [pays, setPays] = useState(() => localStorage.getItem('bebecare.pays') || 'bj')
  const [categories, setCategories] = useState({})
  const [dhis2, setDhis2] = useState(null)
  const [modale, setModale] = useState(false)

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

  const props = { pays, listePays, categories, t, aller: setOnglet, ouvrirAuth: () => setModale(true) }
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
    </Bouclier>
  )

  return (
    <>
      <nav className={`sib-nav ${menu ? 'open' : ''}`}>
        <div className="container nav-inner">
          <a className="sib-brand" href="#" onClick={(e) => { e.preventDefault(); setOnglet('accueil') }}>
            <img src="/logo-bebecare.png" alt="BébéCare" />
          </a>
          <button className="nav-toggler" type="button" aria-label="Menu" onClick={() => setMenu(!menu)}>☰</button>
          <div className="nav-links">
            {NAV.map((k) => (
              <button key={k} className={onglet === k ? 'active' : ''}
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
            <select className="nav-select" value={pays} onChange={(e) => changerPays(e.target.value)}>
              {listePays.map((p) => (
                <option key={p.code} value={p.code}>{p.drapeau} {p.code.toUpperCase()}</option>
              ))}
            </select>
            <select className="nav-select" value={langue} onChange={(e) => changer(e.target.value)}>
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

      {!pleinEcran && (
        <footer className="site-footer">
          <div className="container">
            <div className="foot-grid">
              <div>
                <a className="sib-brand" href="#" onClick={(e) => { e.preventDefault(); setOnglet('accueil') }}>
                  <img src="/logo-bebecare.png" alt="BébéCare" />
                </a>
                <p>{t('pied_texte')}</p>
              </div>
              <div>
                <h5>{t('pied_outils')}</h5>
                <ul>
                  <li><a href="#" onClick={(e) => { e.preventDefault(); setOnglet('carte') }}>{t('pied_carte')}</a></li>
                  <li><a href="#" onClick={(e) => { e.preventDefault(); setOnglet('nutrition') }}>{t('pied_nutrition')}</a></li>
                  <li><a href="#" onClick={(e) => { e.preventDefault(); setOnglet('vaccins') }}>{t('pied_vaccins')}</a></li>
                  <li><a href="#" onClick={(e) => { e.preventDefault(); setOnglet('assistant') }}>{t('pied_assistant')}</a></li>
                </ul>
              </div>
              <div>
                <h5>{t('pied_contact')}</h5>
                <ul>
                  <li><a href="mailto:sante.infantile.benin@gmail.com">sante.infantile.benin@gmail.com</a></li>
                  <li>
                    <a href="https://wa.me/2290198419240?text=Bonjour%2C%20je%20vous%20contacte%20depuis%20B%C3%A9b%C3%A9Care"
                       target="_blank" rel="noopener noreferrer" style={{ fontWeight: 700 }}>
                      {'💬 WhatsApp'}
                    </a>
                  </li>
                  <li>Cotonou, Bénin</li>
                  <li><a href="https://www.linkedin.com/in/gninaz%C3%A9-mingniss%C3%AA-darius-sossa-743721376"
                         target="_blank" rel="noopener noreferrer">LinkedIn</a></li>
                  <li><a href="https://github.com/sosak98" target="_blank" rel="noopener noreferrer">GitHub</a></li>
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
              <span>Développé par SOSSA G. M. Darius</span>
            </div>
          </div>
        </footer>
      )}

      {modale && (
        <ModaleAuth listePays={listePays} paysDefaut={pays} langueDefaut={langue}
                    fermer={() => setModale(false)} />
      )}
    </>
  )
}

export default function App() {
  return <FournisseurAuth><Interieur /></FournisseurAuth>
}
