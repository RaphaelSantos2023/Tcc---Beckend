import React, { useState } from 'react';

function NovaPublicacao() {
  const [form, setForm] = useState({ titulo: '', conteudo: '', categoria: '' });
  const [msg, setMsg] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');

    const res = await fetch('http://localhost:5000/forum/publicar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(form),
    });

    const data = await res.json();
    if (res.ok) {
      setMsg('Publicação feita com sucesso!');
      setForm({ titulo: '', conteudo: '', categoria: '' });
    } else {
      setMsg(data.message || 'Erro ao publicar');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Nova Publicação</h3>
      <input
        type="text"
        name="titulo"
        placeholder="Título"
        value={form.titulo}
        onChange={handleChange}
        required
      />
      <input
        type="text"
        name="categoria"
        placeholder="Categoria (opcional)"
        value={form.categoria}
        onChange={handleChange}
      />
      <textarea
        name="conteudo"
        placeholder="Escreva sua mensagem..."
        value={form.conteudo}
        onChange={handleChange}
        required
      />
      <button type="submit">Publicar</button>
      <p>{msg}</p>
    </form>
  );
}

export default NovaPublicacao;
