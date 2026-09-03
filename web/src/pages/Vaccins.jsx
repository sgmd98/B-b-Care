import { useEffect, useState } from 'react'
import { api } from '../api'
import { useLangue } from '../i18n'

const CLE = 'bebecare.enfant'

export default function Vaccins({ pays, listePays }) {
  const { t, langue } = useLangue()
  const [enfant, setEnfant] = useState(() => {
    try { return JSON.parse(localStorage.getItem(CLE)) || {} } catch { return {} }
  })
  const [planning, setPlanning] = useState(null)
  const [erreur, setErreur] = useState(null)

  const dn = enfant.date_naissance || ''
  const faits = enfant.faits || []
  const locale = langue === 'en' ? 'en-GB' : 'fr-FR'

  useEffect(() => { localStorage.setItem(CLE, JSON.stringify(enfant)) }, [enfant])

  useEffect(() => {
    if (!dn || !pays) { setPlanning(null); return }
    api.planning({ date_naissance: dn, pays, deja_faits: faits })
      .then(setPlanning).catch((e) => setErreur(String(e)))
  }, [dn, pays, JSON.stringify(faits)]) // eslint-disable-line

  function basculer(cle) {
    setEnfant((e) => {
      const f = new Set(e.faits || [])
      f.has(cle) ? f.delete(cle) : f.add(cle)
      return { ...e, faits: [...f] }
    })
  }

  const infosPays = listePays.find((p) => p.code === pays)

  const ETATS = {
    fait: t('v_e_fait'), retard: t('v_e_retard'),
    bientot: t('v_e_bientot'), futur: t('v_e_futur'),
  }

  return (
    <div className="page">
      <div className="bloc">
        <h2>{t('t_vaccins')}</h2>
        <p className="legende-txt">
          {t('v_calendrier_texte')}{' '}
          {infosPays?.drapeau} {infosPays?.nom}{t('v_calendrier_suite')}
        </p>
        <div className="grille g2">
          <label className="champ">
            {t('v_prenom')}
            <input value={enfant.prenom || ''} placeholder="Ex. Amina"
                   onChange={(e) => setEnfant({ ...enfant, prenom: e.target.value })} />
          </label>
          <label className="champ">
            {t('c_date_nais')}
            <input type="date" value={dn} max={new Date().toISOString().slice(0, 10)}
                   onChange={(e) => setEnfant({ ...enfant, date_naissance: e.target.value })} />
          </label>
        </div>
        {dn && (
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4, alignItems: 'center' }}>
            <a className="bouton" style={{ textDecoration: 'none' }}
               href={api.urlPdfVaccins(pays, dn, enfant.prenom, faits, langue)}>
              {t('v_pdf')}
            </a>
            <a className="bouton sec petit" style={{ textDecoration: 'none' }}
               href={api.urlIcs(pays, dn)}>
              {t('v_ics')}
            </a>
            <button type="button" className="bouton sec petit"
                    title={t('v_reset_ok')}
                    onClick={() => { if (window.confirm(t('v_reset_ok'))) setEnfant({}) }}>
              {t('v_reset')}
            </button>
          </div>
        )}
      </div>

      {erreur && <div className="alerte rouge"><h4>{t('erreur')}</h4><p>{erreur}</p></div>}

      {planning && (
        <>
          <div className="grille g4" style={{ marginBottom: 16 }}>
            <div className="stat">
              <div className="etiquette">{t('v_age')}</div>
              <div className="valeur">{planning.age_mois}</div>
              <div className="detail">{t('acc_mois')}</div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('v_doses')}</div>
              <div className="valeur" style={{ color: 'var(--vert)' }}>
                {planning.resume.faits}/{planning.resume.total}
              </div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('v_retard')}</div>
              <div className="valeur" style={{ color: planning.resume.en_retard ? 'var(--rouge)' : 'var(--vert)' }}>
                {planning.resume.en_retard}
              </div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('v_dans_mois')}</div>
              <div className="valeur" style={{ color: 'var(--orange)' }}>
                {planning.resume.dans_le_mois}
              </div>
            </div>
          </div>

          <div className={`alerte ${planning.resume.en_retard ? 'orange' : 'vert'}`}>
            <h4>{planning.resume.en_retard ? t('v_rattrapage') : t('v_a_jour')}</h4>
            <p>{planning.message}</p>
          </div>

          <div className="bloc">
            <h3>{t('v_detaille')}</h3>
            <p className="legende-txt">{t('v_cochez')}</p>
                        <div className="table-scroll">
<table className="t">
              <thead>
                <tr>
                  <th style={{ width: 40 }}>{t('v_fait_col')}</th>
                  <th>{t('v_vaccin')}</th>
                  <th>{t('v_age_prevu')}</th>
                  <th>{t('v_date')}</th>
                  <th>{t('v_statut')}</th>
                </tr>
              </thead>
              <tbody>
                {planning.etapes.map((e) => (
                  <tr key={e.cle + e.date_prevue}>
                    <td>
                      <input type="checkbox" checked={e.etat === 'fait'}
                             onChange={() => basculer(e.cle)}
                             style={{ width: 18, height: 18 }} />
                    </td>
                    <td>
                      <b>{e.vaccin}</b>
                      {e.dose > 1 && <span style={{ color: 'var(--gris)' }}> : dose {e.dose}</span>}
                    </td>
                    <td>{e.age}</td>
                    <td>{new Date(e.date_prevue).toLocaleDateString(locale)}</td>
                    <td>
                      <span className={`badge ${e.etat}`}>
                        {ETATS[e.etat]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
            <div className="note">
              Source : {planning.source}. {t('v_note_pev')}
            </div>
          </div>
        </>
      )}

      {!dn && (
        <div className="alerte info">
          <h4>{t('v_commencez')}</h4>
          <p>{t('v_commencez_p')}</p>
        </div>
      )}
    </div>
  )
}
