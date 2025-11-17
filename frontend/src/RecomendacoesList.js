import React, { useEffect, useState } from "react";

function RecomendacoesList() {
  const [recomendacoes, setRecomendacoes] = useState([]);
  const [avaliacoes, setAvaliacoes] = useState({});
  const [comentarios, setComentarios] = useState({});
  const token = localStorage.getItem("token");

  // 🔹 Carrega as recomendações do backend
  useEffect(() => {
    fetch("http://localhost:5000/recomendacoes", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.recomendacoes) setRecomendacoes(data.recomendacoes);
      })
      .catch((err) => console.error("Erro ao carregar recomendações:", err));
  }, [token]);

  // 🔹 Envia avaliação + comentário
  const enviarAvaliacao = async (idRecomendacao) => {
    const nota = avaliacoes[idRecomendacao];
    const comentario = comentarios[idRecomendacao];

    if (!nota) return alert("Escolha uma nota antes de enviar.");

    try {
      const res = await fetch(`http://localhost:5000/recomendacoes/${idRecomendacao}/avaliar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ nota, comentario }),
      });

      if (res.ok) {
        alert("Avaliação enviada!");
        // opcional: limpar nota e comentário
        setAvaliacoes((prev) => ({ ...prev, [idRecomendacao]: "" }));
        setComentarios((prev) => ({ ...prev, [idRecomendacao]: "" }));
      } else {
        alert("Erro ao enviar avaliação.");
      }
    } catch (err) {
      console.error(err);
      alert("Erro de conexão com o servidor.");
    }
  };

  return (
    <div style={{ marginTop: "2rem" }}>
      <h2>Minhas Recomendações</h2>
      {recomendacoes.length === 0 ? (
        <p>Nenhuma recomendação gerada ainda.</p>
      ) : (
        recomendacoes.map((rec) => (
          <div
            key={rec.id_recomendacao}
            style={{
              border: "1px solid #ccc",
              borderRadius: "8px",
              padding: "10px",
              marginBottom: "15px",
            }}
          >
            <strong>Pergunta:</strong>
            <p>{rec.prompt}</p>
            <strong>Resposta:</strong>
            <p>{rec.resposta}</p>
            <small>{new Date(rec.data_geracao).toLocaleString()}</small>

            <div style={{ marginTop: "10px" }}>
              <label>Avaliar (1-5): </label>
              <input
                type="number"
                min="1"
                max="5"
                value={avaliacoes[rec.id_recomendacao] || ""}
                onChange={(e) =>
                  setAvaliacoes({
                    ...avaliacoes,
                    [rec.id_recomendacao]: e.target.value,
                  })
                }
                style={{ width: "50px", marginRight: "10px" }}
              />
            </div>

            <div style={{ marginTop: "10px" }}>
              <label>Comentário:</label>
              <textarea
                value={comentarios[rec.id_recomendacao] || ""}
                onChange={(e) =>
                  setComentarios({
                    ...comentarios,
                    [rec.id_recomendacao]: e.target.value,
                  })
                }
                rows="3"
                style={{ width: "100%", marginTop: "5px" }}
              />
            </div>

            <button
              style={{ marginTop: "10px" }}
              onClick={() => enviarAvaliacao(rec.id_recomendacao)}
            >
              Enviar
            </button>
          </div>
        ))
      )}
    </div>
  );
}

export default RecomendacoesList;
