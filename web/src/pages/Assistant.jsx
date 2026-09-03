import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useLangue } from '../i18n'
import Triage from './Triage'

const EX_TRIAGE = ['ex_t1', 'ex_t2', 'ex_t3', 'ex_t4']
const EX_QUESTION = ['ex_q1', 'ex_q2', 'ex_q3', 'ex_q4']

// Chaque mode a SA propre conversation : fini l'interface partagee
// entre le triage et les questions libres.
const ACCUEIL_TRIAGE = [{ role: 'ia', texte: null, cle: 'a_bonjour' }]
const ACCUEIL_QUESTION = [{ role: 'ia', texte: null, cle: 'q_bonjour' }]

const MODES = ['triage', 'guide', 'question']

export default function Assistant({ pays, listePays }) {
  const { t } = useLangue()
  const [mode, setMode] = useState('triage')
  const [filTriage, setFilTriage] = useState(ACCUEIL_TRIAGE)
  const [filQuestion, setFilQuestion] = useState(ACCUEIL_QUESTION)
  const [saisie, setSaisie] = useState('')
  const [analyse, setAnalyse] = useState(null)
  const [contexte, setContexte] = useState({ age_mois: null, signes: [], posees: [] })
  const [occupe, setOccupe] = useState(false)
  const finRef = useRef(null)

  // Fil actif et son mutateur : une seule logique, deux conversations distinctes.
  const messages = mode === 'question' ? filQuestion : filTriage
  const setMessages = mode === 'question' ? setFilQuestion : setFilTriage

  useEffect(() => { finRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const infosPays = listePays.find((p) => p.code === pays)

  async function envoyer(texte) {
    const txt = (texte ?? saisie).trim()
    if (!txt || occupe) return
    setSaisie('')
    setMessages((m) => [...m, { role: 'moi', texte: txt }])
    setOccupe(true)

    if (mode === 'question') {
      try {
        const r = await api.assistantQuestion({
          question: txt, pays, age_mois: contexte.age_mois,
          historique: messages.filter((m) => m.texte)
            .map((m) => ({ role: m.role === 'moi' ? 'user' : 'ia', texte: m.texte })),
        })
        const suite = []
        if (r.alerte) suite.push({ role: 'ia', alerte: r.alerte })
        suite.push({ role: 'ia', texte: r.reponse, indispo: !r.disponible })
        setMessages((m) => [...m, ...suite])
      } catch (e) {
        setMessages((m) => [...m, { role: 'ia', texte: `${t('as_erreur')} : ${e.message || e}` }])
      }
      setOccupe(false)
      return
    }

    try {
      const r = await api.assistant({
        texte: txt, age_mois: contexte.age_mois, signes_confirmes: contexte.signes,
        deja_posees: contexte.posees, pays,
      })
      setAnalyse(r)
      const c = r.comprehension
      setContexte((ctx) => ({
        age_mois: c.age_mois ?? ctx.age_mois,
        signes: [...new Set([...ctx.signes, ...c.signes_detectes.map((s) => s.code)])],
        posees: ctx.posees,
      }))

      const nouveaux = []
      if (c.signes_detectes.length) {
        nouveaux.push({
          role: 'ia',
          texte: `${t('a_releve')} ${c.signes_detectes.length} ${t('a_elements')} `
            + c.signes_detectes.map((s) => s.libelle.toLowerCase()).join(', ') + '.',
        })
      }
      if (r.decision) {
        nouveaux.push({ role: 'ia', decision: r.decision })
      }
      if (r.questions.length) {
        nouveaux.push({ role: 'ia', question: r.questions[0] })
      }
      if (!nouveaux.length) {
        nouveaux.push({
          role: 'ia',
          texte: t('a_pas_compris'),
        })
      }
      setMessages((m) => [...m, ...nouveaux])
    } catch (e) {
      setMessages((m) => [...m, { role: 'ia', texte: `${t('as_erreur')} : ${e}` }])
    }
    setOccupe(false)
  }

  function repondreQuestion(q, valeur) {
    setContexte((c) => ({ ...c, posees: [...c.posees, q.cle] }))
    if (q.type === 'nombre') envoyer(`${q.champ === 'age_mois' ? valeur + ' mois' : 'température ' + valeur}`)
    else if (valeur === 'oui') {
      setContexte((c) => ({ ...c, signes: [...c.signes, q.champ], posees: [...c.posees, q.cle] }))
      envoyer('oui')
    } else envoyer('non')
  }

  return (
    <div className="page">
      <div className="bloc">
        <h2>{t('t_assistant')}</h2>
        <p className="legende-txt" style={{ marginBottom: 12 }}>
          <b>{t('a_garantie')}</b>
        </p>

        <div className="onglets onglets-modules" role="tablist">
          {MODES.map((m) => (
            <button key={m} type="button" role="tab" aria-selected={mode === m}
                    className={mode === m ? 'onglet actif' : 'onglet'}
                    onClick={() => setMode(m)}>
              {t(`mode_${m}`)}
            </button>
          ))}
        </div>

        <p className="aide-mode">
          {mode === 'triage' ? t('aide_triage') : mode === 'guide' ? t('aide_guide') : t('aide_question')}
        </p>

        <details className="depliable" style={{ marginBottom: 14 }}>
          <summary>{t('a_comment')}</summary>
          <div className="corps" style={{ paddingTop: 2 }}>
            <p className="legende-txt" style={{ margin: 0 }}>{t('a_intro')}</p>
          </div>
        </details>

        {mode === 'guide' && <Triage pays={pays} listePays={listePays} embarque />}

        {mode !== 'guide' && (<>
        <div className="chat" style={{ minHeight: 240 }}>
          {messages.map((m, i) => {
            if (m.decision) {
              const d = m.decision
              return (
                <div key={i} className={`alerte ${d.niveau}`} style={{ maxWidth: '92%', marginBottom: 0 }}>
                  <h4>{d.niveau === 'rouge' ? '🚨 ' : d.niveau === 'orange' ? '⚠️ ' : '✅ '}{d.titre}</h4>
                  <p><b>{t('pourquoi')} :</b> {d.raisons.join(' · ')}</p>
                  <ul style={{ margin: '9px 0 0', paddingLeft: 18, fontSize: 13.2, lineHeight: 1.65 }}>
                    {d.conseils.map((c, j) => <li key={j}>{c}</li>)}
                  </ul>
                  {d.niveau === 'rouge' && infosPays && (
                    <a className="bouton rouge petit" style={{ marginTop: 11 }} href={`tel:${infosPays.urgence}`}>
                      📞 {t('urgence')} {infosPays.nom} : {infosPays.urgence}
                    </a>
                  )}
                </div>
              )
            }
            if (m.question) {
              const q = m.question
              return (
                <div key={i} className="bulle ia" style={{ maxWidth: '92%' }}>
                  <b>{q.question}</b>
                  <div style={{ fontSize: 12, color: 'var(--gris)', margin: '6px 0 10px' }}>{q.pourquoi}</div>
                  {q.type === 'oui_non' ? (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button className="bouton petit sec" onClick={() => repondreQuestion(q, 'oui')}>{t('a_oui')}</button>
                      <button className="bouton petit sec" onClick={() => repondreQuestion(q, 'non')}>{t('a_non')}</button>
                    </div>
                  ) : (
                    <form style={{ display: 'flex', gap: 8, alignItems: 'center' }}
                          onSubmit={(e) => {
                            e.preventDefault()
                            const v = e.target.elements.champReponse?.value
                            if (v) repondreQuestion(q, v)
                          }}>
                      <input type="number" step="any" name="champReponse" className="champ-compact" style={{ width: 110 }}
                             placeholder={q.champ === 'age_mois' ? 'mois' : '°C'} />
                      <button type="submit" className="bouton petit">OK</button>
                    </form>
                  )}
                </div>
              )
            }
            if (m.alerte) {
              return (
                <div key={i} className="alerte rouge" style={{ maxWidth: '92%', marginBottom: 0 }}>
                  <h4>🚨 {m.alerte.titre}</h4>
                  <p>{m.alerte.message}</p>
                  {m.alerte.raisons?.length > 0 && (
                    <p style={{ marginTop: 6 }}><b>{t('a_releve_alerte')}</b> {m.alerte.raisons.join(' · ')}</p>
                  )}
                  <button className="bouton rouge petit" style={{ marginTop: 10 }}
                          onClick={() => setMode('triage')}>
                    {t('passer_triage')}
                  </button>
                </div>
              )
            }
            if (m.indispo) {
              return (
                <div key={i} className="alerte info" style={{ maxWidth: '92%', marginBottom: 0 }}>
                  <h4>{t('conv_indispo')}</h4>
                  <p>{m.texte}</p>
                </div>
              )
            }
            return <div key={i} className={`bulle ${m.role === 'moi' ? 'moi' : 'ia'}`}>{m.cle ? t(m.cle) : m.texte}</div>
          })}
          {occupe && <div className="bulle ia">…</div>}
          <div ref={finRef} />
        </div>

        <div className="chat-saisie">
          <textarea value={saisie} onChange={(e) => setSaisie(e.target.value)}
                    placeholder={mode === 'triage' ? t('a_ph_triage') : t('a_ph_question')}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); envoyer() } }} />
          <button className="bouton" onClick={() => envoyer()} disabled={occupe}>{t('envoyer')}</button>
        </div>

        {messages.length <= 1 && mode !== 'guide' && (
          <div style={{ marginTop: 14 }}>
            <h4>{t('as_essayez')}</h4>
            <div className="puces">
              {(mode === 'triage' ? EX_TRIAGE : EX_QUESTION).map((k) => t(k)).map((e) => (
                <button key={e} className="puce" onClick={() => envoyer(e)}>{e}</button>
              ))}
            </div>
          </div>
        )}
        </>)}
      </div>

      {analyse && mode !== 'guide' && (
        <details className="depliable">
          <summary>{t('a_details')}</summary>
          <div className="corps">
          <p className="legende-txt">{t('as_compris_p')}</p>
          <div className="grille g4" style={{ marginBottom: 14 }}>
            <div className="stat">
              <div className="etiquette">{t('as_age')}</div>
              <div className="valeur" style={{ fontSize: 21 }}>
                {analyse.comprehension.age_mois != null ? `${analyse.comprehension.age_mois} ${t('acc_mois')}` : '-'}
              </div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('as_temp')}</div>
              <div className="valeur" style={{ fontSize: 21 }}>
                {analyse.comprehension.temperature_c ?? '-'}{analyse.comprehension.temperature_c ? ' °C' : ''}
              </div>
              {analyse.comprehension.temperature_estimee &&
                <div className="detail">{t('as_temp_est')}</div>}
            </div>
            <div className="stat">
              <div className="etiquette">{t('as_resp')}</div>
              <div className="valeur" style={{ fontSize: 21 }}>
                {analyse.comprehension.frequence_respiratoire ?? '-'}
              </div>
              <div className="detail">/min</div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('as_duree')}</div>
              <div className="valeur" style={{ fontSize: 21 }}>
                {analyse.comprehension.duree_jours ?? '-'}
              </div>
              <div className="detail">{t('as_jours')}</div>
            </div>
          </div>

          <h4>{t('as_signes')}</h4>
          <div style={{ marginBottom: 12 }}>
            {analyse.comprehension.signes_detectes.length === 0 && (
              <span style={{ fontSize: 13, color: 'var(--gris)' }}>{t('as_aucun')}</span>
            )}
            {analyse.comprehension.signes_detectes.map((s) => (
              <span key={s.code} className={`jeton-signe ${s.danger ? 'danger' : ''}`}>
                {s.danger && '⚠️'} {s.libelle}
                <span className="conf">{Math.round(s.confiance * 100)} %</span>
              </span>
            ))}
          </div>

          {analyse.comprehension.signes_ecartes_par_negation.length > 0 && (
            <>
              <h4>{t('as_ecartes')}</h4>
              <div style={{ marginBottom: 12 }}>
                {analyse.comprehension.signes_ecartes_par_negation.map((c) => (
                  <span key={c} className="jeton-signe" style={{ opacity: .55, textDecoration: 'line-through' }}>{c}</span>
                ))}
              </div>
            </>
          )}

          <div className="note">{analyse.methode}<br /><br />{analyse.avertissement}</div>
          </div>
        </details>
      )}
    </div>
  )
}
