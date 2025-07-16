import React, { useEffect, useState } from 'react';

function Forum() {
  const [posts, setPosts] = useState([]);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    const fetchPosts = async () => {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/forum/publicacoes', {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (res.ok) {
        setPosts(data.publicacoes);
      } else {
        setMsg(data.message || 'Erro ao carregar fórum');
      }
    };

    fetchPosts();
  }, []);

  return (
    <div>
      <h2>Fórum</h2>
      {msg && <p>{msg}</p>}
      {posts.map((post) => (
        <div key={post.id_publicacao} style={{ border: '1px solid #ccc', margin: '1rem 0', padding: '1rem' }}>
          <h3>{post.titulo}</h3>
          <p><strong>Categoria:</strong> {post.categoria || 'Geral'}</p>
          <p>{post.conteudo}</p>
          <small>Postado por {post.autor} em {new Date(post.data_criacao).toLocaleString()}</small>
        </div>
      ))}
    </div>
  );
}

export default Forum;
