FROM python:3.11-slim

# Evita perguntas interativas
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema (sem Node/Chromium - bot roda em app separado)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório da aplicação
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copia resto do projeto
COPY . .

# Tornar script de inicialização executável
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
