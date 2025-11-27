# ⚙️ Configurar Variáveis de Ambiente no Koyeb

## 🔴 Problema Atual

O Django está tentando conectar em `localhost:3001` em vez da URL do bot no Koyeb.

## ✅ Solução

### 1. App Django (acute-crab-thiagocobrancas-328dda69.koyeb.app)

Vá em **Settings** → **Environment Variables** e adicione/verifique:

```
WPPCONNECT_BOT_URL=https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app
```

**⚠️ IMPORTANTE:**
- **SEM** `http://` ou `https://` no final
- **SEM** porta (`:3001`)
- **SEM** barra no final (`/`)

### 2. App Bot (coastal-leonanie-thiagocobrancas-2843762c.koyeb.app)

Vá em **Settings** → **Environment Variables** e adicione/verifique:

```
PORT=3001
BOT_PORT=3001
DJANGO_API_URL=https://acute-crab-thiagocobrancas-328dda69.koyeb.app/api
WHATSAPP_SESSION=cobranca
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
```

## 📋 Checklist Completo

### App Django
- [ ] `WPPCONNECT_BOT_URL=https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app`
- [ ] `DJANGO_SECRET_KEY=xxxx` (se necessário)
- [ ] `DJANGO_DEBUG=False`
- [ ] `DATABASE_URL=xxxx` (se usar PostgreSQL)

### App Bot
- [ ] `PORT=3001`
- [ ] `BOT_PORT=3001`
- [ ] `DJANGO_API_URL=https://acute-crab-thiagocobrancas-328dda69.koyeb.app/api`
- [ ] `WHATSAPP_SESSION=cobranca`
- [ ] `PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium`
- [ ] `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true`

## 🧪 Teste

Após configurar:

1. **Teste o bot diretamente:**
   ```
   https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app/status
   ```
   Deve retornar JSON (não erro 404 do Django)

2. **Teste pelo Django:**
   - Acesse o dashboard
   - Vá em "WhatsApp Bot"
   - Clique em "Iniciar Bot"
   - Deve funcionar sem erros

## 🔍 Verificar Logs

Se ainda não funcionar:

1. **Logs do Bot:**
   - No app do bot, vá em **Logs**
   - Procure por: `✅ Bot API rodando na porta 3001`
   - Se não aparecer, o bot não está rodando

2. **Logs do Django:**
   - No app Django, vá em **Logs**
   - Procure por erros de conexão
   - Verifique se está usando a URL correta do bot

