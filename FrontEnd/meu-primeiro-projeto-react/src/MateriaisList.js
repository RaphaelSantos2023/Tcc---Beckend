import React, { useState, useEffect } from 'react';

function MateriaisList() {
  const [materiais, setMateriais] = useState([]);
  const [query, setQuery] = useState('');
  const [msg, setMsg] = useState('');

  const token = localStorage.getItem('token');

  const buscarMateriais = async (search = '') => {
    try {
      const res = await fetch(`http://localhost:5000/materiais/buscar?query=${encodeURIComponent(search)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setMateriais(data.materiais || []);
      if (data.materiais.length === 0) setMsg('Nenhum material encontrado.');
      else setMsg('');
    } catch (err) {
      setMsg('Erro ao buscar materiais.');
    }
  };

  useEffect(() => {
    buscarMateriais();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    buscarMateriais(query);
  };

  return (
    <div>
      <h3>Materiais</h3>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Pesquisar por título ou assunto"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Buscar</button>
      </form>
      <p>{msg}</p>
      <ul>
        {materiais.map((m) => (
          <li key={m.id_material}>
            <strong>{m.titulo}</strong> ({m.assunto}) - {m.descricao}<br />
            <em>Autor: {m.autor}</em><br />
            <a 
            href={`http://localhost:5000/uploads/${m.caminho_arquivo.split('/').pop()}`} 
            target="_blank" 
            rel="noreferrer"
            >
            Abrir arquivo
            </a>

          </li>
        ))}
      </ul>
    </div>
  );
}

export default MateriaisList;
