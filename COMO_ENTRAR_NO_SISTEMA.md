# 🚪 Como Entrar no Sistema

## 📋 Passo a Passo Completo

### 1️⃣ Instalar Dependências do Django (se ainda não instalou)

```bash
cd "C:\Users\AVELL\Documents\chatbot - cobrança"
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2️⃣ Configurar o Banco de Dados

```bash
venv\Scripts\python.exe manage.py migrate
```

### 3️⃣ Criar Usuários de Acesso

```bash
venv\Scripts\python.exe manage.py create_users
```

Isso criará os usuários:
- **jeff** / senha: **1**
- **thiago** / senha: **1**

### 4️⃣ Iniciar o Sistema

Você precisa ter **2 terminais abertos**:

#### Terminal 1 - Django (Interface Web):
```bash
cd "C:\Users\AVELL\Documents\chatbot - cobrança"
venv\Scripts\python.exe manage.py runserver
```

#### Terminal 2 - Bot WhatsApp:
```bash
cd "C:\Users\AVELL\Documents\chatbot - cobrança\cobranca-bot"
npm start
```

### 5️⃣ Acessar o Sistema

1. Abra seu navegador
2. Acesse: **http://localhost:8000**
3. Faça login com:
   - **Usuário:** `jeff` ou `thiago`
   - **Senha:** `1`

### 6️⃣ Conectar o WhatsApp

1. Após fazer login, vá em **"WhatsApp Bot"** no menu
2. Clique em **"Iniciar Bot"**
3. O QR Code aparecerá na tela
4. Escaneie com seu WhatsApp
5. Pronto! ✅

## 📱 Endpoints Disponíveis

- **Interface Web:** http://localhost:8000
- **API Django:** http://localhost:8000/api
- **Bot API:** http://localhost:3001

## ⚠️ Importante

- **Mantenha os 2 terminais abertos** enquanto usar o sistema
- O Django deve estar rodando na porta **8000**
- O Bot deve estar rodando na porta **3001**
- Na primeira vez, você precisará escanear o QR Code
- Após escanear, o bot fica conectado automaticamente

## 🐛 Problemas Comuns

**Erro: "Não foi possível conectar ao bot"**
- Verifique se o bot está rodando (Terminal 2)
- Confirme que está na porta 3001
- Verifique se o arquivo `.env` na pasta `cobranca-bot` está configurado

**QR Code não aparece**
- Clique em "Iniciar Bot" primeiro
- Aguarde alguns segundos
- Clique em "Atualizar Status"

**Erro ao fazer login**
- Verifique se os usuários foram criados: `venv\Scripts\python.exe manage.py create_users`
- Verifique se as migrations foram aplicadas: `venv\Scripts\python.exe manage.py migrate`

## 🎯 Resumo Rápido

```bash
# Terminal 1 - Django
venv\Scripts\python.exe manage.py runserver

# Terminal 2 - Bot
cd cobranca-bot
npm start

# Acesse: http://localhost:8000
# Login: jeff / 1
```

