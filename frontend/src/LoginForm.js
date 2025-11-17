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

      // 🔹 Salvar token
      localStorage.setItem('token', data.token);

      // 🔹 Salvar tipo do usuário (para condicional no frontend)
      localStorage.setItem('tipo_usuario', data.tipo_usuario);

      // 🔹 Atualiza a página ou dispara um estado global para renderizar componentes
      window.location.reload(); // ou você pode atualizar estado global se usar context/redux
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
