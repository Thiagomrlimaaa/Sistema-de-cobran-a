# 💬 Chatbot de Cobrança - Luz Rastreamentos

Sistema completo de cobrança automatizada via WhatsApp usando Django e WPPConnect.

## 🚀 Funcionalidades

- ✅ Envio de mensagens personalizadas em massa
- ✅ Filtros por data de vencimento e tipo de veículo (Moto/Carro)
- ✅ Detecção automática de comprovantes de pagamento
- ✅ Dashboard web para gerenciamento
- ✅ Integração com WhatsApp via WPPConnect
- ✅ Sincronização automática de contatos

## 📋 Requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL (opcional, SQLite para desenvolvimento)

## 🛠️ Instalação

### 1. Clonar repositório
```bash
git clone https://github.com/thiagomrlimaaa/chatbot-cobranca.git
cd chatbot-cobranca
```

### 2. Configurar Django
```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Copiar arquivo de ambiente
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Editar .env com suas configurações
# Aplicar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser
```

### 3. Configurar Bot WhatsApp
```bash
cd cobranca-bot

# Instalar dependências
npm install

# Copiar arquivo de ambiente
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Editar .env com suas configurações
```

### 4. Iniciar Sistema

**Windows:**
```bash
.\start_all.bat
```

**Linux/Mac:**
```bash
# Terminal 1 - Django
python manage.py runserver

# Terminal 2 - Bot
cd cobranca-bot
npm start
```

## 📖 Uso

1. Acesse http://localhost:8000
2. Faça login
3. Vá em "WhatsApp Bot" → "Iniciar Bot"
4. Escaneie o QR Code com seu WhatsApp
5. Configure clientes e envie mensagens em massa

## 🌐 Deploy

Consulte os guias:
- `GUIA_HOSPEDAGEM.md` - Opções de hospedagem
- `GUIA_ORACLE_CLOUD.txt` - Deploy no Oracle Cloud (sempre gratuito)
- `COMPARACAO_HOSPEDAGEM.md` - Comparação de serviços

## 📝 Variáveis de Ambiente

Veja `.env.example` e `cobranca-bot/.env.example` para todas as variáveis necessárias.

## 🤝 Contribuindo

1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é privado.

## 👤 Autor

Thiago Lima

---

Para mais informações, consulte a documentação nos arquivos `.txt` do projeto.
