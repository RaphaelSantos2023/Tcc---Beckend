import React, { useEffect, useState } from 'react';

function GerenciarCursos() {
  const [cursos, setCursos] = useState([]);
  const [form, setForm] = useState({ nome: '', descricao: '', carga_horaria: '', link_acesso: '' });
  const token = localStorage.getItem('token');

  const carregarCursos = () => {
    fetch('http://localhost:5000/cursos', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setCursos(data.cursos || []));
  };

  useEffect(() => {
    carregarCursos();
  }, []);

  const criarCurso = async () => {
    await fetch('http://localhost:5000/cursos/criar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(form),
    });
    setForm({ nome: '', descricao: '', carga_horaria: '', link_acesso: '' });
    carregarCursos();
  };

  const deletarCurso = async (id) => {
    await fetch(`http://localhost:5000/cursos/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    carregarCursos();
  };

  return (
    <div>
      <h2>Gerenciar Cursos</h2>
      <input
        placeholder="Nome"
        value={form.nome}
        onChange={(e) => setForm({ ...form, nome: e.target.value })}
      />
      <textarea
        placeholder="Descrição"
        value={form.descricao}
        onChange={(e) => setForm({ ...form, descricao: e.target.value })}
      />
      <input
        placeholder="Carga Horária"
        value={form.carga_horaria}
        onChange={(e) => setForm({ ...form, carga_horaria: e.target.value })}
      />
      <input
        placeholder="Link de Acesso (opcional)"
        value={form.link_acesso}
        onChange={(e) => setForm({ ...form, link_acesso: e.target.value })}
      />
      <button onClick={criarCurso}>Criar Curso</button>

      <ul>
        {cursos.map((curso) => (
          <li key={curso.id_cursos}>
            <strong>{curso.nome}</strong> - {curso.descricao}
            <button onClick={() => deletarCurso(curso.id_cursos)}>Excluir</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default GerenciarCursos;
