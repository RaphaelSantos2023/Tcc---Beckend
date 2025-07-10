import React, { useState } from 'react';

function LoginForm() {
  const [form, setForm] = useState({ email: '', senha: '' });
  const [msg, setMsg] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    const res = await fetch('http://localhost:5000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });

    const data = await res.json();
    if (res.ok) {
      setMsg('Login bem-sucedido!');
      localStorage.setItem('token', data.token); // Salva o token
    } else {
      setMsg(data.message || 'Erro no login');
    }
  };

  return (
    <form onSubmit={handleLogin}>
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
      <button type="submit">Entrar</button>
      <p>{msg}</p>
    </form>
  );
}

export default LoginForm;
