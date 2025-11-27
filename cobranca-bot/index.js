const wppconnect = require('@wppconnect-team/wppconnect');
const axios = require('axios');
const express = require('express');
const cors = require('cors');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Tentar encontrar Chromium no sistema
function findChromium() {
  console.log('🔍 Procurando Chrome/Chromium...');
  console.log(`🔍 PUPPETEER_CACHE_DIR: ${process.env.PUPPETEER_CACHE_DIR || 'não definido'}`);
  console.log(`🔍 PUPPETEER_EXECUTABLE_PATH: ${process.env.PUPPETEER_EXECUTABLE_PATH || 'não definido'}`);
  console.log(`🔍 CHROMIUM_PATH: ${process.env.CHROMIUM_PATH || 'não definido'}`);
  
  // Primeiro, tentar variáveis de ambiente
  if (process.env.PUPPETEER_EXECUTABLE_PATH && fs.existsSync(process.env.PUPPETEER_EXECUTABLE_PATH)) {
    console.log(`✅ Chrome encontrado via PUPPETEER_EXECUTABLE_PATH: ${process.env.PUPPETEER_EXECUTABLE_PATH}`);
    return process.env.PUPPETEER_EXECUTABLE_PATH;
  }
  
  if (process.env.CHROMIUM_PATH && fs.existsSync(process.env.CHROMIUM_PATH)) {
    console.log(`✅ Chrome encontrado via CHROMIUM_PATH: ${process.env.CHROMIUM_PATH}`);
    return process.env.CHROMIUM_PATH;
  }
  
  // Procurar Chrome do Puppeteer usando glob
  try {
    const { glob } = require('glob');
    
    // Tentar vários padrões de busca
    const searchPatterns = [
      // Render cache
      process.env.PUPPETEER_CACHE_DIR ? `${process.env.PUPPETEER_CACHE_DIR}/chrome/**/chrome-linux/chrome` : null,
      // node_modules cache
      path.join(__dirname, 'node_modules', '.cache', 'puppeteer', 'chrome', '**', 'chrome-linux', 'chrome'),
      // Caminho alternativo
      '/opt/render/.cache/puppeteer/chrome/**/chrome-linux/chrome',
      // Home directory
      path.join(process.env.HOME || process.env.USERPROFILE || '/tmp', '.cache', 'puppeteer', 'chrome', '**', 'chrome-linux', 'chrome'),
    ];
    
    for (const pattern of searchPatterns) {
      if (!pattern) continue;
      
      try {
        console.log(`🔍 Procurando em: ${pattern}`);
        const chromeFiles = glob.sync(pattern, { absolute: true });
        console.log(`🔍 Encontrados ${chromeFiles.length} arquivos`);
        
        for (const chromeFile of chromeFiles) {
          if (fs.existsSync(chromeFile)) {
            // Verificar se é executável
            try {
              fs.accessSync(chromeFile, fs.constants.F_OK | fs.constants.X_OK);
              console.log(`✅ Chrome do Puppeteer encontrado em: ${chromeFile}`);
              return chromeFile;
            } catch (e) {
              console.log(`⚠️ Arquivo encontrado mas não executável: ${chromeFile}`);
            }
          }
        }
      } catch (e) {
        console.log(`⚠️ Erro ao procurar em ${pattern}: ${e.message}`);
      }
    }
  } catch (e) {
    console.log(`⚠️ Erro ao usar glob: ${e.message}`);
  }
  
  // Tentar caminhos do sistema
  const systemPaths = [
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/local/bin/chromium',
    '/usr/local/bin/chromium-browser',
  ];
  
  for (const systemPath of systemPaths) {
    if (fs.existsSync(systemPath)) {
      console.log(`✅ Chrome do sistema encontrado em: ${systemPath}`);
      return systemPath;
    }
  }
  
  console.log('❌ Chrome não encontrado em nenhum local');
  return undefined;
}

const chromiumPath = findChromium();
if (chromiumPath) {
  console.log(`✅ Chromium encontrado em: ${chromiumPath}`);
  // Definir variável de ambiente para o Puppeteer usar
  process.env.PUPPETEER_EXECUTABLE_PATH = chromiumPath;
  console.log(`✅ PUPPETEER_EXECUTABLE_PATH definido como: ${chromiumPath}`);
} else {
  console.log('⚠️ Chromium não encontrado no sistema');
  console.log('⚠️ Tentando usar Chrome padrão do Puppeteer (pode falhar)');
  console.log('⚠️ Certifique-se de que o Chrome foi instalado com: npx puppeteer browsers install chrome');
}

const DJANGO_API_URL = process.env.DJANGO_API_URL || 'http://localhost:8000/api';
const SESSION_NAME = process.env.WHATSAPP_SESSION || 'cobranca';
// Usar BOT_PORT primeiro, depois PORT (se não for 8000), ou padrão 3001
// IMPORTANTE: No Fly.io, PORT=8000 é para Django, então sempre usar BOT_PORT
const BOT_PORT = process.env.BOT_PORT || (process.env.PORT && process.env.PORT !== '8000' ? process.env.PORT : null) || 3001;

let whatsappClient = null;
let qrCodeBase64 = null;
let connectionStatus = 'disconnected'; // disconnected, connecting, connected, error
let app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Estado do bot
let botState = {
  status: 'disconnected',
  qrCode: null,
  error: null,
  connectedAt: null,
};

// Função para limpar QR Code (remover prefixo data:image se existir)
function cleanQRCode(qrCode) {
  if (!qrCode) return null;
  if (typeof qrCode !== 'string') return qrCode;
  
  // Se começa com data:image, remover o prefixo
  if (qrCode.startsWith('data:image')) {
    const parts = qrCode.split(',');
    return parts.length > 1 ? parts[1] : qrCode;
  }
  
  return qrCode;
}

// Função para enviar mensagem recebida para o Django
async function sendMessageToDjango(phone, message, messageId, messageType = 'chat') {
  try {
    const response = await axios.post(`${DJANGO_API_URL}/webhooks/whatsapp/wppconnect/`, {
      phone: phone,
      message: message,
      message_id: messageId,
      message_type: messageType,
      timestamp: new Date().toISOString(),
    });
    console.log('Mensagem enviada para Django:', response.data);
    return response.data;
  } catch (error) {
    console.error('Erro ao enviar mensagem para Django:', error.message);
    if (error.response) {
      console.error('Detalhes:', error.response.data);
    }
  }
}

// Função para processar mensagens recebidas
async function handleIncomingMessage(message) {
  // Ignorar mensagens de status, broadcast e newsletter
  if (!message.from || 
      message.from.includes('status@broadcast') || 
      message.from.includes('@broadcast') ||
      message.from.includes('@newsletter')) {
    return; // Ignorar mensagens de status/broadcast/newsletter
  }

  // Ignorar mensagens sem remetente válido
  if (!message.from || !message.from.includes('@')) {
    return;
  }

  const phone = message.from.replace('@c.us', '').replace('@g.us', '');
  const messageBody = message.body || message.caption || '';
  const messageId = message.id;
  const messageType = message.type || 'chat';
  const isImage = messageType === 'image' || messageType === 'document';

  // Se for imagem/documento, processar como comprovante (mesmo sem texto)
  if (isImage) {
    console.log(`📷 Comprovante recebido de ${phone} (${messageType})`);
    // Enviar para Django processar como comprovante
    const result = await sendMessageToDjango(phone, '[COMPROVANTE_ENVIADO]', messageId, messageType);
    if (result && result.auto_reply) {
      try {
        await whatsappClient.sendText(`${phone}@c.us`, result.auto_reply);
        console.log(`✅ Resposta automática enviada para ${phone}`);
      } catch (error) {
        console.error(`❌ Erro ao enviar resposta automática para ${phone}:`, error.message);
      }
    }
    return;
  }

  // Ignorar mensagens vazias (apenas para texto)
  if (!messageBody || !messageBody.trim()) {
    return;
  }

  // Validar telefone (deve ter pelo menos 10 dígitos)
  const phoneDigits = phone.replace(/\D/g, '');
  if (phoneDigits.length < 10) {
    console.log(`⚠️ Telefone inválido ignorado: ${phone}`);
    return;
  }

  console.log(`📨 Mensagem recebida de ${phone}: ${messageBody.substring(0, 50)}...`);

  // Enviar para Django processar
  const result = await sendMessageToDjango(phone, messageBody, messageId);

  // Se o Django retornar uma resposta automática, enviar
  if (result && result.auto_reply) {
    try {
      await whatsappClient.sendText(`${phone}@c.us`, result.auto_reply);
      console.log(`✅ Resposta automática enviada para ${phone}`);
    } catch (error) {
      console.error(`❌ Erro ao enviar resposta automática para ${phone}:`, error.message);
    }
  }
}

// Função para formatar telefone
function formatPhone(phone) {
  // Remove caracteres não numéricos
  let cleaned = phone.replace(/\D/g, '');
  
  // Se não começar com 55 (código do Brasil), adiciona
  if (!cleaned.startsWith('55')) {
    cleaned = '55' + cleaned;
  }
  
  return `${cleaned}@c.us`;
}

// Função para enviar mensagem via bot (quando solicitado pelo Django)
async function sendMessage(phone, message) {
  if (!whatsappClient) {
    throw new Error('Cliente WhatsApp não está conectado');
  }

  // Verificar se o cliente está realmente conectado
  try {
    const isConnected = await whatsappClient.isConnected();
    if (!isConnected) {
      throw new Error('Cliente WhatsApp não está conectado (isConnected retornou false)');
    }
    console.log(`[ENVIO] ✅ Cliente verificado como conectado`);
  } catch (checkError) {
    console.error(`[ENVIO] ❌ Erro ao verificar conexão:`, checkError.message);
    throw new Error('Não foi possível verificar conexão do WhatsApp');
  }

  try {
    const formattedPhone = formatPhone(phone);
    console.log(`[ENVIO] Tentando enviar para: ${formattedPhone} (original: ${phone})`);
    console.log(`[ENVIO] Mensagem (${message.length} caracteres): ${message.substring(0, 50)}...`);
    console.log(`[ENVIO] whatsappClient existe: ${!!whatsappClient}`);
    console.log(`[ENVIO] Tipo do whatsappClient: ${whatsappClient.constructor.name}`);
    
    // Verificar se o método sendText existe
    if (typeof whatsappClient.sendText !== 'function') {
      throw new Error('Método sendText não está disponível no cliente WhatsApp');
    }
    
    // Tentar enviar com timeout
    const sendPromise = whatsappClient.sendText(formattedPhone, message);
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Timeout ao enviar mensagem (30s)')), 30000)
    );
    
    try {
      const result = await Promise.race([sendPromise, timeoutPromise]);
      console.log(`[ENVIO] ✅ Sucesso para ${formattedPhone}`);
      console.log(`[ENVIO] Resultado:`, JSON.stringify(result, null, 2));
      return result;
    } catch (sendError) {
      // Se falhar, tentar novamente após um delay
      console.error(`[ENVIO] ❌ Primeira tentativa falhou: ${sendError.message}`);
      console.error(`[ENVIO] ❌ Stack:`, sendError.stack);
      console.error(`[ENVIO] ❌ Tipo do erro:`, sendError.constructor.name);
      
      // Aguardar 2 segundos antes de tentar novamente
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      try {
        console.log(`[ENVIO] 🔄 Tentando novamente após delay...`);
        const result = await Promise.race([
          whatsappClient.sendText(formattedPhone, message),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout na segunda tentativa (30s)')), 30000)
          )
        ]);
        console.log(`[ENVIO] ✅ Sucesso na segunda tentativa para ${formattedPhone}`);
        return result;
      } catch (retryError) {
        console.error(`[ENVIO] ❌ Erro persistente ao enviar para ${formattedPhone}:`, retryError.message);
        console.error(`[ENVIO] ❌ Stack:`, retryError.stack);
        throw retryError;
      }
    }
  } catch (error) {
    console.error(`[ENVIO] ❌ Erro geral ao enviar para ${phone}:`, error.message);
    console.error(`[ENVIO] ❌ Stack completo:`, error.stack);
    console.error(`[ENVIO] ❌ Tipo do erro:`, error.constructor.name);
    throw error;
  }
}

// Função para inicializar conexão WhatsApp
async function initializeWhatsApp() {
  if (whatsappClient) {
    console.log('Bot já está conectado');
    return Promise.resolve(whatsappClient);
  }

  // Limpar sessão antiga se existir (para evitar erro de navegador já em execução)
  try {
    const path = require('path');
    const sessionPath = path.join(__dirname, 'tokens', SESSION_NAME);
    
    // Verificar se há processos do Chromium rodando para esta sessão
    const { execSync } = require('child_process');
    try {
      console.log('🔧 Verificando processos do Chromium...');
      // Tentar matar processos de forma mais suave
      execSync('killall chromium chromium-browser chrome 2>/dev/null || true', { stdio: 'ignore' });
      execSync('pkill -9 -f puppeteer 2>/dev/null || true', { stdio: 'ignore' });
      console.log('✅ Processos antigos limpos');
    } catch (killError) {
      // Ignorar erros - pode não haver processos
      console.log('⚠️ Processos já limpos ou não existem');
    }
    
    // Limpar diretório de sessão antiga se existir (forçar novo QR Code)
    try {
      const browserDataPath = path.join(sessionPath, 'browser_data');
      if (fs.existsSync(browserDataPath)) {
        console.log('🔧 Limpando dados do navegador antigo...');
        fs.rmSync(browserDataPath, { recursive: true, force: true });
        console.log('✅ Dados do navegador limpos');
      }
    } catch (cleanupErr) {
      console.log('⚠️ Erro ao limpar dados do navegador:', cleanupErr.message);
    }
    
    // Aguardar um pouco para garantir que processos foram finalizados
    await new Promise(resolve => setTimeout(resolve, 3000));
  } catch (cleanupError) {
    console.log('⚠️ Erro ao limpar sessão antiga:', cleanupError.message);
  }

  connectionStatus = 'connecting';
  botState.status = 'connecting';
  botState.qrCode = null;
  botState.error = null;

  // Log de debug
  console.log('🔧 Iniciando WPPConnect...');
  console.log('🔧 Chromium path:', chromiumPath || process.env.PUPPETEER_EXECUTABLE_PATH || process.env.CHROMIUM_PATH || 'não definido');
  console.log('🔧 Session name:', SESSION_NAME);
  console.log('🔧 Verificando se Chromium existe...');
  
  // Verificar se Chromium existe antes de iniciar
  const execPath = chromiumPath || process.env.PUPPETEER_EXECUTABLE_PATH || process.env.CHROMIUM_PATH;
  if (execPath && !fs.existsSync(execPath)) {
    console.error(`❌ Chromium não encontrado em: ${execPath}`);
    console.error('❌ Tentando continuar sem caminho específico...');
  } else if (execPath) {
    console.log(`✅ Chromium encontrado em: ${execPath}`);
  } else {
    console.log('⚠️ Caminho do Chromium não definido, usando padrão do Puppeteer');
  }
  
  // Usar userDataDir único para evitar conflitos
  const path = require('path');
  const userDataDir = path.join(__dirname, 'tokens', SESSION_NAME, 'browser_data');
  
  console.log('🔧 UserDataDir:', userDataDir);
  
  // Criar diretório se não existir
  try {
    if (!fs.existsSync(userDataDir)) {
      fs.mkdirSync(userDataDir, { recursive: true });
      console.log('✅ Diretório userDataDir criado');
    }
  } catch (dirError) {
    console.log('⚠️ Erro ao criar diretório:', dirError.message);
  }
  
  return wppconnect
    .create({
      session: SESSION_NAME,
      userDataDir: userDataDir, // Diretório único para dados do navegador
      disableWelcome: true, // Desabilitar mensagem de boas-vindas
      updatesLog: true, // Habilitar logs de atualizações
      waitForLogin: false, // Não esperar login automático - forçar QR Code
      autoClose: 60000, // Fechar automaticamente após 60 segundos se não conectar
      browserArgs: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-breakpad',
        '--disable-component-update',
        '--disable-domain-reliability',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--disable-sync',
        '--metrics-recording-only',
        '--mute-audio',
        '--no-default-browser-check',
        '--no-pings',
        '--password-store=basic',
        '--use-mock-keychain',
        '--hide-scrollbars',
        '--disable-logging',
        '--disable-notifications'
      ],
      puppeteerOptions: {
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--single-process',
          '--disable-gpu',
          '--disable-software-rasterizer',
          '--disable-extensions',
          '--disable-background-networking',
          '--disable-background-timer-throttling',
          '--disable-renderer-backgrounding',
          '--disable-backgrounding-occluded-windows',
          '--disable-breakpad',
          '--disable-component-update',
          '--disable-domain-reliability',
          '--disable-features=TranslateUI',
          '--disable-ipc-flooding-protection',
          '--disable-sync',
          '--metrics-recording-only',
          '--mute-audio',
          '--no-default-browser-check',
          '--no-pings',
          '--password-store=basic',
          '--use-mock-keychain',
          '--hide-scrollbars',
          '--disable-logging',
          '--disable-notifications'
        ],
        executablePath: chromiumPath || process.env.PUPPETEER_EXECUTABLE_PATH || process.env.CHROMIUM_PATH || undefined,
        ignoreDefaultArgs: ['--disable-extensions'],
        timeout: 180000, // Aumentar timeout para 3 minutos
        protocolTimeout: 300000 // Aumentar protocolTimeout para 5 minutos (para operações pesadas como getAllContacts)
      },
      catchQR: (base64Qr, asciiQR, attempts, urlCode) => {
        console.log('═══════════════════════════════════════════════════════');
        console.log('✅ QR CODE GERADO!');
        console.log('═══════════════════════════════════════════════════════');
        console.log('✅ Tentativa:', attempts || 'N/A');
        console.log('✅ QR Code base64 disponível:', base64Qr ? 'Sim' : 'Não');
        console.log('✅ QR Code ASCII disponível:', asciiQR ? 'Sim' : 'Não');
        console.log('✅ URL Code:', urlCode || 'N/A');
        if (base64Qr) {
          console.log('✅ Tamanho do QR Code:', base64Qr.length, 'caracteres');
        }
        
        // Limpar QR Code (remover prefixo se existir)
        const cleanBase64 = cleanQRCode(base64Qr);
        
        // Armazenar QR Code (apenas o base64 puro)
        qrCodeBase64 = cleanBase64;
        botState.qrCode = cleanBase64;
        botState.status = 'waiting_qr';
        connectionStatus = 'waiting_qr';
        
        console.log('✅ Estado atualizado: waiting_qr');
        console.log('📱 QR Code disponível na API: GET http://localhost:' + BOT_PORT + '/qr');
        console.log('📱 QR Code também disponível em: GET http://localhost:' + BOT_PORT + '/status');
        
        // Forçar atualização imediata do estado
        if (cleanBase64) {
          console.log('✅ QR Code base64 capturado com sucesso! (tamanho: ' + cleanBase64.length + ' caracteres)');
        } else {
          console.error('❌ QR Code base64 está vazio!');
          console.error('❌ Tentando usar ASCII QR Code...');
          if (asciiQR) {
            console.log('⚠️ Usando ASCII QR Code como fallback');
          }
        }
      },
      statusFind: (statusSession, session) => {
        console.log('📊 Status da sessão:', statusSession);
        console.log('📊 Session object:', session ? 'existe' : 'não existe');
        
        if (statusSession === 'isLogged') {
          connectionStatus = 'connected';
          botState.status = 'connected';
          botState.qrCode = null;
          botState.connectedAt = new Date().toISOString();
          botState.error = null;
          console.log('✅ WhatsApp conectado com sucesso!');
          console.log('✅ Bot pronto para enviar mensagens!');
        } else if (statusSession === 'qrReadSuccess') {
          connectionStatus = 'connecting';
          botState.status = 'connecting';
          botState.qrCode = null;
          console.log('📱 QR Code escaneado, conectando...');
        } else if (statusSession === 'notLogged' || statusSession === 'desconnectedMobile') {
          connectionStatus = 'disconnected';
          botState.status = 'disconnected';
          botState.qrCode = null;
          console.log('⚠️ Sessão desconectada');
        } else if (statusSession === 'browserClose' || statusSession === 'qrReadError') {
          connectionStatus = 'error';
          botState.status = 'error';
          botState.error = `Erro na sessão: ${statusSession}`;
          console.error('❌ Erro na sessão:', statusSession);
        } else {
          console.log('ℹ️ Status desconhecido:', statusSession);
        }
      },
    })
    .then((client) => {
      whatsappClient = client;
      connectionStatus = 'connected';
      botState.status = 'connected';
      botState.connectedAt = new Date().toISOString();
      console.log('✅ Bot iniciado e pronto para receber mensagens!');

      // Escutar mensagens recebidas
      client.onMessage(async (message) => {
        // Ignorar mensagens do próprio bot
        if (message.fromMe) return;

        // Ignorar mensagens de status/broadcast/newsletter
        if (message.from && (
          message.from.includes('status@broadcast') || 
          message.from.includes('@broadcast') ||
          message.from.includes('@newsletter')
        )) {
          return; // Ignorar silenciosamente
        }

        // Processar apenas mensagens de texto, imagem ou documento
        if (message.type === 'chat' || message.type === 'image' || message.type === 'document') {
          await handleIncomingMessage(message);
        }
      });

      // Escutar mudanças de status (conexão, desconexão, etc)
      client.onStateChange((state) => {
        console.log('Estado da conexão:', state);
        if (state === 'CONFLICT' || state === 'UNPAIRED') {
          connectionStatus = 'disconnected';
          botState.status = 'disconnected';
          whatsappClient = null;
          console.log('Conexão perdida.');
        }
      });

      return client;
    })
    .catch(async (err) => {
      console.error('❌ Erro ao inicializar WhatsApp:', err);
      console.error('❌ Stack trace:', err.stack);
      console.error('❌ Tipo do erro:', err.constructor.name);
      console.error('❌ Mensagem completa:', JSON.stringify(err, Object.getOwnPropertyNames(err)));
      
      // Se o erro for sobre navegador já em execução, tentar limpar
      if (err.message && (err.message.includes('já está em execução') || err.message.includes('already running'))) {
        console.log('🔧 Detectado erro de navegador já em execução. Limpando...');
        try {
          await disconnect();
          console.log('✅ Sessão antiga limpa. Tente iniciar novamente.');
        } catch (cleanupErr) {
          console.error('❌ Erro ao limpar sessão:', cleanupErr.message);
        }
      }
      
      connectionStatus = 'error';
      botState.status = 'error';
      botState.error = err.message || 'Erro desconhecido ao inicializar WhatsApp';
      whatsappClient = null;
      
      // Não fazer throw para evitar crash - apenas logar o erro
      console.error('❌ Bot não pôde ser inicializado. Tente parar e iniciar novamente.');
    });
}

// Função para desconectar
async function disconnect() {
  if (whatsappClient) {
    try {
      // Tentar fechar graciosamente primeiro
      try {
        await whatsappClient.logout();
        console.log('✅ Logout realizado');
      } catch (logoutErr) {
        console.log('⚠️ Erro no logout (pode já estar desconectado):', logoutErr.message);
      }
      
      // Fechar cliente
      try {
        await whatsappClient.close();
        console.log('✅ Cliente WhatsApp fechado');
      } catch (closeErr) {
        console.log('⚠️ Erro ao fechar cliente (pode já estar fechado):', closeErr.message);
      }
    } catch (err) {
      console.error('❌ Erro ao fechar cliente:', err.message);
    }
    whatsappClient = null;
  }

  // Matar processos do Chromium/Puppeteer que possam estar travados
  try {
    const { execSync } = require('child_process');
    console.log('🔧 Limpando processos do Chromium...');
    try {
      // Tentar matar processos de forma mais suave
      execSync('killall chromium chromium-browser chrome 2>/dev/null || true', { stdio: 'ignore' });
      execSync('pkill -9 -f puppeteer 2>/dev/null || true', { stdio: 'ignore' });
      console.log('✅ Processos do Chromium limpos');
    } catch (killError) {
      // Ignorar erros - pode não haver processos para matar
      console.log('⚠️ Processos já limpos ou não existem');
    }
  } catch (err) {
    console.log('⚠️ Erro ao limpar processos:', err.message);
  }

  connectionStatus = 'disconnected';
  botState.status = 'disconnected';
  botState.qrCode = null;
  botState.connectedAt = null;

  console.log('✅ Bot desconectado');
}

// ========== ENDPOINTS DA API ==========

// Status do bot
app.get('/status', (req, res) => {
  // Garantir que o QR Code está atualizado no estado
  if (qrCodeBase64 && !botState.qrCode) {
    botState.qrCode = cleanQRCode(qrCodeBase64);
  }
  
  const qrCode = botState.qrCode || qrCodeBase64;
  
  res.json({
    status: botState.status,
    qrCode: cleanQRCode(qrCode), // Retornar QR Code limpo (sem prefixo)
    error: botState.error,
    connectedAt: botState.connectedAt,
    isConnected: !!whatsappClient,
  });
});

// Iniciar bot
app.post('/start', async (req, res) => {
  try {
    if (whatsappClient && botState.status === 'connected') {
      return res.json({
        success: true,
        message: 'Bot já está conectado',
        status: botState.status,
        qrCode: null,
      });
    }

    // Se já está inicializando, retornar status atual
    if (botState.status === 'waiting_qr' || botState.status === 'connecting') {
      return res.json({
        success: true,
        message: 'Bot já está inicializando',
        status: botState.status,
        qrCode: cleanQRCode(botState.qrCode), // Retornar QR Code limpo
      });
    }

    // Iniciar bot
    initializeWhatsApp().catch((err) => {
      console.error('❌ Erro ao iniciar bot:', err);
      console.error('❌ Stack trace:', err.stack);
      botState.status = 'error';
      botState.error = err.message || 'Erro desconhecido ao iniciar bot';
      connectionStatus = 'error';
    });

    // Aguardar um pouco para o QR Code ser gerado
    await new Promise(resolve => setTimeout(resolve, 2000));

    res.json({
      success: true,
      message: 'Bot iniciado com sucesso',
      status: botState.status,
      qrCode: cleanQRCode(botState.qrCode), // Retornar QR Code limpo
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      status: botState.status,
    });
  }
});

// Parar bot
app.post('/stop', async (req, res) => {
  try {
    await disconnect();
    res.json({
      success: true,
      message: 'Bot desconectado com sucesso',
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// Obter QR Code
app.get('/qr', (req, res) => {
  // Verificar se há QR Code no estado atual
  if (botState.qrCode) {
    res.json({
      success: true,
      qrCode: cleanQRCode(botState.qrCode), // Retornar QR Code limpo
      status: botState.status,
    });
  } else if (qrCodeBase64) {
    // Se não está no botState mas está na variável, limpar, atualizar e retornar
    const cleanQR = cleanQRCode(qrCodeBase64);
    botState.qrCode = cleanQR;
    botState.status = 'waiting_qr';
    res.json({
      success: true,
      qrCode: cleanQR, // Retornar QR Code limpo
      status: 'waiting_qr',
    });
  } else if (botState.status === 'waiting_qr' || botState.status === 'connecting') {
    // Se está aguardando QR mas ainda não foi capturado, retornar status
    res.json({
      success: false,
      message: 'QR Code sendo gerado, aguarde...',
      status: botState.status,
    });
  } else {
    res.json({
      success: false,
      message: 'QR Code não disponível. Inicie o bot primeiro.',
      status: botState.status,
    });
  }
});

// Enviar mensagem
app.post('/send', async (req, res) => {
  const { phone, message } = req.body;

  console.log(`[SEND] Recebida requisição de envio individual`);
  console.log(`[SEND] Telefone recebido: ${phone}`);
  console.log(`[SEND] Mensagem: ${message ? message.substring(0, 50) : 'vazia'}...`);
  console.log(`[SEND] Status do bot: ${botState.status}`);
  console.log(`[SEND] whatsappClient existe: ${!!whatsappClient}`);

  if (!phone || !message) {
    console.log(`[SEND] ❌ Dados incompletos - phone: ${!!phone}, message: ${!!message}`);
    return res.status(400).json({
      success: false,
      error: 'phone e message são obrigatórios',
    });
  }

  if (!whatsappClient) {
    console.log(`[SEND] ❌ Bot não está conectado - whatsappClient é null`);
    return res.status(400).json({
      success: false,
      error: 'Bot não está conectado. Verifique a conexão do WhatsApp.',
    });
  }

  if (botState.status !== 'connected') {
    console.log(`[SEND] ❌ Bot não está no status conectado - status atual: ${botState.status}`);
    return res.status(400).json({
      success: false,
      error: `Bot não está conectado. Status atual: ${botState.status}`,
    });
  }

  try {
    console.log(`[SEND] ✅ Iniciando envio...`);
    const result = await sendMessage(phone, message);
    console.log(`[SEND] ✅ Mensagem enviada com sucesso!`);
    res.json({
      success: true,
      result: result,
    });
  } catch (error) {
    console.error(`[SEND] ❌ Erro ao enviar mensagem:`, error);
    res.status(500).json({
      success: false,
      error: error.message || 'Erro desconhecido ao enviar mensagem',
    });
  }
});

// Adicionar/verificar contato no WhatsApp
app.post('/add-contact', async (req, res) => {
  const { phone, name } = req.body;

  console.log(`[CONTACT] Verificando contato: ${name || 'Sem nome'} - ${phone}`);

  if (!phone) {
    return res.status(400).json({
      success: false,
      error: 'phone é obrigatório',
    });
  }

  if (!whatsappClient) {
    return res.status(400).json({
      success: false,
      error: 'Bot não está conectado',
    });
  }

  try {
    const formattedPhone = formatPhone(phone);
    const phoneDigits = formattedPhone.replace(/\D/g, '');
    
    // Buscar contatos do WhatsApp para verificar se existe
    let foundContact = null;
    let whatsappName = name || '';
    
    try {
      // Adicionar timeout para getAllContacts (pode demorar muito)
      const allContacts = await Promise.race([
        whatsappClient.getAllContacts(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout ao buscar contatos (30s)')), 30000)
        )
      ]);
      if (Array.isArray(allContacts) && allContacts.length > 0) {
        // Criar mapa para busca rápida
        const contactsMap = new Map();
        allContacts.forEach(c => {
          if (!c) return;
          try {
            // O WPPConnect retorna contatos com id.user ou id._serialized
            let jid = '';
            
            if (c.id) {
              if (typeof c.id === 'object' && c.id !== null) {
                jid = c.id._serialized || c.id.user || '';
              } else {
                jid = String(c.id);
              }
            } else {
              jid = c.jid || c.number || c.phone || c._serialized || '';
              if (typeof jid === 'object' && jid !== null) {
                jid = jid.user || jid._serialized || String(jid);
              }
            }
            
            const jidStr = String(jid);
            // Remover @c.us ou outros sufixos antes de extrair dígitos
            const cleanJid = jidStr.split('@')[0];
            const digits = cleanJid.replace(/\D/g, '');
            
            if (digits.length >= 10) {
              contactsMap.set(digits, c);
              if (digits.startsWith('55') && digits.length > 12) {
                contactsMap.set(digits.substring(2), c);
              }
              // Também armazenar últimos 11 dígitos
              if (digits.length >= 11) {
                contactsMap.set(digits.slice(-11), c);
              }
            }
          } catch (err) {
            // Ignorar contatos com erro
          }
        });
        
        // Buscar o contato (tentar diferentes variações)
        foundContact = contactsMap.get(phoneDigits);
        if (!foundContact && phoneDigits.startsWith('55') && phoneDigits.length > 12) {
          foundContact = contactsMap.get(phoneDigits.substring(2));
        }
        if (!foundContact && phoneDigits.length >= 11) {
          foundContact = contactsMap.get(phoneDigits.slice(-11));
        }
        if (!foundContact && phoneDigits.length >= 10) {
          foundContact = contactsMap.get(phoneDigits.slice(-10));
        }
        
        if (foundContact) {
          whatsappName = foundContact.name || foundContact.notify || foundContact.verifiedName || foundContact.businessName || foundContact.pushname || name || '';
          console.log(`[CONTACT] ✅ Contato encontrado no WhatsApp: "${whatsappName}"`);
        } else {
          console.log(`[CONTACT] ⚠️ Contato não encontrado na lista do WhatsApp (mapa tem ${contactsMap.size} entradas)`);
        }
      }
    } catch (contactsError) {
      console.log(`[CONTACT] ⚠️ Erro ao buscar contatos: ${contactsError.message}`);
      // Não é crítico - continuar mesmo sem contatos
      if (contactsError.message.includes('timeout') || contactsError.message.includes('Timeout')) {
        console.log(`[CONTACT] ⚠️ Timeout ao buscar contatos - continuando sem verificação`);
      }
    }
    
    return res.json({
      success: true,
      message: foundContact ? 'Contato encontrado no WhatsApp' : 'Número formatado (não encontrado na lista de contatos)',
      phone: formattedPhone,
      exists: !!foundContact,
      whatsapp_name: whatsappName !== name ? whatsappName : null,
      note: foundContact ? 'Contato já está no WhatsApp' : 'O número será validado quando a mensagem for enviada',
    });
  } catch (error) {
    console.error(`[CONTACT] ❌ Erro ao verificar contato:`, error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Erro ao verificar contato',
    });
  }
});

// Sincronizar múltiplos contatos
app.post('/sync-contacts', async (req, res) => {
  const { contacts } = req.body;

  console.log(`[SYNC] Sincronizando ${contacts ? contacts.length : 0} contatos`);

  if (!contacts || !Array.isArray(contacts)) {
    return res.status(400).json({
      success: false,
      error: 'contacts (array) é obrigatório',
    });
  }

  if (!whatsappClient) {
    return res.status(400).json({
      success: false,
      error: 'Bot não está conectado',
    });
  }

  const results = [];
  const errors = [];

  // Buscar todos os contatos do WhatsApp uma vez
  let whatsappContacts = [];
  let contactsMap = new Map(); // Mapa para busca rápida por número
  
  try {
    // Adicionar timeout para getAllContacts (pode demorar muito)
    whatsappContacts = await Promise.race([
      whatsappClient.getAllContacts(),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout ao buscar contatos (30s)')), 30000)
      )
    ]);
    console.log(`[SYNC] 📱 Encontrados ${whatsappContacts.length} contatos no WhatsApp`);
    
    // Criar mapa de contatos para busca rápida
    if (Array.isArray(whatsappContacts) && whatsappContacts.length > 0) {
      let processedCount = 0;
      let skippedCount = 0;
      
      // Debug apenas se houver problema (mapa vazio)
      
      whatsappContacts.forEach((contact, index) => {
        if (!contact) {
          skippedCount++;
          return;
        }
        
        try {
          // Tentar extrair o número de diferentes propriedades
          // O WPPConnect retorna contatos com id.user ou id._serialized
          let jid = '';
          
          if (contact.id) {
            if (typeof contact.id === 'object' && contact.id !== null) {
              // id é um objeto com user, server, _serialized
              jid = contact.id._serialized || contact.id.user || '';
            } else {
              jid = String(contact.id);
            }
          } else {
            // Fallback para outras propriedades
            jid = contact.jid || contact.number || contact.phone || contact._serialized || '';
            if (typeof jid === 'object' && jid !== null) {
              jid = jid.user || jid._serialized || String(jid);
            }
          }
          
          // Converter para string e extrair dígitos
          const jidStr = String(jid);
          // Remover @c.us ou outros sufixos antes de extrair dígitos
          const cleanJid = jidStr.split('@')[0]; // Pegar apenas a parte antes do @
          const digits = cleanJid.replace(/\D/g, '');
          
          if (digits.length >= 10) {
            // Armazenar com código completo
            contactsMap.set(digits, contact);
            
            // Se começa com 55 (Brasil), também armazenar sem o código
            if (digits.startsWith('55') && digits.length > 12) {
              const withoutCountry = digits.substring(2);
              if (withoutCountry.length >= 10) {
                contactsMap.set(withoutCountry, contact);
              }
            }
            
            // Também armazenar apenas os últimos 10-11 dígitos (DDD + número)
            if (digits.length >= 10) {
              const lastDigits = digits.slice(-11); // Últimos 11 dígitos (DDD + número)
              if (lastDigits.length >= 10) {
                contactsMap.set(lastDigits, contact);
              }
            }
            
            processedCount++;
          } else {
            skippedCount++;
          }
        } catch (err) {
          skippedCount++;
          // Erros silenciosos - apenas contar
        }
      });
      console.log(`[SYNC] 📋 Mapa de contatos criado: ${contactsMap.size} entradas (${processedCount} processados)`);
      
      // Debug apenas se houver problema
      if (contactsMap.size === 0 && whatsappContacts.length > 0) {
        const firstContact = whatsappContacts[0];
        console.log(`[SYNC] ⚠️ Problema: Mapa vazio! Debug primeiro contato:`, {
          keys: Object.keys(firstContact || {}),
          id: firstContact?.id,
          jid: firstContact?.jid
        });
      }
    } else {
      console.log(`[SYNC] ⚠️ whatsappContacts não é um array válido ou está vazio`);
    }
  } catch (error) {
    console.log(`[SYNC] ⚠️ Não foi possível buscar contatos do WhatsApp: ${error.message}`);
    if (error.message.includes('timeout') || error.message.includes('Timeout')) {
      console.log(`[SYNC] ⚠️ Timeout ao buscar contatos - continuando sem sincronização`);
      console.log(`[SYNC] ⚠️ Envio de mensagens não será afetado - sincronização é opcional`);
    } else {
      console.log(`[SYNC] 🔍 Stack:`, error.stack);
    }
    // Continuar mesmo se falhar - sincronização não é crítica
  }

  for (const contact of contacts) {
    try {
      const phone = contact.phone || contact;
      const name = contact.name || '';
      const formattedPhone = formatPhone(phone);
      
      // Validar formato do telefone (deve ter pelo menos 10 dígitos após formatação)
      const phoneDigits = formattedPhone.replace(/\D/g, '');
      if (phoneDigits.length < 10) {
        errors.push({ phone: formattedPhone, name, exists: false, error: 'Telefone inválido (muito curto)' });
        console.log(`[SYNC] ❌ ${name || formattedPhone}: telefone inválido`);
        continue;
      }
      
      // Buscar nome do contato no WhatsApp se disponível
      let whatsappName = name;
      let foundInWhatsApp = false;
      
      if (contactsMap.size > 0) {
        // Extrair apenas dígitos do telefone formatado
        const phoneDigits = formattedPhone.replace(/\D/g, '');
        
        // Buscar no mapa (tentar diferentes variações)
        let foundContact = contactsMap.get(phoneDigits);
        
        if (!foundContact && phoneDigits.startsWith('55') && phoneDigits.length > 12) {
          // Tentar sem o código 55
          const withoutCountry = phoneDigits.substring(2);
          foundContact = contactsMap.get(withoutCountry);
        }
        
        if (!foundContact && phoneDigits.length >= 11) {
          // Tentar apenas os últimos 11 dígitos (DDD + número)
          const last11 = phoneDigits.slice(-11);
          foundContact = contactsMap.get(last11);
        }
        
        if (!foundContact && phoneDigits.length >= 10) {
          // Tentar apenas os últimos 10 dígitos
          const last10 = phoneDigits.slice(-10);
          foundContact = contactsMap.get(last10);
        }
        
        if (foundContact) {
          foundInWhatsApp = true;
          whatsappName = foundContact.name || foundContact.notify || foundContact.verifiedName || foundContact.businessName || foundContact.pushname || name;
          console.log(`[SYNC] ✅ ${name || formattedPhone}: encontrado no WhatsApp como "${whatsappName}"`);
        } else {
          console.log(`[SYNC] ⚠️ ${name || formattedPhone}: não encontrado na lista de contatos do WhatsApp`);
        }
      }
      
      results.push({ 
        phone: formattedPhone, 
        name: whatsappName || name,
        original_name: name,
        whatsapp_name: whatsappName !== name ? whatsappName : null,
        exists: true,
        found_in_whatsapp: foundInWhatsApp,
      });
      
      // Pequeno delay para evitar rate limit
      await new Promise((resolve) => setTimeout(resolve, 50));
    } catch (error) {
      const phone = contact.phone || contact;
      errors.push({ phone, name: contact.name || '', error: error.message });
      console.error(`[SYNC] ❌ Erro ao verificar ${phone}:`, error.message);
    }
  }

  return res.json({
    success: true,
    verified: results.length,
    not_found: errors.length,
    results: results,
    errors: errors,
  });
});

// Enviar mensagem para múltiplos clientes
app.post('/send-bulk', async (req, res) => {
  const { clients, message } = req.body;

  console.log(`[BULK] Recebida requisição de envio em massa`);
  console.log(`[BULK] Clientes: ${clients ? clients.length : 0}`);
  console.log(`[BULK] Mensagem: ${message ? message.substring(0, 50) : 'vazia'}...`);

  if (!clients || !Array.isArray(clients) || !message) {
    console.log(`[BULK] ❌ Dados inválidos`);
    return res.status(400).json({
      success: false,
      error: 'clients (array) e message são obrigatórios',
    });
  }

  if (!whatsappClient) {
    console.log(`[BULK] ❌ Bot não está conectado`);
    return res.status(400).json({
      success: false,
      error: 'Bot não está conectado',
    });
  }

  console.log(`[BULK] ✅ Bot conectado, iniciando envio...`);

  const results = [];
  const errors = [];

  for (let i = 0; i < clients.length; i++) {
    const client = clients[i];
    try {
      const phone = typeof client === 'string' ? client : client.phone;
      const formattedPhone = formatPhone(phone);
      console.log(`[BULK] [${i + 1}/${clients.length}] Enviando para: ${formattedPhone} (original: ${phone})`);
      
      // Verificar se cliente está conectado antes de cada envio
      try {
        const isConnected = await whatsappClient.isConnected();
        if (!isConnected) {
          throw new Error('Cliente WhatsApp desconectado durante envio');
        }
      } catch (checkError) {
        console.error(`[BULK] [${i + 1}/${clients.length}] ❌ Cliente desconectado:`, checkError.message);
        errors.push({ phone, error: 'Cliente WhatsApp desconectado' });
        continue;
      }
      
      const result = await sendMessage(phone, message);
      console.log(`[BULK] [${i + 1}/${clients.length}] ✅ Sucesso para ${formattedPhone}`);
      results.push({ phone: formattedPhone, success: true, result });
      
      // Pequeno delay para evitar rate limit (2 segundos entre mensagens)
      if (i < clients.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    } catch (error) {
      const phone = typeof client === 'string' ? client : client.phone;
      const formattedPhone = formatPhone(phone);
      console.error(`[BULK] [${i + 1}/${clients.length}] ❌ Erro para ${formattedPhone}:`, error.message);
      console.error(`[BULK] [${i + 1}/${clients.length}] ❌ Stack:`, error.stack);
      errors.push({ phone: formattedPhone, error: error.message });
    }
  }

  console.log(`[BULK] ✅ Concluído! Enviados: ${results.length}, Falhas: ${errors.length}`);

  res.json({
    success: true,
    sent: results.length,
    failed: errors.length,
    results: results,
    errors: errors,
  });
});

// Iniciar servidor
// Iniciar servidor Express
const server = app.listen(BOT_PORT, '0.0.0.0', () => {
  console.log(`✅ Bot API rodando na porta ${BOT_PORT}`);
  console.log(`✅ Escutando em 0.0.0.0:${BOT_PORT} (acessível de qualquer interface)`);
  console.log(`📋 Endpoints disponíveis:`);
  console.log(`  GET  /status - Status do bot`);
  console.log(`  POST /start - Iniciar bot`);
  console.log(`  POST /stop - Parar bot`);
  console.log(`  GET  /qr - Obter QR Code`);
  console.log(`  POST /send - Enviar mensagem`);
  console.log(`  POST /send-bulk - Enviar mensagem em massa`);
  console.log('');
  
  // Verificar se o servidor está realmente escutando
  const address = server.address();
  if (address) {
    console.log(`✅ Servidor confirmado escutando em ${address.address}:${address.port}`);
  } else {
    console.error(`❌ ERRO: Servidor não está escutando!`);
  }
  console.log('🔧 Variáveis de ambiente:');
  console.log(`  BOT_PORT: ${BOT_PORT}`);
  console.log(`  DJANGO_API_URL: ${DJANGO_API_URL}`);
  console.log(`  SESSION_NAME: ${SESSION_NAME}`);
  console.log(`  PUPPETEER_EXECUTABLE_PATH: ${process.env.PUPPETEER_EXECUTABLE_PATH || 'não definido'}`);
  console.log(`  CHROMIUM_PATH: ${process.env.CHROMIUM_PATH || 'não definido'}`);
  console.log(`  Chromium encontrado: ${chromiumPath || 'não encontrado'}`);
  console.log('');
  console.log('🚀 Iniciando bot automaticamente...');
  
  // Iniciar bot automaticamente quando o servidor iniciar
  // Aguardar mais tempo para garantir que tudo está pronto
  setTimeout(() => {
    console.log('⏳ Aguardando 5 segundos antes de iniciar WPPConnect...');
    console.log('⏳ Isso garante que todas as dependências estão carregadas');
    
    initializeWhatsApp().catch((err) => {
      console.error('❌ Erro ao inicializar bot automaticamente:', err);
      console.error('❌ Stack trace:', err.stack);
      console.error('❌ Tipo do erro:', err.constructor.name);
      botState.status = 'error';
      botState.error = err.message || 'Erro desconhecido ao inicializar bot';
      connectionStatus = 'error';
      console.error('❌ Bot não iniciou automaticamente. Use POST /start para tentar novamente.');
    });
  }, 5000);
});

// Tratamento de erros do servidor
server.on('error', (err) => {
  console.error('❌ Erro no servidor Express:', err);
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Porta ${BOT_PORT} já está em uso!`);
    console.error(`❌ Tente usar uma porta diferente ou encerre o processo que está usando a porta ${BOT_PORT}`);
  }
  process.exit(1);
});

// Tratamento de desconexão
server.on('close', () => {
  console.log('⚠️ Servidor Express foi fechado');
});

// Exportar funções
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { sendMessage, initializeWhatsApp, disconnect };
}
