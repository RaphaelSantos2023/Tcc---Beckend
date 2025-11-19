import React, { useEffect, useState } from 'react';

function GerenciarCursos() {
  const [cursos, setCursos] = useState([]);
  const [form, setForm] = useState({ nome: '', descricao: '', carga_horaria: '', link_acesso: '' });
  const token = localStorage.getItem('token');
  const [msg, setMsg] = useState('');

  const carregarCursos = () => {
    fetch('http://localhost:5000/cursos', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("📥 Dados recebidos do servidor (GET /cursos):", data); // LOG AQUI
        setCursos(data.cursos || []);
      })
      .catch((err) => console.error("❌ Erro ao carregar cursos:", err));
  };

  useEffect(() => {
    carregarCursos();
  }, []);

  const criarCurso = async () => {
    try {
      const res = await fetch('http://localhost:5000/cursos/criar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });

      const data = await res.json();
      console.log("🟢 Resposta do servidor (POST /cursos/criar):", data); // LOG AQUI

      setForm({ nome: '', descricao: '', carga_horaria: '', link_acesso: '' });
      setMsg(data.message || 'Erro no cadastro');
      carregarCursos();
    } catch (error) {
      console.error("❌ Erro ao criar curso:", error);
    }
  };

  const deletarCurso = async (id) => {
    try {
      const res = await fetch(`http://localhost:5000/cursos/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      console.log(`🗑️ Resposta do servidor (DELETE /cursos/${id}):`, data); // LOG AQUI

      carregarCursos();
    } catch (error) {
      console.error("❌ Erro ao deletar curso:", error);
    }
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
      <p>{msg}</p>

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
