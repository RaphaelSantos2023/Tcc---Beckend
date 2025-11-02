import React, { useEffect, useState } from 'react';
import NovaPublicacao from './NovaPublicacao';

function Forum() {
  const [foruns, setForuns] = useState([]);
  const [forumSelecionado, setForumSelecionado] = useState(null);
  const [posts, setPosts] = useState([]);
  const [msg, setMsg] = useState('');

  // 🔹 1. Buscar todos os fóruns ao carregar
  useEffect(() => {
    const fetchForuns = async () => {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/forum', {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (res.ok) {
        setForuns(data.foruns);
        if (data.foruns.length > 0) {
          setForumSelecionado(data.foruns[0].id_forum); // seleciona o primeiro por padrão
        }
      } else {
        setMsg(data.message || 'Erro ao carregar fóruns');
      }
    };

    fetchForuns();
  }, []);

  // 🔹 2. Buscar publicações do fórum selecionado
  useEffect(() => {
    if (!forumSelecionado) return;

    const fetchPosts = async () => {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:5000/forum/${forumSelecionado}/publicacoes`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (res.ok) {
        setPosts(data.publicacoes);
        setMsg('');
      } else {
        setMsg(data.message || 'Erro ao carregar publicações');
      }
    };

    fetchPosts();
  }, [forumSelecionado]);

  return (
    <div>
      <h2>Fóruns</h2>
      {msg && <p>{msg}</p>}

      {/* 🔸 Menu de seleção de fórum */}
      <select
        value={forumSelecionado || ''}
        onChange={(e) => setForumSelecionado(e.target.value)}
        style={{ marginBottom: '1rem', padding: '0.5rem' }}
      >
        {foruns.map((forum) => (
          <option key={forum.id_forum} value={forum.id_forum}>
            {forum.nome}
          </option>
        ))}
      </select>

      {/* 🔸 Lista de posts */}
      <div>
        {posts.length === 0 ? (
          <p>Nenhuma publicação ainda neste fórum.</p>
        ) : (
          posts.map((post) => (
            <div
              key={post.id_publicacao}
              style={{ border: '1px solid #ccc', margin: '1rem 0', padding: '1rem' }}
            >
              <h3>{post.titulo}</h3>
              <p><strong>Categoria:</strong> {post.categoria || 'Geral'}</p>
              <p>{post.conteudo}</p>
              <small>
                Postado por {post.autor} em {new Date(post.data_criacao).toLocaleString()}
              </small>
            </div>
          ))
        )}
      </div>

      {/* Publicacao */}
      <NovaPublicacao forumId={forumSelecionado} />
    </div>
  );
}

export default Forum;
