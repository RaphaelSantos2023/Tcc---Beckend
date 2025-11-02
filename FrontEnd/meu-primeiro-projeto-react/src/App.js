import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import Forum from './Forum';
import NovoForum from './NovoForum';
import GeminiChat from './GeminiChat';
import MateriaisList from './MateriaisList';
import UploadMaterial from './UploadMaterial'; // 👈 import

function App() {
  const [view, setView] = useState('login');
  const isLoggedIn = !!localStorage.getItem('token');
  const tipoUsuario = localStorage.getItem('tipo_usuario'); // 👈 pega tipo

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '1rem' }}>
      {isLoggedIn ? (
        <>
          <button onClick={() => { 
            localStorage.removeItem('token'); 
            localStorage.removeItem('tipo_usuario'); 
            window.location.reload(); 
          }}>
            Logout
          </button>

          <NovoForum />
          <Forum />
          <GeminiChat />

          {/* 👇 Renderiza apenas se não for aluno */}
          {tipoUsuario && tipoUsuario !== 'aluno' && <UploadMaterial />}
          <MateriaisList/>
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
