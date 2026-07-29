import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initTheme } from './lib/theme.js'
import './styles/tokens.css'
import './styles/shell.css'
import './styles/screens.css'
import App from './App.jsx'

// Applied before the first render so a night-mode reload never flashes the
// day palette.
initTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
