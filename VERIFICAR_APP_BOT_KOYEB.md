# 🔍 Verificar App do Bot no Koyeb

## ❌ Problema: Django está processando requisições do bot

Se você está vendo erros do Django ao acessar `https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app/status`, significa que o **app do bot não está configurado corretamente** no Koyeb.

## ✅ Passos para Corrigir

### 1. Verificar se o App do Bot Existe

1. Acesse o [Dashboard do Koyeb](https://app.koyeb.com)
2. Verifique se existe um app separado para o bot (não o Django)
3. O app do bot deve ter um nome diferente do app Django

### 2. Verificar Configuração do Dockerfile

No app do bot no Koyeb:

1. Vá em **Settings** → **Build & Deploy**
2. Verifique o campo **Dockerfile Path**
3. Deve estar configurado como: `Dockerfile.bot`
4. **NÃO** deve estar como `Dockerfile` (isso é para Django)

### 3. Verificar Porta

No app do bot:

1. Vá em **Settings** → **Port**
2. Deve estar configurado como: `3001`
3. **NÃO** deve estar como `8000` (isso é para Django)

### 4. Verificar Variáveis de Ambiente

No app do bot, vá em **Settings** → **Environment Variables** e verifique:

```
PORT=3001
BOT_PORT=3001
DJANGO_API_URL=https://acute-crab-thiagocobrancas-328dda69.koyeb.app/api
WHATSAPP_SESSION=cobranca
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
```

### 5. Verificar Logs do App do Bot

1. No app do bot, vá em **Logs**
2. Procure por mensagens como:
   - `✅ Bot API rodando na porta 3001`
   - `✅ Escutando em 0.0.0.0:3001`
   - `📋 Endpoints disponíveis:`
3. Se não aparecer essas mensagens, o bot não está rodando

### 6. Fazer Redeploy

Se algo estiver errado:

1. No app do bot, vá em **Settings** → **Build & Deploy**
2. Clique em **Redeploy**
3. Aguarde o build e deploy completarem
4. Verifique os logs novamente

## 🎯 Configuração Correta

### App Django
- **Dockerfile**: `Dockerfile` (padrão)
- **Porta**: `8000`
- **URL**: `https://acute-crab-thiagocobrancas-328dda69.koyeb.app`

### App Bot
- **Dockerfile**: `Dockerfile.bot`
- **Porta**: `3001`
- **URL**: `https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app`

## ⚠️ Se o App do Bot Não Existe

Se você não criou um app separado para o bot:

1. No Koyeb, clique em **Create App**
2. Conecte o mesmo repositório GitHub
3. Configure:
   - **Dockerfile Path**: `Dockerfile.bot`
   - **Port**: `3001`
   - **Root Directory**: (deixe vazio)
4. Adicione as variáveis de ambiente listadas acima
5. Faça o deploy

## 🧪 Teste

Após configurar corretamente, teste:

```
https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app/status
```

**Deve retornar JSON** (não erro do Django):
```json
{
  "status": "disconnected",
  "qrCode": null,
  "error": null,
  "connectedAt": null,
  "isConnected": false
}
```

