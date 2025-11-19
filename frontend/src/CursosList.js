import React, { useEffect, useState } from 'react';

function CursosList() {
  const [cursos, setCursos] = useState([]);
  const [reload, setReload] = useState(false);
  const [mensagem, setMensagem] = useState('');
  const token = localStorage.getItem('token');
  const tipoUsuario = localStorage.getItem('tipo_usuario');

  useEffect(() => {
    fetch('http://localhost:5000/cursos', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        console.log("📥 [GET /cursos] Status:", res.status);
        return res.json();
      })
      .then((data) => {
        console.log("📦 Dados recebidos de /cursos:", data);
        setCursos(data.cursos || []);
      })
      .catch((err) => console.error("❌ Erro ao buscar cursos:", err));
  }, [token, reload]);   // recarrega sempre que reload mudar


  return (
    <div>
      <h2>Cursos Extracurriculares</h2>
      {mensagem && <p>{mensagem}</p>}
      {cursos.length === 0 ? (
        <p>Nenhum curso disponível.</p>
      ) : (
        <ul>
          {cursos.map((curso) => (
            <li key={curso.id_cursos} style={{ marginBottom: '10px' }}>
              <strong>{curso.nome}</strong> <br />
              {curso.descricao} <br />
              Carga horária: {curso.carga_horaria || 'N/A'}h <br />
              {curso.link_acesso && (
                <a href={curso.link_acesso} target="_blank" rel="noreferrer">
                  Acessar
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default CursosList;
