import { useState } from 'react'
import {
  Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend, Scatter, ComposedChart,
} from 'recharts'
import { api } from '../api'
import Bouclier from '../Bouclier'
import { useLangue } from '../i18n'

/* Tranches OMS d'alimentation du nourrisson et du jeune enfant */
function cleConseil(age) {
  if (age < 6) return 'cn_0_5'
  if (age < 9) return 'cn_6_8'
  if (age < 12) return 'cn_9_11'
  if (age < 24) return 'cn_12_23'
  return 'cn_24_59'
}

/* Le marqueur de l'enfant : point noir cercle de blanc, convention
   des courbes de croissance OMS (comme sur le carnet de sante). */
function PointEnfant(props) {
  const { cx, cy } = props
  if (cx == null || cy == null) return null
  return (
    <g>
      <circle cx={cx} cy={cy} r={12} fill="#16232e" opacity={0.18} />
      <circle cx={cx} cy={cy} r={7} fill="#16232e" stroke="#fff" strokeWidth={2.5} />
    </g>
  )
}

/* Un graphique de courbe OMS : couloirs -3/-2/mediane/+2 + le point de l'enfant.
   Les deux axes sont NUMERIQUES : l'age de l'enfant (6,3 mois par ex.) n'est pas
   forcement une valeur entiere de l'echelle, et le Scatter doit pouvoir le placer
   exactement, sinon il retombe sur l'axe des abscisses. */
function CourbeBloc({ titre, sousTitre, courbe, point, axeX, uniteY, t }) {
  // Le domaine inclut toujours le point de l'enfant, meme hors des couloirs OMS.
  const xs = courbe.map((r) => r.x)
  const ys = courbe.flatMap((r) => [r.z3, r.p2].filter((v) => typeof v === 'number'))
  if (point) { xs.push(point.x); ys.push(point.y) }
  const xMin = Math.floor(Math.min(...xs))
  const xMax = Math.ceil(Math.max(...xs))
  const yMin = Math.max(0, Math.floor(Math.min(...ys) - 0.5))
  const yMax = Math.ceil(Math.max(...ys) + 0.5)
  return (
    <Bouclier>
      <div className="bloc">
        <h3>{titre}</h3>
        <p className="legende-txt">{sousTitre}</p>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <ComposedChart data={courbe} margin={{ top: 6, right: 12, bottom: 6, left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e6ecf0" />
              <XAxis dataKey="x" type="number" domain={[xMin, xMax]} tickCount={10}
                     tick={{ fontSize: 11 }}
                     label={{ value: axeX, position: 'insideBottom', offset: -3, fontSize: 11 }} />
              <YAxis type="number" domain={[yMin, yMax]} tick={{ fontSize: 11 }} width={44}
                     label={{ value: uniteY, angle: -90, position: 'insideLeft', fontSize: 11 }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 10 }} />
              <Legend wrapperStyle={{ fontSize: 11.5 }} />
              <Line type="monotone" dataKey="z3" name={t('n_l3')} stroke="#d7263d" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="z2" name={t('n_l2')} stroke="#f0872a" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="med" name={t('n_lm')} stroke="#0f9d76" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="p2" name={t('n_lp')} stroke="#2e6fb7" dot={false} strokeDasharray="4 4" />
              {point && <Scatter data={[point]} dataKey="y" name={t('n_votre_enfant')}
                                 fill="#16232e" shape={<PointEnfant />} />}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Bouclier>
  )
}

export default function Nutrition() {
  const { t } = useLangue()
  const [f, setF] = useState({ age_mois: '', sexe: 'm', poids_kg: '', taille_cm: '', pb_mm: '', oedemes: false })
  const [res, setRes] = useState(null)
  // 3 courbes OMS : pa = poids/age, ta = taille/age, pt = poids/taille
  const [courbes, setCourbes] = useState({ pa: null, ta: null, pt: null })
  const [occupe, setOccupe] = useState(false)
  const [err, setErr] = useState(null)

  const ageNum = parseFloat(f.age_mois)
  const ageValide = !Number.isNaN(ageNum) && ageNum >= 0 && ageNum <= 60

  /* Convertit la reponse /api/nutrition/courbe en points traces.
     diviseurX : 30.4375 pour afficher l'axe en mois, 1 pour les cm. */
  const traduire = (c, diviseurX) => {
    const px = c?.points?.x
    if (!Array.isArray(px) || !px.length) return null
    return px.map((x, i) => ({
      x: Math.round((x / diviseurX) * 10) / 10,
      z3: c.points.z_moins3?.[i],
      z2: c.points.z_moins2?.[i],
      med: c.points.median?.[i],
      p2: c.points.z_plus2?.[i],
    }))
  }

  async function evaluer(e) {
    e.preventDefault()
    setOccupe(true); setErr(null)
    try {
      const corps = { age_mois: ageNum, sexe: f.sexe, oedemes: f.oedemes }
      if (f.poids_kg) corps.poids_kg = parseFloat(f.poids_kg)
      if (f.taille_cm) corps.taille_cm = parseFloat(f.taille_cm)
      if (f.pb_mm) corps.pb_mm = parseFloat(f.pb_mm)
      const d = await api.depistage(corps)
      setRes(d)

      /* Les 3 courbes se chargent en parallele. Si l'une echoue,
         les autres restent affichees. */
      const vide = { pa: null, ta: null, pt: null }
      const [pa, ta, pt] = await Promise.all([
        api.courbe('wfa', f.sexe, 0, 1856, 30.4375).then((c) => traduire(c, 30.4375)).catch(() => null),
        api.courbe('lhfa', f.sexe, 0, 1856, 30.4375).then((c) => traduire(c, 30.4375)).catch(() => null),
        api.courbe(ageNum < 24 ? 'wfl' : 'wfh', f.sexe, ageNum < 24 ? 45 : 65, 110, 0.5)
          .then((c) => traduire(c, 1)).catch(() => null),
      ])
      setCourbes({ ...vide, pa, ta, pt })
    } catch (e2) {
      setRes(null)
      setErr(e2?.message ? e2.message : String(e2))
    }
    setOccupe(false)
  }

  const nbMesures = res ? Object.keys(res.indicateurs || {}).length : 0
  const poidsNum = f.poids_kg ? parseFloat(f.poids_kg) : null
  const tailleNum = f.taille_cm ? parseFloat(f.taille_cm) : null
  const sexeTxt = f.sexe === 'm' ? t('n_garcons') : t('n_filles')

  return (
    <div className="page">
      <div className="bloc">
        <h2>{t('t_nutrition')}</h2>
        <p className="legende-txt">{t('n_intro')}</p>
        <form onSubmit={evaluer} noValidate>
          <div className="grille g3">
            <label className="champ">
              {t('n_age')} *
              <input type="number" step="any" min="0" max="60" required
                     value={f.age_mois} onChange={(e) => setF({ ...f, age_mois: e.target.value })} />
            </label>
            <label className="champ">
              {t('n_sexe')} *
              <select value={f.sexe} onChange={(e) => setF({ ...f, sexe: e.target.value })}>
                <option value="m">{t('n_garcon')}</option>
                <option value="f">{t('n_fille')}</option>
              </select>
            </label>
            <label className="champ">
              {t('n_poids')}
              <input type="number" step="any" value={f.poids_kg}
                     onChange={(e) => setF({ ...f, poids_kg: e.target.value })} />
            </label>
            <label className="champ">
              {t('n_taille')}
              <input type="number" step="any" value={f.taille_cm}
                     onChange={(e) => setF({ ...f, taille_cm: e.target.value })} />
            </label>
            <label className="champ">
              {t('n_pb')}
              <input type="number" step="any" placeholder={t('n_muac_ph')} value={f.pb_mm}
                     onChange={(e) => setF({ ...f, pb_mm: e.target.value })} />
            </label>
            <label className="champ" style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
              <input type="checkbox" checked={f.oedemes} style={{ width: 18, height: 18 }}
                     onChange={(e) => setF({ ...f, oedemes: e.target.checked })} />
              <span>{t('n_oedemes')}</span>
            </label>
          </div>
          <button className="bouton" disabled={occupe}>
            {occupe ? t('n_calcul') : t('n_analyser')}
          </button>
        </form>
      </div>

      {/* Conseils nutritionnels selon l'age : visibles des que l'age est saisi */}
      {ageValide && (
        <div className="bloc" style={{ borderLeft: '6px solid var(--vert, #2e9e4f)' }}>
          <h3>{t('cn_titre')} ({Math.floor(ageNum)} {t('acc_mois')})</h3>
          <p className="legende-txt" style={{ fontSize: 14.5 }}>{t(cleConseil(ageNum))}</p>
          <div className="note">{t('cn_note')}</div>
        </div>
      )}

      {err && <div className="alerte rouge"><h4>{t('erreur')}</h4><p>{err}</p></div>}

      {res && (
        <>
          {(() => {
            const n = res.verdict || 'vert'
            const fond = n === 'rouge' ? '#fdeeee' : n === 'orange' ? '#fff3e0' : '#e0f2f1'
            const bord = n === 'rouge' ? '#e53935' : n === 'orange' ? '#e0a000' : '#2e9e4f'
            const mot = n === 'rouge' ? t('n_urgent')
                      : n === 'orange' ? t('n_surveillance')
                      : t('n_normes')
            return (
              <div className="bloc" style={{ background: fond, borderLeft: `6px solid ${bord}` }}>
                <span className="eyebrow">{t('n_resultat')}</span>
                <h2 style={{ margin: '10px 0 6px', color: bord }}>
                  {n === 'rouge' ? '🚨 ' : n === 'orange' ? '⚠️ ' : '✅ '}{mot}
                </h2>
                <p className="legende-txt" style={{ fontSize: 14.5, marginBottom: 0 }}>
                  {t('n_enfant_de')} {res.age_mois} {t('acc_mois')}, {res.sexe === 'f' ? t('n_filles') : t('n_garcons')}.
                  {' '}{nbMesures === 0 ? t('n_aucune_mesure') : `${nbMesures} ${t('n_calcules')}`}
                </p>
              </div>
            )
          })()}

          {res.alertes.map((a, i) => (
            <div key={i} className={`alerte ${a.niveau}`}>
              <h4>{a.niveau === 'rouge' ? '🚨 ' : a.niveau === 'orange' ? '⚠️ ' : '✅ '}{a.titre}</h4>
              <p>{a.action}</p>
            </div>
          ))}

          {nbMesures > 0 && (
          <div className="bloc">
            <h3>{t('n_detail')}</h3>
                        <div className="table-scroll">
<table className="t">
              <thead><tr><th>{t('n_indicateur')}</th><th>{t('n_zscore')}</th><th>{t('n_interpretation')}</th><th>{t('n_repere')}</th></tr></thead>
              <tbody>
                {Object.entries(res.indicateurs).filter(([k]) => k !== 'pb').map(([k, v]) => (
                  <tr key={k}>
                    <td>{v.libelle}</td>
                    <td><b style={{ color: v.z < -3 ? 'var(--rouge)' : v.z < -2 ? 'var(--orange)' : 'var(--vert)' }}>
                      {v.z > 0 ? '+' : ''}{v.z}
                    </b></td>
                    <td>{v.classe}</td>
                    <td style={{ minWidth: 130 }}>
                      <div className="barre-fond">
                        <i style={{
                          width: `${Math.min(100, Math.max(2, ((v.z + 5) / 10) * 100))}%`,
                          background: v.z < -3 ? 'var(--rouge)' : v.z < -2 ? 'var(--orange)' : 'var(--vert)',
                        }} />
                      </div>
                    </td>
                  </tr>
                ))}
                {res.indicateurs.pb && (
                  <tr>
                    <td>{res.indicateurs.pb.libelle}</td>
                    <td><b>{res.indicateurs.pb.valeur_mm} mm</b></td>
                    <td>{res.indicateurs.pb.classe}</td>
                    <td style={{ fontSize: 11.5, color: 'var(--gris)' }}>
                      {t('n_seuils')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>
            <div className="note">{res.source}. {res.avertissement}</div>
          </div>
          )}

          {/* ---------- Les 3 courbes OMS, avec le point de l'enfant ---------- */}
          {courbes.pa && (
            <CourbeBloc
              titre={`${t('n_courbe')} (${sexeTxt})`}
              sousTitre={t('n_courbe_p')}
              courbe={courbes.pa}
              point={poidsNum ? { x: Math.round(ageNum * 10) / 10, y: poidsNum } : null}
              axeX={t('n_axe_age')} uniteY="kg" t={t}
            />
          )}
          {courbes.ta && (
            <CourbeBloc
              titre={`${t('n_courbe_ta')} (${sexeTxt})`}
              sousTitre={t('n_courbe_p')}
              courbe={courbes.ta}
              point={tailleNum ? { x: Math.round(ageNum * 10) / 10, y: tailleNum } : null}
              axeX={t('n_axe_age')} uniteY="cm" t={t}
            />
          )}
          {courbes.pt && (
            <CourbeBloc
              titre={`${t('n_courbe_pt')} (${sexeTxt})`}
              sousTitre={t('n_courbe_p')}
              courbe={courbes.pt}
              point={(tailleNum && poidsNum) ? { x: tailleNum, y: poidsNum } : null}
              axeX={t('n_axe_taille')} uniteY="kg" t={t}
            />
          )}
        </>
      )}
    </div>
  )
}
