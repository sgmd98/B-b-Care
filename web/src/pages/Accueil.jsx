import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { useLangue } from '../i18n'

export default function Accueil({ pays, listePays, aller, ouvrirAuth }) {
  const [stats, setStats] = useState(null)
  const [detail, setDetail] = useState(null)
  const { connecte, utilisateur } = useAuth()
  const { t, langue } = useLangue()

  useEffect(() => { api.stats().then(setStats).catch(() => {}) }, [])
  useEffect(() => { if (pays) api.detailPays(pays).then(setDetail).catch(() => {}) }, [pays])

  const p = listePays.find((x) => x.code === pays)
  const cov = detail?.couverture_oms || {}
  const nb = (n) => (n == null ? '-' : n.toLocaleString(langue === 'en' ? 'en-GB' : 'fr-FR'))

  const OUTILS = [
    ['carte', '🗺️', t('o_carte_t'), t('o_carte_p'), t('o_carte_g')],
    ['assistant', '🤖', t('o_assistant_t'), t('o_assistant_p'), t('o_assistant_g')],
    ['nutrition', '⚖️', t('o_nutrition_t'), t('o_nutrition_p'), t('o_nutrition_g')],
    ['vaccins', '💉', t('o_vaccins_t'),
     `${t('o_vaccins_p1')} ${p ? p.nom : t('o_vaccins_p2')}, ${t('o_vaccins_p3')}`,
     t('o_vaccins_g')],
    ['donnees', '📊', t('o_donnees_t'), t('o_donnees_p'), t('o_donnees_g')],
    ['assistant', '🩺', t('o_triage_t'), t('o_triage_p'), t('o_triage_g')],
  ]

  return (
    <>
      {/* ------------------------------------------------------------- HERO */}
      <section className="hero" style={{ padding: 0 }}>
        <div className="container hero-inner">
          <div>
            <span className="eyebrow">{t('acc_eyebrow')}</span>
            <h1>{t('acc_h1a')}<br /><span className="grad">{t('acc_h1b')}</span> {t('acc_h1c')}</h1>
            <p className="lead">{t('acc_lead')}</p>
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={() => aller('carte')}>
                {t('acc_cta1')}
              </button>
              <button className="btn btn-ghost" onClick={() => aller('assistant')}>
                {t('acc_cta2')}
              </button>
            </div>
            <div className="hero-proof">
              <div><b>{stats ? nb(stats.structures_total) : '23 568'}</b> {t('acc_preuve1')}</div>
              <div><b>{stats ? stats.pays : 15}</b> {t('acc_preuve2')}</div>
              <div><b>100%</b> {t('acc_preuve3')}</div>
            </div>
          </div>

          <div className="hero-visual">
            <div className="phone">
              <div className="screen">
                <div className="screen-top">
                  <div className="dot"><span /><span /><span /></div>
                  <span className="chip">{t('acc_suivi')}</span>
                </div>
                <h4>{t('acc_bilan')}</h4>
                <div className="metric-row">
                  <div className="metric"><div className="k">{t('acc_poids')}</div><div className="v">11,4 kg</div></div>
                  <div className="metric"><div className="k">{t('acc_taille')}</div><div className="v">82 cm</div></div>
                  <div className="metric"><div className="k">{t('acc_pb')}</div><div className="v">14,2 cm</div></div>
                  <div className="metric"><div className="k">{t('acc_age')}</div><div className="v">18 {t('acc_mois')}</div></div>
                </div>
                <div className="gauge"><i /></div>
                <div className="status-pill"><span className="ic">✓</span> {t('acc_etat_ok')}</div>
                <div className="row-item">{t('acc_rdv')} <b>3 sept.</b></div>
                <div className="row-item">{t('acc_conseil')} <b>{t('acc_voir')}</b></div>
              </div>
              <div className="float-card fc1">{t('acc_flot1')}</div>
              <div className="float-card fc2">{t('acc_flot2')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------- SANS COMPTE */}
      <section style={{ padding: '10px 0 0' }}>
        <div className="container">
          <div className="disclaimer" style={{
            background: 'var(--teal-50)', borderColor: 'var(--teal-100)', color: 'var(--teal-800)',
            maxWidth: 'none',
          }}>
            <span className="emoji">🔓</span>
            <div>
              {connecte ? (
                <>
                  <strong>{t('acc_bonjour')} {utilisateur?.nom || ''}</strong> {t('acc_enregistres')}
                  {' '}<a onClick={() => aller('compte')} style={{ color: 'var(--teal-600)', fontWeight: 700, cursor: 'pointer' }}>{t('mon_espace')}</a>.
                </>
              ) : (
                <>
                  <strong>{t('acc_sans_compte_t')}</strong> {t('acc_sans_compte')}
                  {' '}<a onClick={ouvrirAuth} style={{ color: 'var(--teal-600)', fontWeight: 700, cursor: 'pointer' }}>{t('acc_creer')}</a>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------- OUTILS */}
      <section id="outils" style={{ paddingTop: 40 }}>
        <div className="container">
          <div className="sec-head">
            <span className="eyebrow">{t('acc_nos_outils')}</span>
            <h2>{t('acc_outils_h')}</h2>
            <p>{t('acc_outils_p')}</p>
          </div>
          <div className="tools">
            {OUTILS.map(([cle, ico, titre, texte, tag]) => (
              <a key={cle} className="tool" href="#" onClick={(e) => { e.preventDefault(); aller(cle) }}>
                <div className="ico">{ico}</div>
                <h3>{titre}</h3>
                <p>{texte}</p>
                <span className="tag">{tag}</span>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ COMMENT ÇA MARCHE */}
      <section style={{ background: 'var(--teal-50)' }}>
        <div className="container">
          <div className="sec-head">
            <span className="eyebrow">{t('acc_simple')}</span>
            <h2>{t('acc_comment_h')}</h2>
            <p>{t('acc_comment_p')}</p>
          </div>
          <div className="steps">
            <div className="step">
              <div className="num">1</div><h3>{t('acc_e1t')}</h3>
              <p>{t('acc_e1p')}</p>
            </div>
            <div className="step">
              <div className="num">2</div><h3>{t('acc_e2t')}</h3>
              <p>{t('acc_e2p')}</p>
            </div>
            <div className="step">
              <div className="num">3</div><h3>{t('acc_e3t')}</h3>
              <p>{t('acc_e3p')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------ CHIFFRES OMS */}
      {p && (
        <section>
          <div className="container">
            <div className="sec-head">
              <span className="eyebrow">{t('acc_urgent')}</span>
              <h2>{p.drapeau} {p.nom} : {t('acc_chiffres')}</h2>
              <p>{t('acc_chiffres_p')}</p>
            </div>
            <div className="grid3">
              {[
                ['BCG', 'BCG'], ['Pentavalent 3', 'DTP3'], ['Rougeole 1re dose', 'MCV1'],
                ['Rougeole 2e dose', 'MCV2'], ['Pneumocoque 3', 'PCV3'], ['Fièvre jaune', 'YFV'],
              ].map(([lib, k]) => {
                const v = cov[k]?.valeur
                return (
                <div key={lib} className="panel" style={{ margin: 0, textAlign: 'center' }}>
                  <div style={{
                    fontSize: '2.1rem', fontWeight: 800, letterSpacing: '-.02em',
                    color: v == null ? 'var(--muted)' : v < 60 ? 'var(--danger)' : v < 85 ? 'var(--amber-dark)' : 'var(--teal-700)',
                  }}>
                    {v == null ? '-' : `${v} %`}
                  </div>
                  <div style={{ color: 'var(--muted)', fontSize: '.9rem', fontWeight: 600 }}>{lib}</div>
                  {cov[k]?.annee && (
                    <div style={{ color: 'var(--muted)', fontSize: '.74rem', marginTop: 4, opacity: .75 }}>
                      OMS {cov[k].annee}
                    </div>
                  )}
                </div>
              )})}
            </div>
            <div style={{ textAlign: 'center', marginTop: 28 }}>
              <button className="btn btn-ghost" onClick={() => aller('donnees')}>
                {t('acc_voir_donnees')}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* --------------------------------------------------------- QUI SUIS-JE */}
      <section className="about" style={{ padding: '64px 0' }}>
        <div className="container about-inner">
          <div className="portrait"><img src="/photo-darius.jpg" alt="SOSSA G. M. Darius" /></div>
          <div>
            <h2>{t('acc_qui')}</h2>
            <p>
              {t('acc_bio1a')} <strong>SOSSA Gninazé Mingnissê Darius</strong>{t('acc_bio1b')}
            </p>
            <p>{t('acc_bio2')}</p>
            <div className="skills">
              <span className="skill">{t('acc_sk1')}</span>
              <span className="skill">{t('acc_sk2')}</span>
              <span className="skill">{t('acc_sk3')}</span>
              <span className="skill">{t('acc_sk4')}</span>
            </div>
            <button className="btn btn-light" onClick={() => aller('apropos')}>{t('acc_savoir')}</button>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------- DISCLAIMER */}
      <section style={{ padding: '44px 0' }}>
        <div className="container">
          <div className="disclaimer">
            <span className="emoji">⚠️</span>
            <div>
              <strong>{t('acc_info_med')}</strong> {t('acc_info_txt')}{' '}
              <strong>{p?.urgence || '112'}</strong> {t('acc_info_fin')}
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
