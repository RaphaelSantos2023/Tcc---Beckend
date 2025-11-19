import React, { useState, useEffect } from "react";

function PerfilAcademico() {
  const [perfil, setPerfil] = useState({
    periodo_atual: "",
    ira_geral: "",
    interesses_principais: "",
    habilidades: "",
    objetivo_carreira: ""
  });
  const [msg, setMsg] = useState('');

  const token = localStorage.getItem("token");

  // 🔹 Buscar perfil existente (caso já tenha)
  useEffect(() => {
    fetch("http://localhost:5000/perfil", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.perfil) setPerfil(data.perfil);
      })
      .catch(() => {});
  }, [token]);

  // 🔹 Atualizar estado
  const handleChange = (e) => {
    setPerfil({ ...perfil, [e.target.name]: e.target.value });
  };

  // 🔹 Enviar para o backend
  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await fetch("http://localhost:5000/perfil", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(perfil),
    });

    const data = await res.json();
    setPerfil({
            periodo_atual: "",
            ira_geral: "",
            interesses_principais: "",
            habilidades: "",
            objetivo_carreira: ""
        });
    alert(data.message || "Perfil salvo!");
  };

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <h2>Perfil Acadêmico</h2>
      <form onSubmit={handleSubmit}>
        <label>Período Atual:</label>
        <input
          type="number"
          name="periodo_atual"
          value={perfil.periodo_atual}
          onChange={handleChange}
        />

        <label>IRA Geral:</label>
        <input
          type="number"
          step="0.01"
          name="ira_geral"
          value={perfil.ira_geral}
          onChange={handleChange}
        />

        <label>Interesses Principais:</label>
        <textarea
          name="interesses_principais"
          value={perfil.interesses_principais}
          onChange={handleChange}
        />

        <label>Habilidades:</label>
        <textarea
          name="habilidades"
          value={perfil.habilidades}
          onChange={handleChange}
        />

        <label>Objetivo de Carreira:</label>
        <textarea
          name="objetivo_carreira"
          value={perfil.objetivo_carreira}
          onChange={handleChange}
        />

        <button type="submit" style={{ marginTop: "1rem" }}>
          Salvar Perfil
        </button>
      </form>
    </div>
  );
}

export default PerfilAcademico;
