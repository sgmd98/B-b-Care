import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { api } from '../api'
import { useLangue } from '../i18n'

/* FONDS DE CARTE
   Pourquoi MapLibre + OpenFreeMap plutôt que Leaflet + tuiles raster :
   - tile.openstreetmap.org limite fortement les usages applicatifs (tuiles
     grises / 403) : c'est ce qui « bloquait » la carte à certains niveaux ;
   - CARTO impose désormais une clé API (filigrane « API KEY REQUIRED ») ;
   - OpenFreeMap sert des tuiles VECTORIELLES, gratuites, sans clé, sans quota
     et sans filigrane. Rendu net à tous les zooms, rotation, transitions
     fluides, et beaucoup moins de données transférées : ce qui compte sur un
     téléphone en 3G. */
const FONDS = {
  clair: { cle: 'c_fond_clair', style: 'https://tiles.openfreemap.org/styles/bright' },
  sobre: { cle: 'c_fond_sobre', style: 'https://tiles.openfreemap.org/styles/positron' },
  relief: { cle: 'c_fond_relief', style: 'https://tiles.openfreemap.org/styles/liberty' },
}

const ORDRE = ['hopital', 'centre_sante', 'maternite', 'pharmacie', 'medecin',
  'laboratoire', 'sante_autre']

export default function Carte({ pays, listePays, categories }) {
  const { t, langue } = useLangue()
  const refDiv = useRef(null)
  const refCarte = useRef(null)
  const refMoi = useRef(null)
  const refPopup = useRef(null)
  const refCharge = useRef(false)

  const [fond, setFond] = useState('clair')
  const [filtres, setFiltres] = useState([])
  const [visibles, setVisibles] = useState(0)
  const [selection, setSelection] = useState(null)
  const [proches, setProches] = useState(null)
  const [requete, setRequete] = useState('')
  const [resultats, setResultats] = useState(null)
  const [occupe, setOccupe] = useState(false)
  const [panneauOuvert, setPanneauOuvert] = useState(true)

  const couleurs = useMemo(() => {
    const c = {}
    Object.entries(categories || {}).forEach(([k, v]) => { c[k] = v.couleur })
    return c
  }, [categories])

  /* --------------------------------------------------------- couches */
  function poserCouches() {
    const carte = refCarte.current
    if (!carte || carte.getSource('lieux')) return

    carte.addSource('lieux', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] },
      cluster: true, clusterRadius: 58, clusterMaxZoom: 13,
    })

    // amas
    carte.addLayer({
      id: 'amas', type: 'circle', source: 'lieux', filter: ['has', 'point_count'],
      paint: {
        'circle-color': [
          'step', ['get', 'point_count'],
          'rgba(18,184,134,.88)', 100, 'rgba(15,150,112,.9)', 750, 'rgba(11,122,94,.94)',
        ],
        'circle-radius': ['step', ['get', 'point_count'], 17, 25, 22, 150, 28, 800, 35],
        'circle-stroke-width': 4,
        'circle-stroke-color': [
          'step', ['get', 'point_count'],
          'rgba(18,184,134,.22)', 100, 'rgba(15,150,112,.22)', 750, 'rgba(11,122,94,.2)',
        ],
      },
    })
    carte.addLayer({
      id: 'amas-texte', type: 'symbol', source: 'lieux', filter: ['has', 'point_count'],
      layout: {
        'text-field': ['get', 'point_count_abbreviated'],
        'text-font': ['Noto Sans Bold'],
        'text-size': ['step', ['get', 'point_count'], 12, 150, 13, 800, 14],
        'text-allow-overlap': true,
      },
      paint: { 'text-color': '#fff' },
    })

    // points unitaires
    const couleurExpr = ['match', ['get', 'c']]
    ORDRE.forEach((k) => { couleurExpr.push(k, couleurs[k] || '#888') })
    couleurExpr.push('#8a8a8a')

    carte.addLayer({
      id: 'points', type: 'circle', source: 'lieux', filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': couleurExpr,
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 4.5, 12, 7, 16, 10],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff',
        'circle-opacity': 0.95,
      },
    })

    carte.on('click', 'amas', (e) => {
      const f = carte.queryRenderedFeatures(e.point, { layers: ['amas'] })[0]
      carte.getSource('lieux').getClusterExpansionZoom(f.properties.cluster_id)
        .then((z) => carte.easeTo({ center: f.geometry.coordinates, zoom: z, duration: 600 }))
        .catch(() => {})
    })
    carte.on('click', 'points', (e) => {
      const p = e.features[0].properties
      setSelection({ ...p, lat: e.features[0].geometry.coordinates[1],
        lon: e.features[0].geometry.coordinates[0] })
    })
    for (const c of ['amas', 'points']) {
      carte.on('mouseenter', c, () => { carte.getCanvas().style.cursor = 'pointer' })
      carte.on('mouseleave', c, () => { carte.getCanvas().style.cursor = '' })
    }
    // survol : étiquette du nom
    carte.on('mouseenter', 'points', (e) => {
      const p = e.features[0].properties
      if (!p.n) return
      refPopup.current?.remove()
      refPopup.current = new maplibregl.Popup({
        closeButton: false, closeOnClick: false, offset: 12, className: 'popup-bc',
      }).setLngLat(e.features[0].geometry.coordinates).setText(p.n).addTo(carte)
    })
    carte.on('mouseleave', 'points', () => { refPopup.current?.remove(); refPopup.current = null })

    refCharge.current = true
    rafraichir()
  }

  /* -------------------------------------------------- initialisation */
  useEffect(() => {
    if (refCarte.current) return
    const carte = new maplibregl.Map({
      container: refDiv.current,
      style: FONDS[fond].style,
      center: [-3, 9.5], zoom: 4.2, minZoom: 2.5, maxZoom: 18,
      attributionControl: false,
    })
    carte.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-right')
    carte.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')
    carte.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution: '© OpenStreetMap · OpenFreeMap',
    }), 'bottom-right')
    carte.on('load', poserCouches)
    carte.on('moveend', rafraichir)
    refCarte.current = carte
    return () => { carte.remove(); refCarte.current = null; refCharge.current = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ------------------------------------------------ changement de fond */
  useEffect(() => {
    const carte = refCarte.current
    if (!carte || !refCharge.current) return
    refCharge.current = false
    carte.setStyle(FONDS[fond].style)
    carte.once('styledata', () => { poserCouches() })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fond])

  /* --------------------------------------------------- recentrage pays */
  useEffect(() => {
    const carte = refCarte.current
    if (!carte) return
    const p = listePays.find((x) => x.code === pays)
    if (p) carte.flyTo({ center: [p.lon, p.lat], zoom: p.zoom - 1.2, duration: 1400, essential: true })
  }, [pays, listePays])

  useEffect(() => { rafraichir() }, [filtres]) // eslint-disable-line

  async function rafraichir() {
    const carte = refCarte.current
    if (!carte || !refCharge.current) return
    const b = carte.getBounds()
    setOccupe(true)
    try {
      const d = await api.bbox({
        sud: b.getSouth(), ouest: b.getWest(), nord: b.getNorth(), est: b.getEast(),
      }, null, filtres, 4000)
      setVisibles(d.nb)
      const src = carte.getSource('lieux')
      if (src) {
        src.setData({
          type: 'FeatureCollection',
          features: d.lieux.map((l) => ({
            type: 'Feature',
            properties: { n: l.n, c: l.c, tel: l.tel, v: l.v, op: l.op, h: l.h, urg: l.urg, id: l.id, p: l.p },
            geometry: { type: 'Point', coordinates: [l.lon, l.lat] },
          })),
        })
      }
    } catch { /* on garde l'affichage précédent */ }
    setOccupe(false)
  }

  async function autourDeMoi() {
    if (!navigator.geolocation) { alert(t('c_geo_indispo')); return }
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const { latitude: lat, longitude: lon } = pos.coords
      const carte = refCarte.current
      carte.flyTo({ center: [lon, lat], zoom: 12.5, duration: 1400 })
      refMoi.current?.remove()
      const el = document.createElement('div')
      el.className = 'mk-moi'
      refMoi.current = new maplibregl.Marker({ element: el }).setLngLat([lon, lat]).addTo(carte)
      const d = await api.proches(lat, lon,
        filtres.length ? filtres : ['hopital', 'centre_sante', 'maternite'], 12)
      setProches(d.resultats); setResultats(null)
    }, () => alert(t('c_geo_refus')),
      { enableHighAccuracy: true, timeout: 12000 })
  }

  async function chercher(e) {
    e.preventDefault()
    if (requete.trim().length < 2) return
    const d = await api.recherche(requete, null)
    setResultats(d.resultats); setProches(null)
  }

  function aller(l) {
    setSelection(l)
    // Sur telephone : on replie le panneau pour voir le point sur la carte.
    if (window.matchMedia('(max-width: 820px)').matches) setPanneauOuvert(false)
    refCarte.current.flyTo({ center: [l.lon, l.lat], zoom: 15.5, duration: 1000 })
  }

  const liste = proches || resultats
  const nomCat = (c) => (categories[c]?.[langue] || categories[c]?.fr || c)
  const cat = (c) => categories[c] || { fr: c, couleur: '#888', icone: '⚕️' }

  return (
    <div className="zone-carte">
      <aside className={`panneau ${panneauOuvert ? 'ouvert' : ''}`}>
        <form onSubmit={chercher} className="groupe">
          <div className="recherche-barre">
            <span className="loupe">🔍</span>
            <input placeholder={t('c_rech_ph')} value={requete}
                   onChange={(e) => setRequete(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 9 }}>
            <button type="submit" className="bouton sec" style={{ flex: 1, justifyContent: 'center' }}>{t('c_chercher')}</button>
            <button type="button" className="bouton" style={{ flex: 1.25, justifyContent: 'center' }} onClick={autourDeMoi}>
              📍 {t('autour')}
            </button>
          </div>
        </form>

        <div className="groupe">
          <h4>{t('c_filtrer')}</h4>
          <div className="puces">
            {ORDRE.filter((k) => categories[k]).map((cle) => {
              const v = categories[cle]
              return (
                <button key={cle} className={`puce ${filtres.includes(cle) ? 'active' : ''}`}
                        onClick={() => setFiltres((f) => f.includes(cle) ? f.filter((x) => x !== cle) : [...f, cle])}>
                  <i style={{ width: 9, height: 9, borderRadius: 9, background: v.couleur, display: 'inline-block' }} />
                  {v[langue] || v.fr}
                </button>
              )
            })}
          </div>
        </div>

        {selection && (
          <div className="groupe">
            <h4>{t('c_structure_sel')}</h4>
            <div className="bloc" style={{ marginBottom: 0, padding: 16 }}>
              <div style={{ display: 'flex', gap: 11, alignItems: 'flex-start' }}>
                <div style={{ background: cat(selection.c).couleur, width: 34, height: 34, borderRadius: 10, display: 'grid', placeItems: 'center', flex: '0 0 auto', fontSize: 16 }}>
                  {cat(selection.c).icone}
                </div>
                <div>
                  <div style={{ fontWeight: 800, fontSize: 15.5, lineHeight: 1.3 }}>
                    {selection.n || t('c_sans_nom')}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--gris)', marginTop: 4 }}>
                    {nomCat(selection.c)}
                    {selection.v ? ` · ${selection.v}` : ''}
                    {selection.op ? ` · ${selection.op}` : ''}
                  </div>
                </div>
              </div>
              {selection.h && <div style={{ fontSize: 12.5, marginTop: 10 }}>🕐 {selection.h}</div>}
              {(selection.urg === true || selection.urg === 'true') &&
                <div style={{ fontSize: 12.5, marginTop: 6, color: 'var(--rouge)', fontWeight: 750 }}>{t('c_service_urgence')}</div>}
              <div style={{ display: 'flex', gap: 8, marginTop: 13, flexWrap: 'wrap' }}>
                <a className="bouton petit" href={`https://www.google.com/maps/dir/?api=1&destination=${selection.lat},${selection.lon}`}
                   target="_blank" rel="noreferrer">🧭 {t('itineraire')}</a>
                {selection.tel && <a className="bouton sec petit" href={`tel:${selection.tel}`}>📞 {selection.tel}</a>}
              </div>
            </div>
          </div>
        )}

        {liste && (
          <div className="groupe">
            <h4>{proches ? t('c_proches') : `${t('c_resultats')} (${liste.length})`}</h4>
            {liste.length === 0 && <p className="legende-txt">{t('aucun')}.</p>}
            {liste.map((l) => (
              <div key={l.p + l.id} className="resultat" onClick={() => aller(l)}>
                <div className="rond" style={{ background: cat(l.c).couleur }}>{cat(l.c).icone}</div>
                <div style={{ minWidth: 0 }}>
                  <div className="nom">{l.n || t('c_sans_nom_court')}</div>
                  <div className="meta">
                    <span>{nomCat(l.c)}</span>
                    {l.distance_km != null && <span className="dist">{l.distance_km} km</span>}
                    {l.tel && <span>📞</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </aside>

      <div className="leaflet-wrap">
        <div ref={refDiv} style={{ height: '100%', width: '100%' }} />
        <button type="button" className="btn-panneau"
                title={panneauOuvert ? t('c_voir_carte') : t('c_voir_liste')}
                aria-label={panneauOuvert ? t('c_voir_carte') : t('c_voir_liste')}
                onClick={() => setPanneauOuvert((v) => !v)}>
          {panneauOuvert ? '🗺️' : '☰'}
        </button>
        <div className="compteur-carte">
          {occupe ? t('charge') : <><b>{visibles.toLocaleString(langue === 'en' ? 'en-GB' : 'fr-FR')}</b> {t('c_structures_vis')}</>}
        </div>
        <div className="outils-carte">
          <div className="selecteur-fond">
            {Object.entries(FONDS).map(([cle, f]) => (
              <button key={cle} className={fond === cle ? 'actif' : ''} onClick={() => setFond(cle)}>{t(f.cle)}</button>
            ))}
          </div>
        </div>
        <div className="legende">
          {ORDRE.filter((k) => categories[k]).map((k) => (
            <div key={k}><i style={{ background: categories[k].couleur }} />{nomCat(k)}</div>
          ))}
        </div>
      </div>
    </div>
  )
}
