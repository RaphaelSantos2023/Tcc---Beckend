import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import Forum from './Forum';
import NovoForum from './NovoForum';
import GeminiChat from './GeminiChat';
import MateriaisList from './MateriaisList';
import UploadMaterial from './UploadMaterial';
import PerfilAcademico from './PerfilAcademico';
import RecomendacoesList from './RecomendacoesList';
import CursosList from './CursosList';
import GerenciarCursos from './GerenciarCursos';
import TemasTCC from './TemasTCC';


function App() {
  const [view, setView] = useState('login');
  const isLoggedIn = !!localStorage.getItem('token');
  const tipoUsuario = localStorage.getItem('tipo_usuario');

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '1rem' }}>
      {isLoggedIn ? (
        <>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              localStorage.removeItem('tipo_usuario');
              window.location.reload();
            }}
          >
            Logout
          </button>

          {(tipoUsuario === 'aluno' || tipoUsuario === 'professor') && <PerfilAcademico />}

          <NovoForum />
          <Forum />
          <TemasTCC />
          <CursosList />
          {tipoUsuario && tipoUsuario !== 'aluno' && <GerenciarCursos />}

          <GeminiChat />

          {/* 👇 Adiciona a listagem de recomendações */}
          <RecomendacoesList />

          {tipoUsuario && tipoUsuario !== 'aluno' && <UploadMaterial />}
          <MateriaisList />
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
