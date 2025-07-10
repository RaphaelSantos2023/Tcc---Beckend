import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

function App() {
  const [view, setView] = useState('login');

  return (
    <div style={{ maxWidth: '400px', margin: '0 auto', padding: '1rem' }}>
      <h1>{view === 'login' ? 'Login' : 'Cadastro'}</h1>
      {view === 'login' ? <LoginForm /> : <RegisterForm />}
      <button onClick={() => setView(view === 'login' ? 'register' : 'login')}>
        {view === 'login' ? 'Criar conta' : 'Já tem conta? Fazer login'}
      </button>
    </div>
  );
}

export default App;
