FROM python:3.11-slim

# Evita perguntas interativas
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências mínimas do Chromium (sem pacotes obsoletos)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxext6 \
    libxfixes3 \
    libgbm1 \
    libasound2 \
    libcups2 \
    libxshmfence1 \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala Node 18 (necessário para Puppeteer)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Variáveis do Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_DOWNLOAD=true

# Cria diretório da aplicação
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copia resto do projeto
COPY . .

# Instala dependências do bot
WORKDIR /app/cobranca-bot
RUN npm install --production=false

# Volta para raiz
WORKDIR /app

# Tornar script de inicialização executável
RUN chmod +x start.sh

EXPOSE 8000 3001

CMD ["./start.sh"]
