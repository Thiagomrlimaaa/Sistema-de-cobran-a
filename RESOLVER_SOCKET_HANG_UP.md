# 🔧 Resolver Erro "socket hang up"

## ❌ Problema

O bot está retornando:
```json
{"status":"error","qrCode":null,"error":"socket hang up","connectedAt":null,"isConnected":false}
```

## 🔍 Diagnóstico

O erro "socket hang up" geralmente acontece quando o Puppeteer não consegue estabelecer conexão com o Chromium.

### Passo 1: Verificar Logs do Bot

1. Acesse o app do bot no Koyeb
2. Vá em **Logs**
3. Procure por mensagens como:
   - `✅ Chromium encontrado e verificado em: /usr/bin/chromium`
   - `❌ Chromium não encontrado em: /usr/bin/chromium`
   - `❌ Chromium NÃO é executável!`
   - `❌ Erro de conexão detectado (socket hang up)`

### Passo 2: Verificar se Chromium está Instalado

Nos logs, procure por:
```
🔍 Procurando Chrome/Chromium...
✅ Chromium do sistema encontrado em: /usr/bin/chromium
```

Se aparecer `❌ Chromium não encontrado`, o Chromium não está instalado corretamente.

### Passo 3: Verificar Permissões

Nos logs, procure por:
```
✅ Chromium é executável
```

Se aparecer `❌ Chromium NÃO é executável!`, há problema de permissões.

## ✅ Soluções

### Solução 1: Verificar Dockerfile.bot

Certifique-se de que o `Dockerfile.bot` está instalando o Chromium:

```dockerfile
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    ...
```

### Solução 2: Verificar Variáveis de Ambiente

No app do bot, verifique se estas variáveis estão configuradas:

```
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
CHROMIUM_PATH=/usr/bin/chromium
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
```

### Solução 3: Fazer Redeploy

1. No app do bot, vá em **Settings** → **Build & Deploy**
2. Clique em **Redeploy**
3. Aguarde o build completar
4. Verifique os logs novamente

### Solução 4: Verificar se o Container tem Permissões

Se o erro persistir, pode ser problema de permissões no container. O Koyeb pode precisar de configurações especiais.

## 🧪 Teste

Após fazer as correções:

1. Faça redeploy do bot
2. Aguarde alguns segundos
3. Tente iniciar o bot novamente pelo dashboard
4. Verifique os logs para ver mensagens mais detalhadas

## 📋 Checklist

- [ ] Logs mostram que Chromium foi encontrado
- [ ] Logs mostram que Chromium é executável
- [ ] Variáveis de ambiente estão configuradas
- [ ] Dockerfile.bot está instalando Chromium
- [ ] Redeploy foi feito após alterações

## 🔗 Próximos Passos

Se o problema persistir após seguir todos os passos:

1. Copie os logs completos do bot
2. Procure por mensagens de erro específicas
3. Verifique se há mensagens sobre permissões ou arquivos não encontrados

