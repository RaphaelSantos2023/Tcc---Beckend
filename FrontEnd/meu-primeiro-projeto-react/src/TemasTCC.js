import React, { useState, useEffect } from 'react';

function TemasTCC() {
  const [temas, setTemas] = useState([]);
  const [form, setForm] = useState({ titulo: '', descricao: '', area_conhecimento: '' });
  const token = localStorage.getItem('token');
  const tipoUsuario = localStorage.getItem('tipo_usuario');

  useEffect(() => {
    fetch('http://localhost:5000/temas', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setTemas(data.temas || []));
  }, [token]);

  const criarTema = async () => {
    await fetch('http://localhost:5000/temas/criar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(form),
    });
    setForm({ titulo: '', descricao: '', area_conhecimento: '' });
    window.location.reload();
  };

  return (
    <div>
      <h2>Temas de TCC</h2>

      {(tipoUsuario === 'professor' || tipoUsuario === 'parceiro' || tipoUsuario === 'admin') && (
        <>
          <input
            placeholder="Título"
            value={form.titulo}
            onChange={(e) => setForm({ ...form, titulo: e.target.value })}
          />
          <textarea
            placeholder="Descrição"
            value={form.descricao}
            onChange={(e) => setForm({ ...form, descricao: e.target.value })}
          />
          <input
            placeholder="Área de conhecimento"
            value={form.area_conhecimento}
            onChange={(e) => setForm({ ...form, area_conhecimento: e.target.value })}
          />
          <button onClick={criarTema}>Criar Tema</button>
        </>
      )}

      <ul>
        {temas.map((t) => (
          <li key={t.id_tema}>
            <strong>{t.titulo}</strong> — {t.area_conhecimento} <br />
            {t.descricao} <br />
            <em>Criado por: {t.criado_por}</em>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default TemasTCC;
