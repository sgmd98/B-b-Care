import { Component } from 'react'

/* Sans ce garde-fou, une seule erreur dans un graphique suffit a faire
   disparaitre tout le site : React demonte l'arbre entier et l'ecran devient
   blanc. Pendant une demonstration devant un jury, c'est fatal. */

export default class Bouclier extends Component {
  constructor(props) {
    super(props)
    this.state = { erreur: null }
  }

  static getDerivedStateFromError(erreur) {
    return { erreur }
  }

  componentDidCatch(erreur, info) {
    console.error('[BébéCare] erreur capturée :', erreur, info)
  }

  render() {
    if (!this.state.erreur) return this.props.children

    return (
      <div className="bloc" style={{ borderLeft: '5px solid var(--danger, #e53935)' }}>
        <h3 style={{ marginTop: 0 }}>Cette section n’a pas pu s’afficher</h3>
        <p className="legende-txt">
          Le reste du site fonctionne normalement. Vous pouvez réessayer, ou
          passer à un autre module.
        </p>
        <details style={{ margin: '12px 0' }}>
          <summary style={{ cursor: 'pointer', fontSize: 13.5 }}>Détail technique</summary>
          <pre style={{
            marginTop: 10, background: '#06322c', color: '#d7f0ea', padding: 14,
            borderRadius: 10, fontSize: 12, overflow: 'auto', whiteSpace: 'pre-wrap',
          }}>{String(this.state.erreur?.stack || this.state.erreur)}</pre>
        </details>
        <button className="btn btn-primary btn-sm"
                onClick={() => this.setState({ erreur: null })}>
          Réessayer
        </button>
      </div>
    )
  }
}
