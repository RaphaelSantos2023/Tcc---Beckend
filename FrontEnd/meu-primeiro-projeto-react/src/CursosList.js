import React, { useEffect, useState } from 'react';

function CursosList() {
  const [cursos, setCursos] = useState([]);
  const [mensagem, setMensagem] = useState('');
  const token = localStorage.getItem('token');
  const tipoUsuario = localStorage.getItem('tipo_usuario');

  useEffect(() => {
    fetch('http://localhost:5000/cursos', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setCursos(data.cursos || []))
      .catch((err) => console.error(err));
  }, [token]);

  const inscrever = async (id_curso) => {
    try {
      const res = await fetch('http://localhost:5000/cursos/inscrever', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ id_curso }),
      });
      const data = await res.json();
      setMensagem(data.message || 'Erro ao se inscrever');
    } catch (error) {
      setMensagem('Erro ao se inscrever');
    }
  };

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
              {tipoUsuario === 'aluno' && (
                <button
                  onClick={() => inscrever(curso.id_cursos)}
                  style={{ marginTop: '5px', display: 'block' }}
                >
                  Inscrever-se
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default CursosList;
