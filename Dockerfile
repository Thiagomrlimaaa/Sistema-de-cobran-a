FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Atualiza sistema e instala dependências do Chromium + Node
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    build-essential \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxext6 \
    libxfixes3 \
    libgbm1 \
    libpango1.0-0 \
    libcups2 \
    libxshmfence1 \
    chromium \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Caminho do Chromium para Puppeteer
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_DOWNLOAD=true

# Pasta do projeto
WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia script de inicialização primeiro
COPY start.sh /app/start.sh

# Copia projeto inteiro
COPY . .

# Instala dependências do bot
WORKDIR /app/cobranca-bot
RUN npm install

# Volta para raiz
WORKDIR /app

# Tornar script de inicialização executável
RUN chmod +x start.sh

EXPOSE 8000 3001

CMD ["./start.sh"]
