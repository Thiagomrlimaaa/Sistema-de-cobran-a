# Configuração para Ambiente LOCAL

Este bot foi configurado para rodar **somente localmente**.

## Pré-requisitos

1. **Node.js** (versão 18 ou superior)
2. **Chrome/Chromium** instalado no sistema OU o Puppeteer irá baixar automaticamente

## Instalação

1. Instale as dependências:
```bash
cd cobranca-bot
npm install
```

2. (Opcional) Se o Chrome não for encontrado automaticamente, instale via Puppeteer:
```bash
npx puppeteer browsers install chrome
```

## Configuração

Crie um arquivo `.env` na pasta `cobranca-bot` com as seguintes variáveis (opcionais):

```env
# URL da API Django (padrão: http://localhost:8000/api)
DJANGO_API_URL=http://localhost:8000/api

# Nome da sessão do WhatsApp (padrão: cobranca)
WHATSAPP_SESSION=cobranca

# Porta do bot (padrão: 3001)
BOT_PORT=3001

# Caminho do Chrome/Chromium (opcional - deixe vazio para usar o padrão do Puppeteer)
# CHROMIUM_PATH=
# PUPPETEER_EXECUTABLE_PATH=

# Modo headless (true/false) - padrão: true
# Se false, o navegador será aberto visivelmente (útil para debug)
HEADLESS=true
```

## Execução

Inicie o bot com:

```bash
npm start
```

O bot estará disponível em: `http://localhost:3001`

## Endpoints Disponíveis

- `GET http://localhost:3001/status` - Status do bot
- `POST http://localhost:3001/start` - Iniciar bot
- `POST http://localhost:3001/stop` - Parar bot
- `GET http://localhost:3001/qr` - Obter QR Code
- `POST http://localhost:3001/send` - Enviar mensagem
- `POST http://localhost:3001/send-bulk` - Enviar mensagem em massa

## Notas

- O bot inicia automaticamente quando o servidor é iniciado
- O QR Code será gerado automaticamente e estará disponível em `/qr` ou `/status`
- O bot escuta apenas em `localhost` (127.0.0.1) para segurança
- Para ver o navegador em ação (debug), defina `HEADLESS=false` no `.env`

