import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { useLangue } from '../i18n'

/* Le mode soignant repond au vrai probleme de terrain : un agent de sante
   communautaire note ses vaccinations sur papier, et quelqu'un les ressaisit
   dans DHIS2 des semaines plus tard. Ici il saisit UNE fois, et BebeCare
   produit le document dataValueSets agrege attendu par le SNIS national. */

const moisCourant = () => {
  const d = new Date()
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function Soignant() {
  const { t } = useLangue()
  const [formations, setFormations] = useState([])
  const [orgUnit, setOrgUnit] = useState('DiszpKrYNg8')
  const [periode, setPeriode] = useState(moisCourant())
  const [lignes, setLignes] = useState([])
  const [saisie, setSaisie] = useState({ prenom: '', age_mois: '', vaccins: [], nutrition_code: '' })
  const [res, setRes] = useState(null)
  const [envoi, setEnvoi] = useState(null)
  const [charge, setCharge] = useState(false)
  const [erreur, setErreur] = useState(null)

  const VACCINS = [
    ['BCG', 'BCG'], ['OPV0', 'OPV 0'], ['OPV1', 'OPV 1'], ['OPV2', 'OPV 2'], ['OPV3', 'OPV 3'],
    ['PENTA1', 'Penta 1'], ['PENTA2', 'Penta 2'], ['PENTA3', 'Penta 3'],
    ['PCV1', 'Pneumo 1'], ['PCV2', 'Pneumo 2'], ['PCV3', 'Pneumo 3'],
    ['MEASLES', t('g_rougeole')], ['YF', t('g_fievre_jaune')], ['VITA', t('g_vita')],
  ]
  const NUTRITION = [['', t('g_nut_aucun')], ['MAS', t('g_nut_mas')], ['MAM', t('g_nut_mam')]]

  useEffect(() => {
    api.dhis2Formations(300)
      .then((d) => {
        const l = d.formations || d.resultats || d.liste || []
        setFormations(l)
        if (l.length && !l.find((f) => f.id === orgUnit)) setOrgUnit(l[0].id)
      })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const total = useMemo(() => {
    const doses = lignes.reduce((n, l) => n + l.vaccins.length, 0)
    const bebes = lignes.filter((l) => Number(l.age_mois) < 12).length
    return { doses, bebes, grands: lignes.length - bebes }
  }, [lignes])

  function basculerVaccin(code) {
    setSaisie((s) => ({
      ...s,
      vaccins: s.vaccins.includes(code) ? s.vaccins.filter((v) => v !== code) : [...s.vaccins, code],
    }))
  }

  function ajouter() {
    if (saisie.age_mois === '' || (!saisie.vaccins.length && !saisie.nutrition_code)) {
      setErreur(t('g_err_ajout'))
      return
    }
    setErreur(null)
    setLignes((l) => [...l, { ...saisie, age_mois: Number(saisie.age_mois) }])
    setSaisie({ prenom: '', age_mois: '', vaccins: [], nutrition_code: '' })
    setRes(null); setEnvoi(null)
  }

  async function preparer() {
    setCharge(true); setErreur(null); setEnvoi(null)
    try {
      setRes(await api.dhis2Seance({ org_unit: orgUnit, periode, consultations: lignes }))
    } catch (e) { setErreur(String(e.message || e)) } finally { setCharge(false) }
  }

  async function envoyer() {
    setCharge(true); setErreur(null)
    try {
      setEnvoi(await api.dhis2SeanceEnvoyer({ org_unit: orgUnit, periode, consultations: lignes }))
    } catch (e) { setErreur(String(e.message || e)) } finally { setCharge(false) }
  }

  return (
    <div className="page">

      <div className="bloc">
        <span className="eyebrow">{t('g_eyebrow')}</span>
        <h2 style={{ marginTop: 12 }}>{t('g_pourquoi_h')}</h2>
        <p className="legende-txt" style={{ fontSize: 14.5 }}>
          {t('g_p1')}
        </p>
        <p className="legende-txt" style={{ fontSize: 14.5 }}>
          {t('g_p2a')} <strong>{t('g_une_fois')}</strong>{t('g_p2c')}
        </p>
        <div className="note">
          <strong>{t('g_securite_t')}</strong> {t('g_sec2a')}
          {' '}<code>BEBECARE_DHIS2_PUSH</code>{t('g_sec2b')}
        </div>
      </div>

      {/* ------------------------------------------------ PARAMÈTRES DE SÉANCE */}
      <div className="bloc">
        <h3>{t('g_seance_h')}</h3>
        <p className="sub legende-txt">{t('g_seance_p')}</p>
        <div className="grid2">
          <div className="field">
            <label>{t('g_formation')}</label>
            {formations.length ? (
              <select className="form-select" value={orgUnit} onChange={(e) => setOrgUnit(e.target.value)}>
                {formations.map((f) => <option key={f.id} value={f.id}>{f.nom || f.name} · {f.id}</option>)}
              </select>
            ) : (
              <input className="form-control" value={orgUnit} onChange={(e) => setOrgUnit(e.target.value)}
                     placeholder={t('g_org_ph')} />
            )}
          </div>
          <div className="field">
            <label>{t('g_periode')}</label>
            <input className="form-control" value={periode} onChange={(e) => setPeriode(e.target.value)}
                   placeholder="202609" />
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------- SAISIE ENFANT */}
      <div className="bloc">
        <h3>{t('g_enfants_h')}</h3>
        <p className="sub legende-txt">
          {t('g_enfants_p')}
        </p>
        <div className="grid2">
          <div className="field">
            <label>{t('g_prenom')}</label>
            <input className="form-control" value={saisie.prenom}
                   onChange={(e) => setSaisie({ ...saisie, prenom: e.target.value })} placeholder="Amina" />
          </div>
          <div className="field">
            <label>{t('g_age_mois')}</label>
            <input className="form-control" type="number" step="any" min="0" max="60" value={saisie.age_mois}
                   onChange={(e) => setSaisie({ ...saisie, age_mois: e.target.value })} placeholder="3" />
          </div>
        </div>

        <div className="field">
          <label>{t('g_vaccins')}</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {VACCINS.map(([code, lib]) => {
              const on = saisie.vaccins.includes(code)
              return (
                <button key={code} type="button" onClick={() => basculerVaccin(code)}
                        className={on ? 'btn btn-primary btn-sm' : 'btn btn-ghost btn-sm'}>
                  {lib}
                </button>
              )
            })}
          </div>
        </div>

        <div className="field" style={{ maxWidth: 320 }}>
          <label>{t('g_depistage')}</label>
          <select className="form-select" value={saisie.nutrition_code}
                  onChange={(e) => setSaisie({ ...saisie, nutrition_code: e.target.value })}>
            {NUTRITION.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>

        {erreur && <div className="alert alert-error">{erreur}</div>}
        <button className="btn btn-primary" onClick={ajouter}>{t('g_ajouter')}</button>
      </div>

      {/* ----------------------------------------------------------- LE REGISTRE */}
      {lignes.length > 0 && (
        <div className="bloc">
          <h3>{t('g_registre_h')}</h3>
          <p className="sub legende-txt">
            {lignes.length} {t('g_enfants_u')} · {total.doses} {t('g_doses_u')} · {total.bebes} {t('g_moins1')} ·
            {' '}{total.grands} {t('g_plus1')}
          </p>
          <table className="sib-table">
            <thead>
              <tr><th>{t('c_prenom')}</th><th>{t('v_age')}</th><th>{t('g_th_vaccins')}</th><th>Nutrition</th><th /></tr>
            </thead>
            <tbody>
              {lignes.map((l, i) => (
                <tr key={i}>
                  <td>{l.prenom || <span style={{ opacity: .5 }}>{t('g_anonyme')}</span>}</td>
                  <td>{l.age_mois} {t('acc_mois')}</td>
                  <td>{l.vaccins.join(', ') || '-'}</td>
                  <td>{l.nutrition_code || '-'}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn btn-ghost btn-sm"
                            onClick={() => { setLignes(lignes.filter((_, k) => k !== i)); setRes(null); setEnvoi(null) }}>
                      {t('g_retirer')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={preparer} disabled={charge}>
              {charge ? t('n_calcul') : t('g_preparer')}
            </button>
            <button className="btn btn-ghost" onClick={() => { setLignes([]); setRes(null); setEnvoi(null) }}>
              {t('g_vider')}
            </button>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- LE RÉSULTAT */}
      {res && (
        <>
          <div className="bloc">
            <h3>{t('g_part_h')}</h3>
            <p className="sub legende-txt">
              {res.resume.nb_consultations} {t('g_part_a')} {res.resume.nb_lignes_dhis2}{' '}
              {t('g_part_b')}
            </p>
            <div className="grid3">
              {Object.entries(res.resume.doses_par_vaccin).map(([v, n]) => (
                <div key={v} className="metric"><div className="k">{v}</div><div className="v">{n} {t('g_doses_u')}</div></div>
              ))}
            </div>
            <div style={{ marginTop: 18 }}>
              <span className={`badge-pill ${res.validation.valide ? 'badge-ok' : 'badge-danger'}`}>
                {res.validation.valide
                  ? `${t('g_valide')} · ${res.validation.nb_valeurs} ${t('g_valeurs')}`
                  : `✕ ${res.validation.erreurs.length} ${t('g_erreurs')}`}
              </span>
              {res.vaccins_non_mappes.length > 0 && (
                <span className="badge-pill badge-warn" style={{ marginLeft: 10 }}>
                  {t('g_non_mappes')} : {res.vaccins_non_mappes.join(', ')}
                </span>
              )}
            </div>
          </div>

          <div className="bloc">
            <h3>{t('g_doc_brut')}</h3>
            <p className="sub legende-txt">
              POST <code>{res.endpoint}</code>
            </p>
            <pre style={{
              background: 'var(--teal-900)', color: '#d7f0ea', padding: 18, borderRadius: 12,
              overflow: 'auto', fontSize: 12.5, lineHeight: 1.55, maxHeight: 380,
            }}>{JSON.stringify(res.payload, null, 2)}</pre>
            <p className="legende-txt" style={{ fontSize: 13.5 }}>{res.explication}</p>

            <div style={{ marginTop: 16 }}>
              {res.ecriture_activee ? (
                <button className="btn btn-primary" onClick={envoyer} disabled={charge}>
                  {t('g_envoyer_reel')}
                </button>
              ) : (
                <div className="note">
                  <strong>{t('g_envoi_off_t')}</strong> {t('g_envoi_off_a')}
                  {' '}<code>BEBECARE_DHIS2_PUSH=1</code>.
                  <div style={{ marginTop: 12 }}>
                    <button className="btn btn-ghost btn-sm" onClick={envoyer} disabled={charge}>
                      {t('g_tester')}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {envoi && (
              <div className={`alert ${envoi.envoye ? 'alert-success' : 'alert-info'}`} style={{ marginTop: 16 }}>
                {envoi.envoye
                  ? `${t('g_envoye_a')} ${envoi.statut_http}.`
                  : envoi.raison}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
