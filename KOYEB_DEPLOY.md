# 🚀 Deploy no Koyeb

Este projeto está configurado para rodar no Koyeb com Django e Bot WhatsApp no mesmo container.

## 📋 Configuração

### Variáveis de Ambiente no Koyeb

Configure as seguintes variáveis de ambiente no painel do Koyeb:

#### Django
- `DJANGO_SECRET_KEY` - Chave secreta do Django (gerar uma nova)
- `DJANGO_DEBUG` - `False` para produção
- `DJANGO_ALLOWED_HOSTS` - `*` (ou domínio específico do Koyeb) - **Opcional**: já configurado automaticamente
- `DJANGO_API_URL` - URL da API Django (ex: `https://seu-servico.koyeb.app/api`)
- `KOYEB_APP_URL` - URL completa do app no Koyeb (ex: `https://seu-app.koyeb.app`) - **Opcional**: CSRF já configurado automaticamente

#### Bot WhatsApp
- `WHATSAPP_SESSION` - Nome da sessão (padrão: `cobranca`)
- `BOT_PORT` - `3001` (porta interna do bot)
- `PUPPETEER_EXECUTABLE_PATH` - `/usr/bin/chromium` (já configurado no Dockerfile)
- `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` - `true` (já configurado no Dockerfile)

#### Database (opcional)
- `DATABASE_URL` - URL do PostgreSQL se usar banco externo

## 🚀 Deploy

1. **Conecte seu repositório GitHub ao Koyeb**
2. **Configure as variáveis de ambiente** no painel do Koyeb
3. **O Koyeb detectará automaticamente o Dockerfile**
4. **O build será executado automaticamente**

## 🔧 Como Funciona

1. **Dockerfile** instala:
   - Python 3.11
   - Node.js 18.x
   - Chromium e todas as dependências necessárias

2. **start.sh** (criado no Dockerfile) executa:
   - `python manage.py migrate` - Aplica migrações
   - `python manage.py collectstatic --noinput` - Coleta arquivos estáticos
   - `node cobranca-bot/index.js &` - Inicia bot em background
   - `python manage.py runserver 0.0.0.0:8000` - Inicia Django (processo principal)

3. **Koyeb** roteia tráfego HTTP para a porta 8000 (Django)

## ⚠️ Importante

- O Django roda na porta 8000 (processo principal)
- O bot roda na porta 3001 (background)
- O Chromium está instalado e configurado automaticamente
- O container roda 24/7 sem limitações no Koyeb
- **CSRF está configurado automaticamente** para o domínio do Koyeb (não precisa configurar manualmente)

## 📝 Notas

- Todos os processos rodam no mesmo container
- Logs estão disponíveis no painel do Koyeb
- O serviço fica sempre online (sem hibernação)
- Compatível com WPPConnect + Puppeteer

