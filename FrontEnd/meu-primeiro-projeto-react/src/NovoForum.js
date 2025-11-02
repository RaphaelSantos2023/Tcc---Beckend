import React, { useState } from 'react';

function NovoForum() {
  const [nome, setNome] = useState('');
  const [descricao, setDescricao] = useState('');
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    if (!token) {
      setMsg('Você precisa estar logado para criar um fórum.');
      return;
    }

    try {
      const res = await fetch('http://localhost:5000/forum/criar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ nome, descricao })
      });

      const data = await res.json();

      if (res.ok) {
        setMsg('Fórum criado com sucesso!');
        setNome('');
        setDescricao('');
      } else {
        setMsg(data.message || 'Erro ao criar fórum');
      }
    } catch (error) {
      console.error(error);
      setMsg('Erro de rede ao criar fórum.');
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', marginBottom: '1rem' }}>
      <h3>Criar Novo Fórum</h3>
      {msg && <p>{msg}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Nome do Fórum:</label><br />
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem' }}
          />
        </div>
        <div>
          <label>Descrição:</label><br />
          <textarea
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem' }}
          />
        </div>
        <button type="submit" style={{ padding: '0.5rem 1rem' }}>Criar Fórum</button>
      </form>
    </div>
  );
}

export default NovoForum;
