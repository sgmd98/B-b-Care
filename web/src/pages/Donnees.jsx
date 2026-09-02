import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis, Cell,
} from 'recharts'
import { api } from '../api'
import { useLangue } from '../i18n'

export default function Donnees({ pays, listePays }) {
  const { t } = useLangue()
  const [statut, setStatut] = useState(null)
  const [couv, setCouv] = useState(null)
  const [districts, setDistricts] = useState([])
  const [ou, setOu] = useState('ImspTQPwCqd')
  const [indic, setIndic] = useState('DTP3')
  const [comparaison, setComparaison] = useState(null)
  const [payload, setPayload] = useState(null)
  const [vaccins, setVaccins] = useState(['BCG', 'PENTA1', 'OPV1'])

  const INDICATEURS = [
    ['DTP3', t('d_i_dtp3')],
    ['MCV1', t('d_i_mcv1')],
    ['BCG', t('d_i_bcg')],
    ['PCV3', t('d_i_pcv3')],
    ['ROTA', t('d_i_rota')],
    ['U5MR', t('d_i_u5mr')],
  ]

  useEffect(() => {
    api.dhis2Statut().then(setStatut).catch(() => setStatut({ connecte: false }))
    api.dhis2Districts().then(setDistricts).catch(() => {})
  }, [])
  useEffect(() => { api.dhis2Couverture(ou).then(setCouv).catch(() => {}) }, [ou])
  useEffect(() => { api.omsComparaison(indic).then(setComparaison).catch(() => {}) }, [indic])

  const donneesGraphe = (() => {
    if (!couv?.series?.length) return []
    const map = {}
    couv.series.forEach((s) => {
      s.points.forEach((p) => {
        map[p.periode] = { ...(map[p.periode] || { periode: p.libelle }), [s.nom]: p.valeur }
      })
    })
    return Object.keys(map).sort().map((k) => map[k])
  })()

  const infosPays = listePays.find((p) => p.code === pays)

  async function genererPayload() {
    const d = await api.dhis2Export({
      org_unit: 'DiszpKrYNg8', vaccins, age_mois: 3, nutrition_code: 'pa_jaune',
    })
    setPayload(d)
  }

  const TOUS_VACCINS = ['BCG', 'OPV0', 'OPV1', 'OPV2', 'OPV3', 'PENTA1', 'PENTA2',
    'PENTA3', 'PCV1', 'PCV2', 'PCV3', 'MEASLES', 'YF', 'VITA']

  return (
    <div className="page">
      {/* --------------------------------------------------- Statut DHIS2 */}
      <div className="bloc">
        <h2>{t('d_h2')}</h2>
        <p className="legende-txt">
          {t('d_intro_a')} <b>{t('d_intro_b')}</b> {t('d_intro_c')}
        </p>
        {statut && (
          <div className="grille g4">
            <div className="stat">
              <div className="etiquette">{t('d_connexion')}</div>
              <div className="valeur" style={{ fontSize: 20, color: statut.connecte ? 'var(--vert)' : 'var(--rouge)' }}>
                {statut.connecte ? t('d_en_ligne') : t('d_hors_ligne')}
              </div>
              <div className="detail">{t('d_test_direct')}</div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('d_version')}</div>
              <div className="valeur" style={{ fontSize: 20 }}>{statut.version || '-'}</div>
              <div className="detail">{statut.revision}</div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('d_base')}</div>
              <div className="valeur" style={{ fontSize: 15, lineHeight: 1.3 }}>Sierra Leone</div>
              <div className="detail">{t('d_donnees_demo')}</div>
            </div>
            <div className="stat">
              <div className="etiquette">{t('d_mode_ecriture')}</div>
              <div className="valeur" style={{ fontSize: 16 }}>{statut.mode_ecriture || '-'}</div>
              <div className="detail">{t('d_aucune_ecriture')}</div>
            </div>
          </div>
        )}
      </div>

      {/* ------------------------------------------- Lecture live analytics */}
      <div className="bloc">
        <h3>{t('d_lecture_h')}</h3>
        <p className="legende-txt">
          {t('d_lecture_p')}
        </p>
        <label className="champ" style={{ maxWidth: 340 }}>
          {t('d_uo')}
          <select value={ou} onChange={(e) => setOu(e.target.value)}>
            <option value="ImspTQPwCqd">Sierra Leone {t('d_national')}</option>
            {districts.map((d) => <option key={d.id} value={d.id}>{d.nom}</option>)}
          </select>
        </label>
        {donneesGraphe.length > 0 ? (
          <div style={{ width: '100%', height: 320 }}>
            <ResponsiveContainer>
              <LineChart data={donneesGraphe} margin={{ top: 6, right: 12, bottom: 4, left: -18 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6ecf0" />
                <XAxis dataKey="periode" tick={{ fontSize: 10.5 }} interval={0} angle={-25} height={58} textAnchor="end" />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 10 }} />
                <Legend wrapperStyle={{ fontSize: 11.5 }} />
                {couv.series.map((s, i) => (
                  <Line key={s.id} type="monotone" dataKey={s.nom} dot={false} strokeWidth={2}
                        stroke={['#0f9d76', '#2e6fb7', '#f0872a', '#d7263d', '#7b6d8d'][i % 5]} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : <div className="chargement">{t('d_chargement')}</div>}
        {couv?.source && <div className="note">Source : {couv.source}</div>}
      </div>

      {/* ---------------------------------------------- Écriture / payload */}
      <div className="bloc">
        <h3>{t('d_ecriture_h')}</h3>
        <p className="legende-txt">
          {t('d_ecriture_p')}
        </p>
        <div className="puces" style={{ marginBottom: 12 }}>
          {TOUS_VACCINS.map((v) => (
            <button key={v} className={`puce ${vaccins.includes(v) ? 'active' : ''}`}
                    onClick={() => setVaccins((s) => s.includes(v) ? s.filter((x) => x !== v) : [...s, v])}>
              {v}
            </button>
          ))}
        </div>
        <button className="bouton" onClick={genererPayload}>
          {t('d_generer')}
        </button>
        {payload && (
          <div style={{ marginTop: 14 }}>
            <div className={`alerte ${payload.validation.valide ? 'vert' : 'rouge'}`}>
              <h4>{payload.validation.valide ? t('d_valide') : t('d_invalide')}</h4>
              <p>
                {payload.validation.nb_valeurs} {t('d_valeurs')} ·
                POST <code>{payload.endpoint}</code>
                {payload.validation.erreurs.length > 0 && ` · ${payload.validation.erreurs.join(', ')}`}
              </p>
            </div>
            <pre className="code">{JSON.stringify(payload.payload, null, 2)}</pre>
            <div className="note">{payload.explication}</div>
          </div>
        )}
      </div>

      {/* ------------------------------------------------ Comparatif OMS */}
      <div className="bloc">
        <h3>{t('d_oms_h')}</h3>
        <p className="legende-txt">
          {t('d_oms_p')}
          {infosPays && <> {t('d_pays_sel')} <b>{infosPays.drapeau} {infosPays.nom}</b>.</>}
        </p>
        <label className="champ" style={{ maxWidth: 340 }}>
          {t('n_indicateur')}
          <select value={indic} onChange={(e) => setIndic(e.target.value)}>
            {INDICATEURS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        {comparaison && (
          <div style={{ width: '100%', height: 340 }}>
            <ResponsiveContainer>
              <BarChart data={comparaison.lignes} margin={{ top: 6, right: 12, bottom: 44, left: -18 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6ecf0" />
                <XAxis dataKey="nom" tick={{ fontSize: 10.5 }} angle={-32} height={70} textAnchor="end" interval={0} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 10 }} />
                <Bar dataKey="valeur" radius={[6, 6, 0, 0]}>
                  {comparaison.lignes.map((l) => (
                    <Cell key={l.pays}
                          fill={l.pays === pays ? '#f0872a'
                            : indic === 'U5MR' ? '#7b6d8d'
                              : l.valeur >= 90 ? '#0f9d76' : l.valeur >= 70 ? '#63b995' : '#d7263d'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
        <div className="note">
          Source : {comparaison?.source}. {t('d_note_couv')}
        </div>
      </div>
    </div>
  )
}
