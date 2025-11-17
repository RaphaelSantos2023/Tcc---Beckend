import React, { useState } from 'react';

function RegisterForm() {
  const [form, setForm] = useState({
    email: '',
    senha: '',
    nome_completo: '',
    curso_atual: '',
    tipo_usuario: 'aluno',
    data_nascimento: '',
    genero: '',
    // parceiro
    tipo_parceiro: '',
    nome_fantasia: '',
    razao_social: '',
    cnpj: '',
    // endereço
    endereco: {
      cep: '',
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      estado: '',
      pais: 'Brasil',
      tipo_endereco: 'residencial'
    }
  });

  const [msg, setMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;

    // Campos de endereço
    if (name.startsWith('endereco.')) {
      const field = name.split('.')[1];
      setForm((prevForm) => ({
        ...prevForm,
        endereco: { ...prevForm.endereco, [field]: value }
      }));
    } else {
      setForm({ ...form, [name]: value });
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();

    const dataToSend = { ...form };

    // Remove dados não obrigatórios se não forem necessários
    if (form.tipo_usuario !== 'parceiro') {
      delete dataToSend.tipo_parceiro;
      delete dataToSend.nome_fantasia;
      delete dataToSend.razao_social;
      delete dataToSend.cnpj;
    }

    // Remove endereço se campos obrigatórios estiverem vazios
    const { cep, logradouro, numero, bairro, cidade, estado } = form.endereco;
    if (!cep || !logradouro || !numero || !bairro || !cidade || !estado) {
      delete dataToSend.endereco;
    }

    const res = await fetch('http://localhost:5000/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dataToSend),
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
      <h2>Cadastro</h2>

      <input type="text" name="nome_completo" placeholder="Nome completo" value={form.nome_completo} onChange={handleChange} required />
      <input type="email" name="email" placeholder="Email" value={form.email} onChange={handleChange} required />
      <input type="password" name="senha" placeholder="Senha" value={form.senha} onChange={handleChange} required />
      <input type="date" name="data_nascimento" value={form.data_nascimento} onChange={handleChange} required />

      <select name="genero" value={form.genero} onChange={handleChange} required>
        <option value="">Selecione o gênero</option>
        <option value="masculino">Masculino</option>
        <option value="feminino">Feminino</option>
        <option value="outro">Outro</option>
      </select>

      <select name="tipo_usuario" value={form.tipo_usuario} onChange={handleChange}>
        <option value="aluno">Aluno</option>
        <option value="professor">Professor</option>
        <option value="parceiro">Parceiro (Empresa/Faculdade)</option>
        <option value="admin">Admin</option>
      </select>

      {(form.tipo_usuario === 'aluno' || form.tipo_usuario === 'professor') && (
        <input type="text" name="curso_atual" placeholder="Curso atual" value={form.curso_atual} onChange={handleChange} required />
      )}

      {form.tipo_usuario === 'professor' && (
        <>
          <input
            type="text"
            name="formacao"
            placeholder="Formação"
            value={form.formacao}
            onChange={handleChange}
            required
          />
          <input
            type="text"
            name="area_atuacao"
            placeholder="Área de Atuação"
            value={form.area_atuacao}
            onChange={handleChange}
            required
          />
          <input
            type="number"
            name="tempo_experiencia"
            placeholder="Tempo de experiência (anos)"
            value={form.tempo_experiencia}
            onChange={handleChange}
            required
          />
        </>
      )}

      {/* Dados de parceiro */}
      {form.tipo_usuario === 'parceiro' && (
        <>
          <select name="tipo_parceiro" value={form.tipo_parceiro} onChange={handleChange} required>
            <option value="">Tipo de parceiro</option>
            <option value="empresa">Empresa</option>
            <option value="faculdade">Faculdade</option>
          </select>
          <input type="text" name="nome_fantasia" placeholder="Nome Fantasia" value={form.nome_fantasia} onChange={handleChange} required />
          <input type="text" name="razao_social" placeholder="Razão Social" value={form.razao_social} onChange={handleChange} required />
          <input type="text" name="cnpj" placeholder="CNPJ" value={form.cnpj} onChange={handleChange} required />
          <input
            type="text"
            name="telefone"
            placeholder="Telefone"
            value={form.telefone}
            onChange={handleChange}
          />
          <input
            type="text"
            name="site"
            placeholder="Site"
            value={form.site}
            onChange={handleChange}
          />
          <input
            type="email"
            name="email_parceiro"
            placeholder="Email do parceiro (opcional)"
            value={form.email_parceiro}
            onChange={handleChange}
          />

        </>
      )}

      {/* Endereço */}
      <h3>Endereço</h3>
      <input type="text" name="endereco.cep" placeholder="CEP" value={form.endereco.cep} onChange={handleChange} required />
      <input type="text" name="endereco.logradouro" placeholder="Logradouro" value={form.endereco.logradouro} onChange={handleChange} required />
      <input type="text" name="endereco.numero" placeholder="Número" value={form.endereco.numero} onChange={handleChange} required />
      <input type="text" name="endereco.complemento" placeholder="Complemento (opcional)" value={form.endereco.complemento} onChange={handleChange} />
      <input type="text" name="endereco.bairro" placeholder="Bairro" value={form.endereco.bairro} onChange={handleChange} required />
      <input type="text" name="endereco.cidade" placeholder="Cidade" value={form.endereco.cidade} onChange={handleChange} required />
      <select name="endereco.estado" value={form.endereco.estado} onChange={handleChange} required>
        <option value="">UF</option>
        <option value="AC">AC</option>
        <option value="AL">AL</option>
        <option value="AP">AP</option>
        <option value="AM">AM</option>
        <option value="BA">BA</option>
        <option value="CE">CE</option>
        <option value="DF">DF</option>
        <option value="ES">ES</option>
        <option value="GO">GO</option>
        <option value="MA">MA</option>
        <option value="MT">MT</option>
        <option value="MS">MS</option>
        <option value="MG">MG</option>
        <option value="PA">PA</option>
        <option value="PB">PB</option>
        <option value="PR">PR</option>
        <option value="PE">PE</option>
        <option value="PI">PI</option>
        <option value="RJ">RJ</option>
        <option value="RN">RN</option>
        <option value="RS">RS</option>
        <option value="RO">RO</option>
        <option value="RR">RR</option>
        <option value="SC">SC</option>
        <option value="SP">SP</option>
        <option value="SE">SE</option>
        <option value="TO">TO</option>
      </select>

      <input type="text" name="endereco.pais" placeholder="País" value={form.endereco.pais} onChange={handleChange} />
      <select name="endereco.tipo_endereco" value={form.endereco.tipo_endereco} onChange={handleChange}>
        <option value="residencial">Residencial</option>
        <option value="comercial">Comercial</option>
        <option value="outro">Outro</option>
      </select>

      <button type="submit">Cadastrar</button>
      <p>{msg}</p>
    </form>
  );
}

export default RegisterForm;
