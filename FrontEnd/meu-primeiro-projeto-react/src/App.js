import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import Forum from './Forum';
import NovaPublicacao from './NovaPublicacao';

function App() {
  const [view, setView] = useState('login');

  const isLoggedIn = !!localStorage.getItem('token');

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '1rem' }}>
      {isLoggedIn ? (
        <>
          <button onClick={() => { localStorage.removeItem('token'); window.location.reload(); }}>
            Logout
          </button>
          <NovaPublicacao />
          <Forum />
        </>
      ) : (
        <>
          <h1>{view === 'login' ? 'Login' : 'Cadastro'}</h1>
          {view === 'login' ? <LoginForm /> : <RegisterForm />}
          <button onClick={() => setView(view === 'login' ? 'register' : 'login')}>
            {view === 'login' ? 'Criar conta' : 'Já tem conta? Fazer login'}
          </button>
        </>
      )}
    </div>
  );
}

export default App;
