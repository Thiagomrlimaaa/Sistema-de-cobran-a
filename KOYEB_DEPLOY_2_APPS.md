# 🚀 Deploy no Koyeb - 2 Apps Separados

O Koyeb não permite rodar dois processos no mesmo container. Por isso, precisamos criar **2 apps separados**:

## 📋 Estrutura

### 🔵 App 1: Django (API + Dashboard)
- **Dockerfile**: `Dockerfile` (raiz do projeto)
- **Porta**: 8000
- **Função**: API Django, Dashboard, Admin

### 🟢 App 2: Bot WhatsApp (WPPConnect)
- **Dockerfile**: `Dockerfile.bot` (raiz do projeto)
- **Porta**: 3001
- **Função**: Bot WhatsApp via WPPConnect

## 🛠️ Configuração no Koyeb

### 1. Criar App Django

1. **Criar novo app no Koyeb**
2. **Conectar repositório GitHub**
3. **Configurar Dockerfile**: Usar `Dockerfile` (padrão)
4. **Root Directory**: Deixar vazio (raiz do projeto)
5. **Porta**: 8000

**Variáveis de Ambiente:**
```
DJANGO_SECRET_KEY=xxxx
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=seu-django.koyeb.app
DJANGO_API_URL=https://seu-django.koyeb.app/api
WPPCONNECT_BOT_URL=https://seu-bot.koyeb.app
DATABASE_URL=postgresql://... (se usar PostgreSQL)
```

### 2. Criar App Bot

1. **Criar novo app no Koyeb**
2. **Conectar mesmo repositório GitHub**
3. **Configurar Dockerfile**: Usar `Dockerfile.bot`
4. **Root Directory**: Deixar vazio (raiz do projeto)
5. **Porta**: 3001

**Variáveis de Ambiente:**
```
PORT=3001
BOT_PORT=3001
DJANGO_API_URL=https://seu-django.koyeb.app/api
WHATSAPP_SESSION=cobranca
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
```

**⚠️ IMPORTANTE:**
- O Koyeb usa a variável `PORT` para rotear o tráfego HTTP
- Defina `PORT=3001` no app do bot
- O bot usa `PORT` ou `BOT_PORT` (prioridade para `BOT_PORT`)

## 🔗 Comunicação entre Apps

- **Django → Bot**: `https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app`
- **Bot → Django**: `https://acute-crab-thiagocobrancas-328dda69.koyeb.app/api`

### URLs Configuradas:
- **App Django**: `https://acute-crab-thiagocobrancas-328dda69.koyeb.app`
- **App Bot**: `https://coastal-leonanie-thiagocobrancas-2843762c.koyeb.app`

## ✅ Resultado

- ✅ Django roda em app separado
- ✅ Bot roda em app separado
- ✅ Ambos ficam sempre online
- ✅ Sem timeouts
- ✅ QR Code funciona
- ✅ Mensagens enviam normalmente

## 📝 Notas

- Cada app tem seu próprio container
- Cada app pode escalar independentemente
- Logs separados para cada app
- Mais fácil de debugar e monitorar

