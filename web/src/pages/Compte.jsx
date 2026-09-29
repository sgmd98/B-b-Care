import { useState } from 'react'
import { useAuth } from '../auth'
import { useLangue } from '../i18n'
import { telechargerJson } from '../api'
import { POINTS_CONFIDENTIALITE, VERSION_POLITIQUE } from '../legal'


export function ModaleAuth({ listePays, paysDefaut, langueDefaut, fermer, ouvrirLegal }) {
  const { inscrire, connecter } = useAuth()
  const { t } = useLangue()
  const [mode, setMode] = useState('inscription')
  const [f, setF] = useState({
    identifiant: '', mot_de_passe: '', nom: '',
    pays: paysDefaut || 'bj', langue: langueDefaut || 'fr', role: 'parent',
  })
  const [consentement, setConsentement] = useState(false)
  const [err, setErr] = useState(null)
  const [occupe, setOccupe] = useState(false)

  async function soumettre(e) {
    e.preventDefault(); setErr(null)
    if (mode === 'inscription' && !consentement) {
      setErr(t('c_consentement_requis'))
      return
    }
    setOccupe(true)
    try {
      if (mode === 'inscription') {
        await inscrire({ ...f, consentement: true, version_politique: VERSION_POLITIQUE })
      } else {
        await connecter(f.identifiant, f.mot_de_passe)
      }
      fermer()
    } catch (e2) {
      const m = String(e2).match(/\{"detail":"(.*?)"\}/)
      setErr(m ? m[1] : String(e2))
    }
    setOccupe(false)
  }

  function allerAuxDocuments(e, cle) {
    e.preventDefault()
    fermer()
    if (ouvrirLegal) ouvrirLegal(cle)
  }

  return (
    <div className="voile-modale" onClick={(e) => e.target === e.currentTarget && fermer()}>
      <div className="modale" role="dialog" aria-modal="true"
           aria-label={mode === 'inscription' ? t('creer_compte') : t('c_connecter_titre')}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
          <img src="/logo-bebecare.png" alt="BébéCare" style={{ height: 46, width: 'auto' }} />
          <div>
            <h2 style={{ margin: 0 }}>{mode === 'inscription' ? t('creer_compte') : t('c_connecter_titre')}</h2>
            <p style={{ margin: '3px 0 0', fontSize: 13, color: 'var(--gris)' }}>
              {t('c_gratuit')}
            </p>
          </div>
          <button type="button" className="modale-fermer" aria-label={t('fermer')}
                  onClick={fermer}>✕</button>
        </div>

        <div className="bascule-modale">
          <button className={mode === 'inscription' ? 'actif' : ''} onClick={() => setMode('inscription')}>{t('c_inscription')}</button>
          <button className={mode === 'connexion' ? 'actif' : ''} onClick={() => setMode('connexion')}>{t('connexion')}</button>
        </div>

        <form onSubmit={soumettre}>
          {mode === 'inscription' && (
            <label className="champ">
              {t('c_nom')}
              <input value={f.nom} onChange={(e) => setF({ ...f, nom: e.target.value })} placeholder="Ex. Aïcha" />
            </label>
          )}
          <label className="champ">
            {t('c_identifiant')}
            <input required value={f.identifiant} autoComplete="username"
                   placeholder={t('c_identifiant_ph')}
                   onChange={(e) => setF({ ...f, identifiant: e.target.value })} />
          </label>
          <label className="champ">
            {t('c_mdp')} {mode === 'inscription' && <span style={{ fontWeight: 500 }}>{t('c_mdp_min')}</span>}
            <input required type="password" value={f.mot_de_passe}
                   autoComplete={mode === 'inscription' ? 'new-password' : 'current-password'}
                   onChange={(e) => setF({ ...f, mot_de_passe: e.target.value })} />
          </label>

          {mode === 'inscription' && (
            <>
              <div className="grille g2" style={{ gap: 10 }}>
                <label className="champ">
                  {t('c_votre_pays')}
                  <select value={f.pays} onChange={(e) => setF({ ...f, pays: e.target.value })}>
                    {listePays.map((p) => <option key={p.code} value={p.code}>{p.drapeau} {p.nom}</option>)}
                  </select>
                </label>
                <label className="champ">
                  {t('langue')}
                  <select value={f.langue} onChange={(e) => setF({ ...f, langue: e.target.value })}>
                    <option value="fr">Français</option>
                    <option value="en">English</option>
                  </select>
                </label>
              </div>
              <label className="champ">
                {t('c_vous_etes')}
                <select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>
                  <option value="parent">{t('c_parent')}</option>
                  <option value="soignant">{t('c_soignant_role')}</option>
                </select>
              </label>
              <p style={{ fontSize: 11.5, color: 'var(--gris)', lineHeight: 1.55, margin: '0 0 14px' }}>
                {t('c_pays_note')}
              </p>

              {/* L'essentiel de la politique, affiché là où le consentement
                  est donné : personne ne lit un document de douze sections
                  avant de cocher une case. Le texte complet reste à un clic. */}
              <details className="essentiel" open>
                <summary>🔒 {t('c_essentiel')}</summary>
                <ul>
                  {POINTS_CONFIDENTIALITE.map((cle) => <li key={cle}>{t(cle)}</li>)}
                </ul>
              </details>

              {/* Consentement : case obligatoire, avec accès direct aux textes.
                  La version acceptée est transmise au serveur et horodatée. */}
              <div className="consentement">
                <label className="consentement-case">
                  <input type="checkbox" required checked={consentement}
                         onChange={(e) => setConsentement(e.target.checked)} />
                  <span>
                    {t('c_consentement')}{' '}
                    <a href="#confidentialite" onClick={(e) => allerAuxDocuments(e, 'confidentialite')}>
                      {t('c_lire_politique')}
                    </a>{' '}
                    {t('c_et')}{' '}
                    <a href="#conditions" onClick={(e) => allerAuxDocuments(e, 'conditions')}>
                      {t('c_lire_conditions')}
                    </a>.
                  </span>
                </label>
                <p className="consentement-note">{t('c_consent_note')}</p>
              </div>
            </>
          )}

          {err && <div className="alerte rouge" style={{ padding: '10px 13px' }}><p>{err}</p></div>}

          <button className="bouton" style={{ width: '100%', justifyContent: 'center' }} disabled={occupe}>
            {occupe ? '…' : mode === 'inscription' ? t('c_creer_mon') : t('c_connecter_titre')}
          </button>
        </form>

        <button className="bouton sec" style={{ width: '100%', justifyContent: 'center', marginTop: 10 }} onClick={fermer}>
          {t('c_continuer_sans')}
        </button>
        <p style={{ fontSize: 11.5, color: 'var(--gris-doux)', textAlign: 'center', marginTop: 12, lineHeight: 1.5 }}>
          {t('c_outils_libres')}
        </p>
      </div>
    </div>
  )
}


/* --------------------------------------------- Mes donnees et mes droits */
function MesDroits({ ouvrirLegal }) {
  const { utilisateur, exporter, supprimerCompte, changerMdp } = useAuth()
  const { t } = useLangue()
  const [mdp, setMdp] = useState('')
  const [ancien, setAncien] = useState('')
  const [nouveau, setNouveau] = useState('')
  const [confirmation, setConfirmation] = useState(false)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [occupe, setOccupe] = useState(false)

  async function faireExport() {
    setErr(null); setMsg(null)
    try {
      const donnees = await exporter()
      telechargerJson(donnees, `bebecare-mes-donnees-${new Date().toISOString().slice(0, 10)}.json`)
      setMsg(t('c_exporter_ok'))
    } catch (e) { setErr(String(e)) }
  }

  async function faireSuppression(e) {
    e.preventDefault()
    setErr(null); setMsg(null); setOccupe(true)
    try { await supprimerCompte(mdp) } catch (e2) { setErr(String(e2)) }
    setOccupe(false)
  }

  async function faireChangementMdp(e) {
    e.preventDefault()
    setErr(null); setMsg(null); setOccupe(true)
    try {
      await changerMdp(ancien, nouveau)
      setMsg(t('c_mdp_change'))
    } catch (e2) { setErr(String(e2)) }
    setOccupe(false)
  }

  return (
    <div className="bloc">
      <h3>{t('c_mes_donnees')}</h3>
      <p className="legende-txt">{t('c_mes_donnees_p')}</p>

      {utilisateur?.consentement_version && (
        <p className="legende-txt" style={{ fontSize: 12.5 }}>
          {t('c_version_politique')} : <b>{utilisateur.consentement_version}</b>
          {utilisateur.consentement_le && (
            <> · {t('c_consentement_le')} {utilisateur.consentement_le.slice(0, 10)}</>
          )}
        </p>
      )}

      <div className="grille g2" style={{ alignItems: 'start' }}>
        <div>
          <button className="bouton sec" onClick={faireExport}>⬇️ {t('c_exporter')}</button>
          <button className="bouton sec" style={{ marginTop: 10 }}
                  onClick={() => ouvrirLegal && ouvrirLegal('confidentialite')}>
            📄 {t('c_lien_documents')}
          </button>
        </div>

        <form onSubmit={faireChangementMdp} className="cadre-form">
          <h4>{t('c_changer_mdp')}</h4>
          <label className="champ">
            {t('c_mdp_actuel')}
            <input required type="password" value={ancien} autoComplete="current-password"
                   onChange={(e) => setAncien(e.target.value)} />
          </label>
          <label className="champ">
            {t('c_nouveau_mdp')}
            <input required type="password" minLength={8} value={nouveau} autoComplete="new-password"
                   onChange={(e) => setNouveau(e.target.value)} />
          </label>
          <button className="bouton sec" disabled={occupe}>{t('c_changer_mdp')}</button>
        </form>
      </div>

      <div className="zone-danger">
        <h4>{t('c_supprimer_compte')}</h4>
        <p>{t('c_supprimer_compte_avert')}</p>
        {!confirmation ? (
          <button className="bouton danger" onClick={() => setConfirmation(true)}>
            {t('c_supprimer_compte')}
          </button>
        ) : (
          <form onSubmit={faireSuppression} className="ligne-danger">
            <input required type="password" value={mdp} autoComplete="current-password"
                   placeholder={t('c_mdp_actuel')} onChange={(e) => setMdp(e.target.value)} />
            <button className="bouton danger" disabled={occupe}>{t('c_supprimer_confirmer')}</button>
            <button type="button" className="bouton sec"
                    onClick={() => { setConfirmation(false); setMdp('') }}>{t('c_annuler')}</button>
          </form>
        )}
      </div>

      {msg && <div className="alerte vert" role="status"><p>{msg}</p></div>}
      {err && <div className="alerte rouge" role="alert"><p>{err}</p></div>}
    </div>
  )
}


export default function Compte({ listePays, ouvrirAuth, ouvrirLegal }) {
  const { connecte, utilisateur, enfants, deconnecter, majProfil, ajouterEnfant, supprimerEnfant } = useAuth()
  const { t, langue } = useLangue()
  const [nouveau, setNouveau] = useState({ prenom: '', sexe: 'm', date_naissance: '' })
  const [err, setErr] = useState(null)

  if (!connecte) {
    return (
      <div className="page">
        <div className="bloc" style={{ textAlign: 'center', padding: 44 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
            <img src="/logo-bebecare.png" alt="BébéCare" style={{ height: 62, width: 'auto' }} />
          </div>
          <h2>{t('c_creer_gratuit')}</h2>
          <p className="legende-txt" style={{ maxWidth: 520, margin: '0 auto 22px' }}>
            {t('c_jamais')}
          </p>
          <div className="grille g3" style={{ textAlign: 'left', marginBottom: 24 }}>
            {[
              ['🌍', t('c_f1_t'), t('c_f1_p')],
              ['🗣️', t('c_f2_t'), t('c_f2_p')],
              ['👶', t('c_f3_t'), t('c_f3_p')],
              ['📈', t('c_f4_t'), t('c_f4_p')],
              ['🔔', t('c_f5_t'), t('c_f5_p')],
              ['🔒', t('c_f6_t'), t('c_f6_p')],
            ].map(([i, tt, d]) => (
              <div key={tt} className="carte-module" style={{ cursor: 'default' }}>
                <div className="ico">{i}</div>
                <b>{tt}</b><p>{d}</p>
              </div>
            ))}
          </div>
          <button className="bouton" onClick={ouvrirAuth}>{t('c_creer_mon_gratuit')}</button>
          <div className="essentiel" style={{ textAlign: 'left', marginTop: 22 }}>
            <b style={{ display: 'block', marginBottom: 8 }}>🔒 {t('c_essentiel')}</b>
            <ul>
              {POINTS_CONFIDENTIALITE.map((cle) => <li key={cle}>{t(cle)}</li>)}
            </ul>
          </div>
          <p style={{ marginTop: 18 }}>
            <button className="lien-texte" onClick={() => ouvrirLegal && ouvrirLegal('confidentialite')}>
              {t('c_lien_documents')}
            </button>
          </p>
        </div>
      </div>
    )
  }

  async function creer(e) {
    e.preventDefault(); setErr(null)
    try {
      await ajouterEnfant({ ...nouveau, pays: utilisateur.pays })
      setNouveau({ prenom: '', sexe: 'm', date_naissance: '' })
    } catch (e2) { setErr(String(e2)) }
  }

  return (
    <div className="page">
      <div className="bloc">
        <h2>{t('c_mon_compte')}</h2>
        <p className="legende-txt">{utilisateur.identifiant} · {t('c_inscrit_le')} {utilisateur.cree_le?.slice(0, 10)}</p>
        <div className="grille g3">
          <label className="champ">
            {t('c_nom_label')}
            <input defaultValue={utilisateur.nom || ''} onBlur={(e) => majProfil({ nom: e.target.value })} />
          </label>
          <label className="champ">
            {t('pays')}
            <select value={utilisateur.pays} onChange={(e) => majProfil({ pays: e.target.value })}>
              {listePays.map((p) => <option key={p.code} value={p.code}>{p.drapeau} {p.nom}</option>)}
            </select>
          </label>
          <label className="champ">
            {t('langue')}
            <select value={utilisateur.langue} onChange={(e) => majProfil({ langue: e.target.value })}>
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </label>
        </div>
        <button className="bouton sec" onClick={deconnecter}>{t('deconnexion')}</button>
      </div>

      <div className="bloc">
        <h3>{t('c_mes_enfants')} ({enfants.length})</h3>
        <p className="legende-txt">
          {t('c_mes_enfants_p')}
        </p>
        {enfants.map((e) => {
          const ageJours = Math.floor((Date.now() - new Date(e.date_naissance)) / 86400000)
          return (
            <div key={e.id} className="resultat" style={{ cursor: 'default' }}>
              <div className="rond" style={{ background: e.sexe === 'm' ? 'var(--bleu)' : '#c04ac0' }}>
                {e.sexe === 'm' ? '👦' : '👧'}
              </div>
              <div style={{ flex: 1 }}>
                <div className="nom">{e.prenom}</div>
                <div className="meta">
                  <span>{t('c_ne_le')} {new Date(e.date_naissance).toLocaleDateString(langue === 'en' ? 'en-GB' : 'fr-FR')}</span>
                  <span>{(ageJours / 30.4375).toFixed(1)} {t('acc_mois')}</span>
                  <span>{e.vaccins_faits.length} {t('c_doses_cochees')}</span>
                </div>
              </div>
              <button className="bouton sec petit" onClick={() => confirm(`${t('c_supprimer')} ${e.prenom} ${t('c_supp_apres')}`) && supprimerEnfant(e.id)}>
                {t('c_supprimer')}
              </button>
            </div>
          )
        })}

        <form onSubmit={creer} className="grille g3" style={{ marginTop: 16, alignItems: 'end' }}>
          <label className="champ">
            {t('c_prenom')}
            <input required value={nouveau.prenom} placeholder="Ex. Amina"
                   onChange={(e) => setNouveau({ ...nouveau, prenom: e.target.value })} />
          </label>
          <label className="champ">
            {t('n_sexe')}
            <select value={nouveau.sexe} onChange={(e) => setNouveau({ ...nouveau, sexe: e.target.value })}>
              <option value="m">{t('n_garcon')}</option><option value="f">{t('n_fille')}</option>
            </select>
          </label>
          <label className="champ">
            {t('c_date_nais')}
            <input required type="date" value={nouveau.date_naissance} max={new Date().toISOString().slice(0, 10)}
                   onChange={(e) => setNouveau({ ...nouveau, date_naissance: e.target.value })} />
          </label>
          <button className="bouton" style={{ marginBottom: 14 }}>{t('c_ajouter')}</button>
        </form>
        {err && <div className="alerte rouge" role="alert"><p>{err}</p></div>}
      </div>

      <MesDroits ouvrirLegal={ouvrirLegal} />
    </div>
  )
}
