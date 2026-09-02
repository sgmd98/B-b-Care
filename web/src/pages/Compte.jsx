import { useState } from 'react'
import { useAuth } from '../auth'
import { useLangue } from '../i18n'
import { Logo } from '../Logo'

export function ModaleAuth({ listePays, paysDefaut, langueDefaut, fermer }) {
  const { inscrire, connecter } = useAuth()
  const { t } = useLangue()
  const [mode, setMode] = useState('inscription')
  const [f, setF] = useState({
    identifiant: '', mot_de_passe: '', nom: '',
    pays: paysDefaut || 'bj', langue: langueDefaut || 'fr', role: 'parent',
  })
  const [err, setErr] = useState(null)
  const [occupe, setOccupe] = useState(false)

  async function soumettre(e) {
    e.preventDefault(); setErr(null); setOccupe(true)
    try {
      if (mode === 'inscription') await inscrire(f)
      else await connecter(f.identifiant, f.mot_de_passe)
      fermer()
    } catch (e2) {
      const m = String(e2).match(/\{"detail":"(.*?)"\}/)
      setErr(m ? m[1] : String(e2))
    }
    setOccupe(false)
  }

  return (
    <div className="voile-modale" onClick={(e) => e.target === e.currentTarget && fermer()}>
      <div className="modale">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
          <Logo taille={42} />
          <div>
            <h2 style={{ margin: 0 }}>{mode === 'inscription' ? t('creer_compte') : t('c_connecter_titre')}</h2>
            <p style={{ margin: '3px 0 0', fontSize: 13, color: 'var(--gris)' }}>
              {t('c_gratuit')}
            </p>
          </div>
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

export default function Compte({ listePays, ouvrirAuth }) {
  const { connecte, utilisateur, enfants, deconnecter, majProfil, ajouterEnfant, supprimerEnfant } = useAuth()
  const { t, langue } = useLangue()
  const [nouveau, setNouveau] = useState({ prenom: '', sexe: 'm', date_naissance: '' })
  const [err, setErr] = useState(null)

  if (!connecte) {
    return (
      <div className="page">
        <div className="bloc" style={{ textAlign: 'center', padding: 44 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}><Logo taille={60} /></div>
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
        {err && <div className="alerte rouge"><p>{err}</p></div>}
      </div>
    </div>
  )
}
