import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './sib.css'
import './index.css'
import App from './App.jsx'
import { FournisseurLangue } from './i18n.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <FournisseurLangue>
      <App />
    </FournisseurLangue>
  </StrictMode>,
)
