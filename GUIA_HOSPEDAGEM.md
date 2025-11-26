# 🚀 Guia de Hospedagem Gratuita - Chatbot de Cobrança

## 📋 Opções de Hospedagem Gratuita

### 1. **Render.com** ⭐ (Recomendado)
- **Gratuito**: Sim (com limitações)
- **Suporta**: Django + Node.js
- **URL**: https://render.com
- **Vantagens**:
  - Fácil configuração via GitHub
  - Suporta múltiplos serviços (web + worker)
  - SSL gratuito
  - Deploy automático
- **Limitações**:
  - Serviços gratuitos "dormem" após 15min de inatividade
  - 750 horas/mês gratuitas

**Como configurar:**
1. Crie conta no Render.com
2. Conecte seu repositório GitHub
3. Crie 2 serviços:
   - **Web Service**: Django (Python)
   - **Background Worker**: Bot Node.js
4. Configure variáveis de ambiente

---

### 2. **Railway.app** ⭐
- **Gratuito**: Sim (com créditos mensais)
- **Suporta**: Django + Node.js
- **URL**: https://railway.app
- **Vantagens**:
  - $5 créditos gratuitos/mês
  - Deploy muito rápido
  - Suporta PostgreSQL gratuito
- **Limitações**:
  - Créditos limitados

---

### 3. **Fly.io**
- **Gratuito**: Sim
- **Suporta**: Django + Node.js
- **URL**: https://fly.io
- **Vantagens**:
  - 3 VMs gratuitas
  - Sem dormência
  - Globalmente distribuído

---

### 4. **Heroku** (Alternativa)
- **Gratuito**: Não mais (removido em 2022)
- **Alternativa paga**: A partir de $7/mês

---

### 5. **VPS Gratuito** (Limitado)
- **Oracle Cloud Free Tier**
  - 2 VMs sempre gratuitas
  - 200GB de armazenamento
  - Requer cartão de crédito (não cobra)
- **Google Cloud Free Tier**
  - $300 créditos por 90 dias
  - Depois pode ter custos

---

## 🛠️ Configuração para Render.com (Recomendado)

### Passo 1: Preparar o Projeto

1. **Criar arquivo `render.yaml`** na raiz do projeto:

```yaml
services:
  - type: web
    name: django-server
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: python manage.py runserver 0.0.0.0:$PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: WPPCONNECT_BOT_URL
        value: https://whatsapp-bot.onrender.com
      - key: DJANGO_API_URL
        value: https://django-server.onrender.com/api

  - type: worker
    name: whatsapp-bot
    env: node
    buildCommand: cd cobranca-bot && npm install
    startCommand: cd cobranca-bot && npm start
    envVars:
      - key: DJANGO_API_URL
        fromService:
          type: web
          name: django-server
          property: url
      - key: WHATSAPP_SESSION
        value: cobranca
      - key: BOT_PORT
        value: 3001
```

### Passo 2: Criar `Procfile` (alternativa)

**Para Django:**
```
web: python manage.py runserver 0.0.0.0:$PORT
```

**Para Bot (cobranca-bot/Procfile):**
```
worker: npm start
```

### Passo 3: Configurar Variáveis de Ambiente

No painel do Render, adicione:
- `SECRET_KEY` (gere uma chave secreta)
- `DATABASE_URL` (se usar banco externo)
- `WPPCONNECT_BOT_URL` (URL do bot)
- `DJANGO_API_URL` (URL do Django)

### Passo 4: Deploy

1. Faça push para GitHub
2. Conecte no Render.com
3. Crie os 2 serviços conforme `render.yaml`
4. Aguarde o deploy

---

## 🛠️ Configuração para Railway.app

### Passo 1: Criar `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py runserver 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Passo 2: Deploy

1. Conecte GitHub
2. Railway detecta automaticamente
3. Configure variáveis de ambiente
4. Deploy automático

---

## 📝 Checklist de Deploy

- [ ] Projeto no GitHub
- [ ] `requirements.txt` atualizado
- [ ] `package.json` no `cobranca-bot/`
- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados configurado (SQLite para testes, PostgreSQL para produção)
- [ ] `ALLOWED_HOSTS` configurado no `settings.py`
- [ ] `DEBUG=False` em produção
- [ ] Migrations aplicadas

---

## ⚠️ Importante

1. **WhatsApp Web**: O bot precisa manter a sessão ativa. Em serviços gratuitos que "dormem", você precisará escanear o QR Code novamente após inatividade.

2. **Banco de Dados**: 
   - SQLite funciona para testes
   - Para produção, use PostgreSQL (Render oferece gratuito)

3. **Portas**: 
   - Django: Use variável `$PORT` (Render/Railway definem automaticamente)
   - Bot: Configure `BOT_PORT` nas variáveis de ambiente

4. **SSL**: Render e Railway fornecem SSL automático

---

## 🔧 Scripts Locais vs Produção

**Local (Windows):**
- Use `start_all.bat` para iniciar tudo

**Produção (Render/Railway):**
- Os serviços iniciam automaticamente
- Configure via `render.yaml` ou painel

---

## 📞 Suporte

Para dúvidas sobre deploy, consulte:
- Documentação Render: https://render.com/docs
- Documentação Railway: https://docs.railway.app

