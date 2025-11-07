// src/GeminiChat.js
import React, { useState } from "react";
import { perguntarGemini } from "./geminiService";

function GeminiChat() {
  const [prompt, setPrompt] = useState("");
  const [resposta, setResposta] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResposta("Carregando...");

    try {
      console.log(prompt)
      const data = await perguntarGemini(prompt);
      console.log(data)
      setResposta(data.resposta || "Sem resposta do Gemini.");
    } catch (error) {
      setResposta("Erro ao consultar o Gemini.");
      console.error(error);
    }
  };

  return (
    <div style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #ccc" }}>
      <h2>Consulta ao Gemini</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Digite sua pergunta..."
          style={{ width: "100%", minHeight: "80px" }}
        />
        <br />
        <button type="submit">Perguntar</button>
      </form>
      {resposta && (
        <div style={{ marginTop: "1rem", whiteSpace: "pre-wrap" }}>
          <strong>Resposta:</strong>
          <p>{resposta}</p>
        </div>
      )}
    </div>
  );
}

export default GeminiChat;
