# 🚀 Início Rápido - Bot WhatsApp WPPConnect

## ✅ Passo a Passo para Começar

### 1️⃣ Configurar Variáveis de Ambiente

**Na raiz do projeto** - Criar arquivo `.env`:
```env
WPPCONNECT_BOT_URL=http://localhost:3001
WHATSAPP_PROVIDER=wppconnect
```

**Na pasta `cobranca-bot`** - Criar arquivo `.env`:
```env
DJANGO_API_URL=http://localhost:8000/api
WHATSAPP_SESSION=cobranca
BOT_PORT=3001
```

### 2️⃣ Iniciar o Sistema

Você precisa ter **2 terminais abertos**:

**Terminal 1 - Django:**
```bash
python manage.py runserver
```

**Terminal 2 - Bot WhatsApp:**
```bash
# Opção A: Usar o arquivo batch (mais fácil)
start_bot.bat

# Opção B: Manual
cd cobranca-bot
npm start
```

### 3️⃣ Usar no Dashboard

1. Acesse: http://localhost:8000
2. Faça login (jeff/1 ou thiago/1)
3. Vá em **"WhatsApp Bot"** no menu
4. Clique em **"Iniciar Bot"**
5. O QR Code aparecerá na tela
6. Escaneie com seu WhatsApp
7. Pronto! ✅

## 📱 Funcionalidades Disponíveis

- ✅ **QR Code na tela** - Aparece automaticamente quando necessário
- ✅ **Controle do bot** - Iniciar/Parar pelo site
- ✅ **Envio em massa** - Selecione clientes e envie mensagens
- ✅ **Status em tempo real** - Veja se o bot está conectado
- ✅ **Importação de contatos** - Via CSV

## ⚠️ Importante

- **Mantenha o terminal do bot aberto** enquanto usar o sistema
- O bot precisa estar rodando na porta 3001
- Na primeira vez, você precisará escanear o QR Code
- Após escanear, o bot fica conectado automaticamente

## 🐛 Problemas Comuns

**Erro: "Não foi possível conectar ao bot"**
- Verifique se o bot está rodando (Terminal 2)
- Confirme que está na porta 3001
- Verifique o arquivo `.env` na pasta `cobranca-bot`

**QR Code não aparece**
- Clique em "Iniciar Bot" primeiro
- Aguarde alguns segundos
- Clique em "Atualizar Status"

**Mensagens não são enviadas**
- Verifique se o bot está conectado (status verde)
- Confirme que os clientes têm telefone cadastrado
- Verifique os logs no terminal do bot

## 📞 Suporte

Se tiver problemas, verifique:
1. Terminal do Django está rodando?
2. Terminal do bot está rodando?
3. Bot está conectado (status verde)?
4. Arquivos `.env` estão configurados?

