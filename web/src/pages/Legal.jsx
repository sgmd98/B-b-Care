import { useState } from 'react'
import { useLangue } from '../i18n'
import { DATE_POLITIQUE, EDITEUR, LEGAL, ONGLETS_LEGAUX, VERSION_POLITIQUE } from '../legal'

/* Page des documents légaux : politique de confidentialité, conditions
   d'utilisation et mentions légales. Trois onglets, une seule page, un lien
   direct par onglet (#confidentialite, #conditions, #mentions) pour que
   chaque document soit citable et partageable tel quel. */

export default function Legal({ ongletInitial = 'confidentialite' }) {
  const { langue } = useLangue()
  const L = LEGAL[langue] || LEGAL.fr
  const [actif, setActif] = useState(
    ONGLETS_LEGAUX.includes(ongletInitial) ? ongletInitial : 'confidentialite')

  const doc = L[actif]

  function ouvrir(cle) {
    setActif(cle)
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', `#${cle}`)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <div className="page">
      <div className="bloc legal-bloc">
        <div className="legal-entete">
          <span className="eyebrow">⚖️ {L.mentions.titre} · {L.onglet_confidentialite}</span>
          <h1 className="legal-titre">{doc.titre}</h1>
          <p className="legende-txt" style={{ fontSize: 14.5, maxWidth: 780 }}>{doc.chapeau}</p>
          <p className="legal-version">
            {L.version_label} {VERSION_POLITIQUE} · {L.maj_label} {DATE_POLITIQUE[langue] || DATE_POLITIQUE.fr}
            {' · '}{EDITEUR.nom}
          </p>
        </div>

        <div className="legal-onglets" role="tablist" aria-label={L.mentions.titre}>
          {ONGLETS_LEGAUX.map((cle) => (
            <button key={cle} type="button" role="tab" id={`onglet-${cle}`}
                    aria-selected={actif === cle} aria-controls={`doc-${cle}`}
                    className={actif === cle ? 'actif' : ''}
                    onClick={() => ouvrir(cle)}>
              {L[`onglet_${cle}`]}
            </button>
          ))}
        </div>

        <div className="legal-sommaire" aria-label="Sommaire">
          {doc.sections.map((sec, i) => (
            <a key={sec.t} href={`#${actif}-${i}`}
               onClick={(e) => {
                 e.preventDefault()
                 document.getElementById(`${actif}-${i}`)
                   ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
               }}>
              {sec.t}
            </a>
          ))}
        </div>

        <div className="legal-corps" id={`doc-${actif}`} role="tabpanel"
             aria-labelledby={`onglet-${actif}`}>
          {doc.sections.map((sec, i) => (
            <section key={sec.t} id={`${actif}-${i}`} className="legal-section">
              <h2>{sec.t}</h2>
              {sec.p.map((paragraphe) => <p key={paragraphe}>{paragraphe}</p>)}
            </section>
          ))}
        </div>

        <div className="legal-pied">
          <p>
            {langue === 'en'
              ? 'Questions about this document, or about your data? Write to '
              : 'Une question sur ce document ou sur vos données ? Écrivez à '}
            <a href={`mailto:${EDITEUR.email}`}>{EDITEUR.email}</a>.
          </p>
          <div className="legal-actions">
            <button type="button" className="btn btn-ghost btn-sm"
                    onClick={() => window.print()}>{L.imprimer}</button>
            <button type="button" className="btn btn-ghost btn-sm"
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
              ↑ {L.retour_haut}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
