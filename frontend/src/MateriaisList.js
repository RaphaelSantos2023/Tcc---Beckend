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
  const baixarArquivo = async (path) => {
    const res = await fetch(`http://localhost:5000/materiais/download/${path}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!res.ok) {
      alert("Erro ao baixar!");
      return;
    }

    // transforma resposta em blob (arquivo binário)
    const blob = await res.blob();

    // cria URL temporária
    const url = window.URL.createObjectURL(blob);

    // cria link invisível e clica
    const a = document.createElement("a");
    a.href = url;
    a.download = path.split("/").pop(); // usa o nome do arquivo
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
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
            <strong>{m.titulo}</strong> ({m.tipo_material}) <br />

            <button onClick={() => baixarArquivo(m.caminho_arquivo)}>
              Baixar arquivo
            </button>
          </li>
        ))}
      </ul>

    </div>
  );
}

export default MateriaisList;
