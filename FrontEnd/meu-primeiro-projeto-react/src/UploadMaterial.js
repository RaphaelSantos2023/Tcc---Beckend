import React, { useState } from 'react';

function UploadMaterial() {
  const [arquivo, setArquivo] = useState(null);
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [assunto, setAssunto] = useState(''); // 🔹 novo estado
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');

    const formData = new FormData();
    formData.append('arquivo', arquivo);
    formData.append('titulo', titulo);
    formData.append('descricao', descricao);
    formData.append('tipo', assunto); // 🔹 enviar assunto

    const res = await fetch('http://localhost:5000/materiais/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    const data = await res.json();
    setMsg(data.message);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Enviar Material</h3>
      <input type="text" placeholder="Título" value={titulo} onChange={e => setTitulo(e.target.value)} required />
      <input type="text" placeholder="Assunto" value={assunto} onChange={e => setAssunto(e.target.value)} /> {/* 🔹 novo input */}
      <textarea placeholder="Descrição" value={descricao} onChange={e => setDescricao(e.target.value)} />
      <input type="file" onChange={e => setArquivo(e.target.files[0])} required />
      <button type="submit">Enviar</button>
      <p>{msg}</p>
    </form>
  );
}

export default UploadMaterial;
