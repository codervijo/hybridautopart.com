import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Mount to #psd-root (WordPress shortcode) or #root (dev server)
const container = document.getElementById('psd-root') || document.getElementById('root')

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>
)
