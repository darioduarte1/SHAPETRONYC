// =============================================================================
// AppMessages.jsx
// -----------------------------------------------------------------------------
// Componente visual das mensagens globais da app.
// É usado pelo App.jsx para mostrar erros, confirmações e avisos sem recorrer
// a pop-ups nativos do browser. Mantém o atleta dentro do fluxo normal da app.
// =============================================================================
export default function AppMessages({ messages, dismissMessage }) {
  if (!messages.length) {
    return null;
  }

  return (
    <div className="app-message-stack" role="status" aria-live="polite">
      {messages.map((message) => (
        <div key={message.id} className={`app-message ${message.type}`}>
          <div>
            <strong>{message.title}</strong>
            {message.detail && <p>{message.detail}</p>}
          </div>
          <button type="button" onClick={() => dismissMessage(message.id)}>
            Fechar
          </button>
        </div>
      ))}
    </div>
  );
}
