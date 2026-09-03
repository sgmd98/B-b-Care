import { useEffect, useState } from 'react'
import { api } from '../api'
import { useLangue } from '../i18n'

export default function APropos() {
  const { t, langue } = useLangue()
  const [s, setS] = useState(null)
  const [stats, setStats] = useState(null)
  useEffect(() => {
    api.sources().then(setS).catch(() => {})
    api.stats().then(setStats).catch(() => {})
  }, [])

  const nombre = (n) => n.toLocaleString(langue === 'en' ? 'en-GB' : 'fr-FR')

  return (
    <div className="page">

      {/* ------------------------------------------------- LE FONDATEUR */}
      <div className="bloc" style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 26, alignItems: 'start' }}>
        <img src="/photo-darius.jpg" alt="SOSSA Gninazé Mingnissê Darius"
             style={{ width: 180, height: 210, objectFit: 'cover', objectPosition: '50% 22%',
                      borderRadius: 16, border: '1px solid var(--line)' }} />
        <div>
          <span className="eyebrow">{t('ap_fondateur')}</span>
          <h2 style={{ margin: '12px 0 4px' }}>SOSSA Gninazé Mingnissê Darius</h2>
          <p style={{ color: 'var(--muted)', fontWeight: 600, margin: '0 0 14px' }}>
            {t('ap_meta')}
          </p>
          <p className="legende-txt" style={{ fontSize: 14.5 }}>
            {t('ap_bio1')}
          </p>
          <p className="legende-txt" style={{ fontSize: 14.5 }}>
            {t('ap_bio2')}
          </p>
          <div className="skills" style={{ margin: '18px 0 0' }}>
            {[t('acc_sk1'), t('acc_sk2'), t('ap_sk_pub'), t('acc_sk3'),
              t('ap_sk_genie'), t('acc_sk4')]
              .map((k) => (
                <span key={k} className="skill"
                      style={{ background: 'var(--teal-50)', border: '1px solid var(--teal-100)', color: 'var(--teal-800)' }}>
                  {k}
                </span>
              ))}
          </div>
          <div style={{ marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <a className="btn btn-ghost btn-sm"
               href="https://www.linkedin.com/in/gninaz%C3%A9-mingniss%C3%AA-darius-sossa-743721376"
               target="_blank" rel="noopener noreferrer">LinkedIn</a>
            <a className="btn btn-ghost btn-sm" href="https://github.com/sosak98"
               target="_blank" rel="noopener noreferrer">GitHub</a>
            <a className="btn btn-ghost btn-sm" href="mailto:sante.infantile.benin@gmail.com">{t('ap_ecrire')}</a>
          </div>
        </div>
      </div>

      <div className="bloc">
        <h2>{t('ap_h2')}</h2>
        <p className="legende-txt" style={{ fontSize: 14.5 }}>
          {t('ap_intro')}
        </p>
      </div>

      {stats && (
        <div className="grille g4" style={{ marginBottom: 16 }}>
          <div className="stat">
            <div className="etiquette">{t('ap_pays')}</div>
            <div className="valeur">{stats.pays}</div>
            <div className="detail">CEDEAO</div>
          </div>
          <div className="stat">
            <div className="etiquette">{t('ap_struct')}</div>
            <div className="valeur">{nombre(stats.structures_total)}</div>
            <div className="detail">OpenStreetMap</div>
          </div>
          <div className="stat">
            <div className="etiquette">{t('ap_hop')}</div>
            <div className="valeur">
              {nombre((stats.par_categorie.hopital || 0) + (stats.par_categorie.centre_sante || 0))}
            </div>
          </div>
          <div className="stat">
            <div className="etiquette">Pharmacies</div>
            <div className="valeur">{nombre(stats.par_categorie.pharmacie || 0)}</div>
          </div>
        </div>
      )}

      <div className="bloc">
        <h3>{t('ap_sources_h')}</h3>
        <p className="legende-txt">
          {t('ap_sources_p')}
        </p>
        {s && (
                    <div className="table-scroll">
<table className="t">
            <thead><tr><th>Module</th><th>Source</th><th>Licence</th></tr></thead>
            <tbody>
              {Object.entries(s).map(([cle, v]) => (
                <tr key={cle}>
                  <td style={{ textTransform: 'capitalize' }}>{cle.replace(/_/g, ' ')}</td>
                  <td>
                    <b>{v.nom}</b>
                    {v.url && <> : <a href={v.url} target="_blank" rel="noreferrer">{t('ap_lien')}</a></>}
                    {v.note && <div style={{ fontSize: 12, color: 'var(--gris)' }}>{v.note}</div>}
                  </td>
                  <td style={{ fontSize: 12.5 }}>{v.licence || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>

      <div className="bloc">
        <h3>{t('ap_vp_h')}</h3>
        <ul style={{ fontSize: 13.5, lineHeight: 1.8, paddingLeft: 20, margin: 0 }}>
          <li>{t('ap_vp1')}</li>
          <li>{t('ap_vp2')}</li>
          <li>{t('ap_vp3')}</li>
          <li>{t('ap_vp4')}</li>
        </ul>
      </div>

      <div className="alerte info">
        <h4>{t('ap_av_h')}</h4>
        <p>
          {t('ap_av_p')}
        </p>
      </div>
    </div>
  )
}
