import { useEffect, useState } from 'react'
import { api } from '../api'
import { useLangue } from '../i18n'

export default function Triage({ pays, listePays, embarque = false }) {
  const { t } = useLangue()
  const [cat, setCat] = useState(null)
  const [f, setF] = useState({ age_mois: '', temp_c: '', freq_resp: '', allaite: null })
  const [signes, setSignes] = useState([])
  const [res, setRes] = useState(null)
  const [occupe, setOccupe] = useState(false)

  useEffect(() => { api.catalogueTriage().then(setCat) }, [])

  const infosPays = listePays.find((p) => p.code === pays)

  function basculer(code) {
    setSignes((s) => s.includes(code) ? s.filter((x) => x !== code) : [...s, code])
  }

  async function evaluer(e) {
    e.preventDefault()
    setOccupe(true)
    const corps = { age_mois: parseFloat(f.age_mois || 0), signes, pays }
    if (f.temp_c) corps.temp_c = parseFloat(f.temp_c)
    if (f.freq_resp) corps.freq_resp = parseInt(f.freq_resp, 10)
    if (f.allaite !== null) corps.allaite = f.allaite
    try { setRes(await api.triage(corps)) } catch (e2) { alert(String(e2)) }
    setOccupe(false)
  }

  return (
    <div className={embarque ? '' : 'page'}>
      <div className={embarque ? '' : 'bloc'}>
        {!embarque && (
          <>
            <h2>{t('t_triage')}</h2>
            <p className="legende-txt">{t('tr_intro')}</p>
          </>
        )}
        <form onSubmit={evaluer} noValidate>
          <div className="grille g4">
            <label className="champ">
              {t('n_age')} *
              <input type="number" step="any" min="0" max="60" required value={f.age_mois}
                     onChange={(e) => setF({ ...f, age_mois: e.target.value })} />
            </label>
            <label className="champ">
              {t('tr_temp')}
              <input type="number" step="any" placeholder="38.5" value={f.temp_c}
                     onChange={(e) => setF({ ...f, temp_c: e.target.value })} />
            </label>
            <label className="champ">
              {t('tr_resp')}
              <input type="number" step="any" placeholder={t('tr_resp_ph')} value={f.freq_resp}
                     onChange={(e) => setF({ ...f, freq_resp: e.target.value })} />
            </label>
            <label className="champ">
              {t('tr_allaite')}
              <select value={f.allaite === null ? '' : String(f.allaite)}
                      onChange={(e) => setF({ ...f, allaite: e.target.value === '' ? null : e.target.value === 'true' })}>
                <option value="">{t('tr_non_precise')}</option>
                <option value="true">{t('a_oui')}</option>
                <option value="false">{t('a_non')}</option>
              </select>
            </label>
          </div>

          {cat && (
            <>
              <div className="groupe">
                <h4 style={{ color: 'var(--rouge)' }}>{t('tr_danger_h')}</h4>
                <div className="puces">
                  {cat.danger.map((s) => (
                    <button type="button" key={s.code}
                            className={`puce danger ${signes.includes(s.code) ? 'active' : ''}`}
                            onClick={() => basculer(s.code)}>{s.libelle}</button>
                  ))}
                </div>
              </div>
              <div className="groupe">
                <h4>{t('tr_autres')}</h4>
                <div className="puces">
                  {cat.symptomes.map((s) => (
                    <button type="button" key={s.code}
                            className={`puce ${signes.includes(s.code) ? 'active' : ''}`}
                            onClick={() => basculer(s.code)}>{s.libelle}</button>
                  ))}
                </div>
              </div>
            </>
          )}

          <button className="bouton" disabled={occupe}>
            {occupe ? t('tr_analyse') : t('tr_evaluer')}
          </button>
        </form>
      </div>

      {res && (
        <>
          <div className={`alerte ${res.niveau}`} style={{ padding: '18px 20px' }}>
            <h4 style={{ fontSize: 19 }}>
              {res.niveau === 'rouge' ? '🚨 ' : res.niveau === 'orange' ? '⚠️ ' : '✅ '}{res.titre}
            </h4>
            {res.niveau === 'rouge' && infosPays && (
              <p style={{ marginTop: 8 }}>
                <a className="bouton rouge" style={{ textDecoration: 'none', display: 'inline-block', color: '#fff' }}
                   href={`tel:${infosPays.urgence}`}>
                  📞 {t('urgence')} {infosPays.nom} : {infosPays.urgence}
                </a>
              </p>
            )}
          </div>

          <div className="grille g2">
            <div className="bloc">
              <h3>{t('tr_pourquoi')}</h3>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13.5, lineHeight: 1.75 }}>
                {res.raisons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
              <h3 style={{ marginTop: 16 }}>{t('tr_regles')}</h3>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12.5, lineHeight: 1.7, color: 'var(--gris)' }}>
                {res.regles_appliquees.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>

            <div className="bloc">
              <h3>{t('tr_faire')}</h3>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13.5, lineHeight: 1.75 }}>
                {res.conseils.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
              <h3 style={{ marginTop: 16 }}>{t('tr_revenir')}</h3>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13.5, lineHeight: 1.75, color: 'var(--rouge)' }}>
                {res.signes_retour.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          </div>

          <div className="note">{res.source}. {res.avertissement}</div>
        </>
      )}
    </div>
  )
}
