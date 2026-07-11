// =============================================================================
// main.jsx
// -----------------------------------------------------------------------------
// Ponto de entrada do frontend React.
// Monta o componente App dentro do elemento HTML principal e carrega os estilos globais.
// É executado pelo Vite quando a aplicação abre no browser.
// =============================================================================
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
