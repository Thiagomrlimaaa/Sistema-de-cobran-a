# 🚂 Deploy no Railway

Este projeto está configurado para rodar no Railway com Django e Bot WhatsApp no mesmo container.

## 📋 Configuração

### Variáveis de Ambiente no Railway

Configure as seguintes variáveis de ambiente no painel do Railway:

#### Django
- `DJANGO_SECRET_KEY` - Chave secreta do Django (gerar uma nova)
- `DJANGO_DEBUG` - `False` para produção
- `DJANGO_ALLOWED_HOSTS` - Domínio do Railway (ex: `seu-app.railway.app`)
- `DATABASE_URL` - URL do PostgreSQL (Railway fornece automaticamente se usar PostgreSQL)

#### Bot WhatsApp
- `BOT_PORT` - `3001` (porta interna do bot)
- `DJANGO_API_URL` - URL da API Django (ex: `https://seu-app.railway.app/api`)
- `WHATSAPP_SESSION` - Nome da sessão (padrão: `cobranca`)

#### Puppeteer (já configurado no Dockerfile)
- `PUPPETEER_EXECUTABLE_PATH` - `/usr/bin/chromium-browser` (já configurado)
- `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` - `true` (já configurado)

## 🚀 Deploy

1. **Conecte seu repositório GitHub ao Railway**
2. **Configure as variáveis de ambiente** no painel do Railway
3. **O Railway detectará automaticamente o Dockerfile**
4. **O build será executado automaticamente**

## 🔧 Como Funciona

1. **Dockerfile** instala:
   - Python 3.11
   - Node.js 18.x
   - Chromium-browser e todas as dependências

2. **start_both.sh** inicia:
   - Bot WhatsApp na porta 3001 (background)
   - Django/Gunicorn na porta definida por `PORT` (processo principal)

3. **Railway** usa a variável `PORT` para rotear tráfego HTTP para o Django

## ⚠️ Importante

- O Railway usa a variável `PORT` dinamicamente
- O Django será acessível na porta definida pelo Railway
- O bot roda internamente na porta 3001
- O Chromium está instalado e configurado automaticamente

## 📝 Notas

- O container roda 24/7 sem limitações no Railway
- Todos os processos rodam no mesmo container
- Logs estão disponíveis no painel do Railway

