import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from './api'

const Ctx = createContext(null)
const CLE = 'bebecare.jeton'

export function FournisseurAuth({ children }) {
  const [jeton, setJeton] = useState(() => localStorage.getItem(CLE))
  const [utilisateur, setUtilisateur] = useState(null)
  const [enfants, setEnfants] = useState([])
  const [pret, setPret] = useState(false)

  const deconnecter = useCallback(() => {
    localStorage.removeItem(CLE); setJeton(null); setUtilisateur(null); setEnfants([])
  }, [])

  const rechargerEnfants = useCallback(async () => {
    if (!jeton) return
    try { setEnfants(await api.enfants(jeton)) } catch { /* silencieux */ }
  }, [jeton])

  useEffect(() => {
    if (!jeton) { setPret(true); return }
    api.moi(jeton)
      .then((u) => { setUtilisateur(u); return api.enfants(jeton) })
      .then(setEnfants)
      .catch(() => deconnecter())
      .finally(() => setPret(true))
  }, [jeton, deconnecter])

  const valeur = useMemo(() => ({
    jeton, utilisateur, enfants, pret,
    connecte: !!utilisateur,
    async inscrire(donnees) {
      const r = await api.inscription(donnees)
      localStorage.setItem(CLE, r.jeton); setJeton(r.jeton); setUtilisateur(r.utilisateur)
      return r
    },
    async connecter(identifiant, mot_de_passe) {
      const r = await api.connexion({ identifiant, mot_de_passe })
      localStorage.setItem(CLE, r.jeton); setJeton(r.jeton); setUtilisateur(r.utilisateur)
      return r
    },
    deconnecter,
    async majProfil(champs) {
      const u = await api.majProfil(jeton, champs); setUtilisateur(u); return u
    },
    async ajouterEnfant(e) { const r = await api.ajouterEnfant(jeton, e); await rechargerEnfants(); return r },
    async majEnfant(id, e) { const r = await api.majEnfant(jeton, id, e); await rechargerEnfants(); return r },
    async supprimerEnfant(id) { await api.supprimerEnfant(jeton, id); await rechargerEnfants() },
    rechargerEnfants,
  }), [jeton, utilisateur, enfants, pret, deconnecter, rechargerEnfants])

  return <Ctx.Provider value={valeur}>{children}</Ctx.Provider>
}

export const useAuth = () => useContext(Ctx)
