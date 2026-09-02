/* Logo BébéCare : SVG vectoriel, net à toutes les tailles, aucun réseau requis.
   Concept : un croissant protecteur (le bras de la mère) qui entoure la tête
   d'un bébé, l'espace négatif dessinant un cœur. */

export function Logo({ taille = 36, mono = false }) {
  const fond = mono ? 'currentColor' : 'url(#bc-degrade)'
  return (
    <svg width={taille} height={taille} viewBox="0 0 64 64" aria-label="BébéCare"
         role="img" style={{ display: 'block', flex: '0 0 auto' }}>
      <defs>
        <linearGradient id="bc-degrade" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#12b886" />
          <stop offset="100%" stopColor="#0b7a5e" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="64" height="64" rx="17" fill={fond} />
      {/* bras protecteur */}
      <path
        d="M46.5 15.5c5.6 4.3 9 11 9 18.5C55.5 47.6 44.9 58 32 58S8.5 47.6 8.5 34
           C8.5 20.4 19.1 10 32 10c2.5 0 4.9.4 7.2 1.1"
        fill="none" stroke="#fff" strokeWidth="5.4" strokeLinecap="round" />
      {/* tête du bébé */}
      <circle cx="32" cy="30" r="8.6" fill="#fff" />
      {/* mèche */}
      <path d="M32 21.4c1.4-2.6 4-3.4 5.6-2.2-1.6.5-2.4 1.6-2.6 3.1"
            fill="#fff" />
      {/* corps blotti */}
      <path d="M20.6 47.5c1.6-6 6-9.6 11.4-9.6s9.8 3.6 11.4 9.6c-3.3 2.4-7.2 3.7-11.4 3.7
               s-8.1-1.3-11.4-3.7Z" fill="#fff" opacity=".92" />
      {/* cœur */}
      <path d="M48.6 20.6c1.7-2 4.6-2.1 6.4-.3 1.8 1.8 1.8 4.7 0 6.6l-6.3 6.4-6.3-6.4
               c-1.8-1.9-1.8-4.8 0-6.6 1.8-1.8 4.7-1.7 6.2.3Z"
            fill="#ffd166" stroke={mono ? 'currentColor' : '#0b7a5e'} strokeWidth="1.6" />
    </svg>
  )
}

export function LogoTexte({ slogan }) {
  return (
    <div className="marque">
      <Logo taille={38} />
      <div className="marque-texte">
        <span className="marque-nom">Bébé<span>Care</span></span>
        {slogan && <span className="marque-slogan">{slogan}</span>}
      </div>
    </div>
  )
}
