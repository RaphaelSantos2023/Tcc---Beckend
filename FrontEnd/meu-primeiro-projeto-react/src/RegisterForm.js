import React, { useState } from 'react';

function RegisterForm() {
  const [form, setForm] = useState({
    email: '',
    senha: '',
    nome_completo: '',
    curso_atual: '',
    tipo_usuario: 'aluno',
    data_nascimento: '',
    genero: ''
  });

  const [msg, setMsg] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e) => {
    e.preventDefault();

    const res = await fetch('http://localhost:5000/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });

    const data = await res.json();
    if (res.ok) {
      setMsg('Cadastro realizado com sucesso!');
    } else {
      setMsg(data.message || 'Erro no cadastro');
    }
  };

  return (
    <form onSubmit={handleRegister}>
      <input
        type="text"
        name="nome_completo"
        placeholder="Nome completo"
        value={form.nome_completo}
        onChange={handleChange}
        required
      />
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={form.email}
        onChange={handleChange}
        required
      />
      <input
        type="password"
        name="senha"
        placeholder="Senha"
        value={form.senha}
        onChange={handleChange}
        required
      />
      <input
        type="text"
        name="curso_atual"
        placeholder="Curso atual"
        value={form.curso_atual}
        onChange={handleChange}
        required
      />
      <input
        type="date"
        name="data_nascimento"
        value={form.data_nascimento}
        onChange={handleChange}
        required
      />

      <select name="genero" value={form.genero} onChange={handleChange} required>
        <option value="">Selecione o gênero</option>
        <option value="masculino">Masculino</option>
        <option value="feminino">Feminino</option>
        <option value="outro">Outro</option>
      </select>

      <select name="tipo_usuario" value={form.tipo_usuario} onChange={handleChange}>
        <option value="aluno">Aluno</option>
        <option value="professor">Professor</option>
        <option value="admin">Admin</option>
      </select>
      <button type="submit">Cadastrar</button>
      <p>{msg}</p>
    </form>
  );
}

export default RegisterForm;
