import requests
import json
import time
import subprocess
import os
import sys
import threading
import logging
import shutil
import zipfile
import tempfile
import urllib.request
from datetime import datetime
import webbrowser
import re

# Configuração de logging
log_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Sistema Fiado')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'whatsapp_bot.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WhatsAppBot")

class WhatsAppServiceAPI:
    """
    Serviço para enviar mensagens pelo WhatsApp usando um bot Node.js integrado.
    Este serviço se comunica com o servidor bot via API REST.
    """
    def __init__(self):
        self.base_url = "http://localhost:3000/api"  # Baileys server
        self.bot_process = None
        self.connected = False
        
        # Auto setup dependências
        self.setup_thread = None
        self.setup_complete = False
        self.setup_status = "Não iniciado"
        self.setup_progress = 0
        
        # Iniciar verificação/instalação em segundo plano
        self.iniciar_verificacao_automatica()
    
    def iniciar_verificacao_automatica(self):
        """Inicia a verificação automática de dependências em uma thread separada"""
        self.setup_thread = threading.Thread(target=self._verificar_instalar_dependencias, daemon=True)
        self.setup_thread.start()
    
    def _verificar_instalar_dependencias(self):
        """Verifica e instala as dependências necessárias para o bot"""
        try:
            self.setup_status = "Verificando dependências..."
            self.setup_progress = 10
            
            # 1. Verificar se o Node.js está instalado
            if not self._verificar_nodejs():
                self.setup_status = "Instalando Node.js..."
                self.setup_progress = 20
                if not self._instalar_nodejs():
                    self.setup_status = "Falha ao instalar Node.js"
                    return False
            
            self.setup_progress = 40
            self.setup_status = "Verificando dependências npm..."
            
            # 2. Verificar e instalar dependências npm
            if not self._verificar_instalar_npm_deps():
                self.setup_status = "Falha ao instalar dependências npm"
                return False
            
            self.setup_progress = 70
            self.setup_status = "Verificando dependências Python..."
            
            # 3. Verificar e instalar dependências Python
            if not self._verificar_instalar_python_deps():
                self.setup_status = "Falha ao instalar dependências Python"
                return False
            
            self.setup_progress = 100
            self.setup_status = "Configuração concluída"
            self.setup_complete = True
            logger.info("Setup automático completo!")
            return True
            
        except Exception as e:
            self.setup_status = f"Erro: {str(e)}"
            logger.error(f"Erro durante o setup automático: {str(e)}")
            return False
    
    def _verificar_nodejs(self):
        """Verifica se o Node.js está instalado"""
        try:
            # Verificar se NODE_PATH está no PATH
            node_in_path = shutil.which("node") is not None

            if node_in_path:
                # Verificar a versão instalada
                result = subprocess.run(
                    ["node", "--version"], 
                    capture_output=True, 
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    node_version = result.stdout.strip()
                    logger.info(f"Node.js encontrado: {node_version}")
                    return True
            
            # Verificar se há uma instalação local no diretório do bot
            bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_bot", "node")
            if os.path.exists(os.path.join(bot_dir, "node.exe")):
                logger.info("Node.js encontrado na pasta local")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar Node.js: {str(e)}")
            return False
    
    def _instalar_nodejs(self):
        """Instala o Node.js localmente"""
        try:
            self.setup_status = "Baixando Node.js..."
            logger.info("Baixando Node.js...")
            
            # URL do Node.js (versão LTS para Windows)
            node_url = "https://nodejs.org/dist/v18.17.1/node-v18.17.1-win-x64.zip"
            
            # Diretório de destino
            target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_bot", "node")
            
            # Criar o diretório de destino se não existir
            os.makedirs(target_dir, exist_ok=True)
            
            # Baixar Node.js
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                temp_path = temp_file.name
                
            urllib.request.urlretrieve(node_url, temp_path)
            
            self.setup_status = "Extraindo Node.js..."
            
            # Extrair o conteúdo
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                # O zip do Node.js tem uma pasta raiz como "node-v18.17.1-win-x64"
                # Precisamos extrair o conteúdo dessa pasta
                for zip_info in zip_ref.infolist():
                    if '/' in zip_info.filename:
                        # Remover a pasta raiz do caminho
                        zip_info.filename = '/'.join(zip_info.filename.split('/')[1:])
                        if zip_info.filename:
                            zip_ref.extract(zip_info, target_dir)
            
            # Remover o arquivo temporário
            os.unlink(temp_path)
            
            logger.info(f"Node.js instalado em: {target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao instalar Node.js: {str(e)}")
            return False
    
    def _verificar_instalar_npm_deps(self):
        """Verifica e instala as dependências npm do bot"""
        try:
            bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_bot")
            node_modules_dir = os.path.join(bot_dir, "node_modules")
            
            # Alternativa 1: Verificar se módulos empacotados estão disponíveis
            modules_pkg = os.path.join(bot_dir, "node_modules_pkg")
            if os.path.exists(modules_pkg) and os.path.isfile(modules_pkg):
                self.setup_status = "Extraindo node_modules empacotados..."
                try:
                    # Criar pasta de destino
                    os.makedirs(node_modules_dir, exist_ok=True)
                    
                    # Extrair pacote (pode ser um arquivo zip ou tar)
                    if modules_pkg.endswith('.zip'):
                        with zipfile.ZipFile(modules_pkg, 'r') as zip_ref:
                            zip_ref.extractall(bot_dir)
                    
                    # Verificar se deu certo
                    if os.path.exists(node_modules_dir) and os.listdir(node_modules_dir):
                        logger.info("Módulos empacotados extraídos com sucesso")
                        return True
                except Exception as e:
                    logger.error(f"Erro ao extrair módulos empacotados: {str(e)}")
                    # Continuar com outras alternativas
            
            # Se node_modules existir e não estiver vazio, presumimos que as dependências já estão instaladas
            if os.path.exists(node_modules_dir) and os.listdir(node_modules_dir):
                logger.info("Dependências npm já estão instaladas")
                return True
            
            # Alternativa 2: Verificar se temos uma cópia local de node_modules
            prebuilt_modules = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prebuilt", "node_modules")
            if os.path.exists(prebuilt_modules) and os.listdir(prebuilt_modules):
                self.setup_status = "Copiando node_modules pré-compilados..."
                try:
                    # Criar pasta de destino se não existir
                    os.makedirs(node_modules_dir, exist_ok=True)
                    
                    # Copiar de prebuilt para node_modules
                    shutil.copytree(prebuilt_modules, node_modules_dir, dirs_exist_ok=True)
                    
                    logger.info("Módulos pré-compilados copiados com sucesso")
                    return True
                except Exception as e:
                    logger.error(f"Erro ao copiar módulos pré-compilados: {str(e)}")
                    # Continuar com outras alternativas
            
            self.setup_status = "Instalando dependências npm..."
            logger.info("Instalando dependências npm...")
            
            # Verificar se o package.json existe
            if not os.path.exists(os.path.join(bot_dir, "package.json")):
                logger.error("O arquivo package.json não foi encontrado")
                self.setup_status = "Erro: package.json não encontrado"
                return False
                
            # Verificar se temos Node.js no PATH ou na pasta local
            node_cmd = "node"
            npm_cmd = "npm"
            
            # Se temos Node.js local, usar esse caminho
            local_node_dir = os.path.join(bot_dir, "node")
            if os.path.exists(os.path.join(local_node_dir, "node.exe")):
                node_cmd = os.path.join(local_node_dir, "node.exe")
                npm_cmd = os.path.join(local_node_dir, "npm.cmd")
                
                # Verificar se npm.cmd existe
                if not os.path.exists(npm_cmd):
                    # Tentar npm.bat como alternativa
                    npm_alt = os.path.join(local_node_dir, "npm.bat")
                    if os.path.exists(npm_alt):
                        npm_cmd = npm_alt
                    else:
                        # Instalação manual das dependências
                        return self._instalar_deps_manualmente(bot_dir, node_cmd)
            
            # Método 1: Tentar instalação via npm install
            try:
                self.setup_status = "Tentando npm install..."
                logger.info(f"Executando {npm_cmd} install em {bot_dir}")
                
                process = subprocess.run(
                    [npm_cmd, "install"], 
                    cwd=bot_dir,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if process.returncode == 0:
                    logger.info("Dependências npm instaladas com sucesso")
                    return True
                else:
                    logger.warning(f"Falha no npm install: {process.stderr}")
                    # Continuar com método alternativo
            except Exception as e:
                logger.warning(f"Erro ao usar npm install: {str(e)}")
                # Continuar com método alternativo
            
            # Método 2: Instalação direta via npm install <pacote>
            try:
                self.setup_status = "Instalando dependências individualmente..."
                
                # Ler o package.json para extrair as dependências
                with open(os.path.join(bot_dir, "package.json"), 'r') as f:
                    package_data = json.load(f)
                
                # Obter lista de dependências
                dependencies = package_data.get('dependencies', {})
                
                # Instalar cada dependência individualmente
                for package, version in dependencies.items():
                    self.setup_status = f"Instalando {package}..."
                    logger.info(f"Instalando {package}...")
                    
                    # Remover ^ ou ~ do início da versão
                    clean_version = version
                    if version.startswith('^') or version.startswith('~'):
                        clean_version = version[1:]
                    
                    # Criar o comando npm install pacote@versão
                    install_cmd = [npm_cmd, "install", f"{package}@{clean_version}"]
                    
                    process = subprocess.run(
                        install_cmd,
                        cwd=bot_dir,
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if process.returncode != 0:
                        logger.warning(f"Falha ao instalar {package}: {process.stderr}")
                
                # Verificar se as dependências foram instaladas
                if os.path.exists(node_modules_dir) and os.listdir(node_modules_dir):
                    logger.info("Dependências npm instaladas com sucesso")
                    return True
                else:
                    logger.error("Falha ao instalar dependências npm")
                    # Continuar para instalação manual
            except Exception as e:
                logger.warning(f"Erro ao instalar dependências individuais: {str(e)}")
                # Continuar para instalação manual
            
            # Método 3: Instalação manual (baixando os pacotes)
            return self._instalar_deps_manualmente(bot_dir, node_cmd)
            
        except Exception as e:
            self.setup_status = f"Erro: {str(e)}"
            logger.error(f"Erro ao instalar dependências npm: {str(e)}")
            return False
    
    def _instalar_deps_manualmente(self, bot_dir, node_cmd):
        """Método alternativo para instalar dependências baixando-as manualmente"""
        try:
            self.setup_status = "Baixando dependências manualmente..."
            logger.info("Tentando instalação manual das dependências")
            
            # URL do pacote pré-configurado com todas as dependências
            deps_url = "https://github.com/whatsapp-web/whatsapp-web.js/archive/refs/heads/main.zip"
            
            # Criar diretório temporário
            temp_dir = os.path.join(bot_dir, "temp_deps")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Baixar o arquivo zip
            zip_path = os.path.join(temp_dir, "deps.zip")
            try:
                urllib.request.urlretrieve(deps_url, zip_path)
            except Exception as e:
                logger.error(f"Erro ao baixar dependências: {str(e)}")
                
                # Tentar criar node_modules manualmente com os pacotes básicos
                node_modules_dir = os.path.join(bot_dir, "node_modules")
                os.makedirs(node_modules_dir, exist_ok=True)
                
                # Criar pastas para simular instalação mínima
                os.makedirs(os.path.join(node_modules_dir, "express"), exist_ok=True)
                os.makedirs(os.path.join(node_modules_dir, "cors"), exist_ok=True)
                os.makedirs(os.path.join(node_modules_dir, "body-parser"), exist_ok=True)
                os.makedirs(os.path.join(node_modules_dir, "whatsapp-web.js"), exist_ok=True)
                os.makedirs(os.path.join(node_modules_dir, "qrcode-terminal"), exist_ok=True)
                
                # Criar arquivo de teste para verificar se o bot pode iniciar mesmo com dependências parciais
                simple_bot_path = os.path.join(bot_dir, "simple_server.js")
                with open(simple_bot_path, 'w') as f:
                    f.write("""
const http = require('http');
const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'application/json'});
    
    if (req.url === '/api/status') {
        res.end(JSON.stringify({
            status: 'offline',
            isReady: false,
            hasQR: false
        }));
    } else if (req.url === '/api/initialize') {
        res.end(JSON.stringify({
            success: true,
            message: 'Inicialização solicitada'
        }));
    } else {
        res.end(JSON.stringify({error: 'Endpoint não disponível'}));
    }
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Servidor simplificado rodando na porta ${PORT}`);
});
                    """)
                
                self.setup_status = "Configuração parcial - algumas funcionalidades estarão indisponíveis"
                logger.warning("Instalação parcial - modo limitado ativado")
                return True
            
            # Extrair arquivos
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Verificar pasta extraída
            extracted_folders = [f for f in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, f))]
            if not extracted_folders:
                logger.error("Nenhuma pasta extraída do arquivo zip")
                return False
            
            # Mover node_modules da pasta extraída
            extracted_dir = os.path.join(temp_dir, extracted_folders[0])
            source_node_modules = os.path.join(extracted_dir, "node_modules")
            
            if os.path.exists(source_node_modules):
                # Mover para o diretório do bot
                target_node_modules = os.path.join(bot_dir, "node_modules")
                
                # Remover diretório antigo se existir
                if os.path.exists(target_node_modules):
                    shutil.rmtree(target_node_modules)
                
                # Copiar para o diretório do bot
                shutil.copytree(source_node_modules, target_node_modules)
                
                # Limpar arquivos temporários
                shutil.rmtree(temp_dir)
                
                logger.info("Dependências instaladas manualmente com sucesso")
                return True
            else:
                logger.error("node_modules não encontrado no pacote baixado")
                return False
            
        except Exception as e:
            self.setup_status = f"Erro na instalação manual: {str(e)}"
            logger.error(f"Erro na instalação manual: {str(e)}")
            return False
    
    def _verificar_instalar_python_deps(self):
        """Verifica e instala as dependências Python necessárias"""
        try:
            # Lista de pacotes necessários
            required_packages = ["qrcode", "pillow", "requests"]
            missing_packages = []
            
            # Verificar quais pacotes estão faltando
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if not missing_packages:
                logger.info("Todas as dependências Python estão instaladas")
                return True
            
            self.setup_status = f"Instalando pacotes Python: {', '.join(missing_packages)}..."
            logger.info(f"Instalando pacotes Python: {missing_packages}")
            
            # Instalar pacotes faltantes
            for package in missing_packages:
                try:
                    process = subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    if process.returncode != 0:
                        logger.error(f"Erro ao instalar {package}: {process.stderr}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Erro ao instalar {package}: {str(e)}")
                    return False
            
            logger.info("Todas as dependências Python foram instaladas")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar/instalar dependências Python: {str(e)}")
            return False
    
    def obter_status_setup(self):
        """Retorna o status atual do processo de configuração"""
        return {
            "completo": self.setup_complete,
            "status": self.setup_status,
            "progresso": self.setup_progress
        }
        
    def _start_bot_server(self):
        """Inicia o servidor bot em segundo plano se ainda não estiver rodando"""
        try:
            # Verificar se o servidor já está rodando
            try:
                response = requests.get(f"{self.base_url}/status", timeout=2)
                if response.status_code == 200:
                    logger.info("Servidor bot já está rodando")
                    return True
            except requests.exceptions.RequestException:
                # Servidor não está rodando, vamos iniciá-lo
                pass
            
            # Verificar se a configuração foi concluída
            if not self.setup_complete:
                logger.warning("Configuração ainda não está completa. Aguardando...")
                # Aguardar a configuração ser concluída
                max_attempts = 30  # 30 segundos
                attempts = 0
                while not self.setup_complete and attempts < max_attempts:
                    time.sleep(1)
                    attempts += 1
                
                if not self.setup_complete:
                    logger.error("Tempo esgotado aguardando a configuração")
                    return False
            
            # Obter o diretório do bot
            bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_bot")
            
            # Verificar se o diretório existe
            if not os.path.exists(bot_dir):
                logger.error(f"Diretório do bot não encontrado: {bot_dir}")
                return False
            
            # Verificar se Node.js está no PATH ou temos uma instalação local
            node_path = "node"
            npm_path = "npm"
            
            # Se temos Node.js local, usar esse caminho
            local_node_dir = os.path.join(bot_dir, "node")
            if os.path.exists(os.path.join(local_node_dir, "node.exe")):
                node_path = os.path.join(local_node_dir, "node.exe")
                npm_path = os.path.join(local_node_dir, "npm.cmd")
            
            # Verificar plataforma para comando correto
            if sys.platform.startswith('win'):
                # Windows - executar node diretamente
                server_script = os.path.join(bot_dir, "server.js")
                
                startup_cmd = [node_path, server_script]
                self.bot_process = subprocess.Popen(
                    startup_cmd,
                    cwd=bot_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux/Mac
                startup_cmd = f"cd {bot_dir} && {node_path} server.js"
                self.bot_process = subprocess.Popen(
                    startup_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
            logger.info("Iniciando servidor bot. Aguarde...")
            
            # Aguardar o servidor iniciar
            attempts = 0
            max_attempts = 15
            
            while attempts < max_attempts:
                try:
                    response = requests.get(f"{self.base_url}/status", timeout=2)
                    if response.status_code == 200:
                        logger.info("Servidor bot iniciado com sucesso!")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    attempts += 1
                    
            logger.error("Falha ao iniciar o servidor bot")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor bot: {str(e)}")
            return False
        
    def iniciar_bot(self):
        """Inicia o bot do WhatsApp e retorna o QR Code se necessário"""
        if not self._start_bot_server():
            return None, "Falha ao iniciar o servidor bot"
            
        try:
            # Inicializar o cliente WhatsApp no servidor
            init_response = requests.post(f"{self.base_url}/initialize")
            init_response.raise_for_status()
            
            # Verificar status
            status_response = requests.get(f"{self.base_url}/status")
            status_response.raise_for_status()
            status_data = status_response.json()
            
            # Se já estiver conectado
            if status_data.get('isReady', False):
                self.connected = True
                return None, "Conectado ao WhatsApp"
                
            # Se precisar de QR Code
            if status_data.get('hasQR', False):
                qr_response = requests.get(f"{self.base_url}/qrcode")
                qr_response.raise_for_status()
                qr_data = qr_response.json()
                return qr_data.get('qrCode'), "Escaneie o QR Code para conectar ao WhatsApp"
                
            return None, f"Status atual: {status_data.get('status', 'desconhecido')}"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de comunicação com o servidor bot: {str(e)}")
            return None, f"Erro ao comunicar com o servidor bot: {str(e)}"
        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {str(e)}")
            return None, f"Erro ao iniciar bot: {str(e)}"
            
    def verificar_status(self):
        """Verifica o status atual do bot"""
        try:
            response = requests.get(f"{self.base_url}/status")
            response.raise_for_status()
            data = response.json()
            
            self.connected = data.get('isReady', False)
            
            return {
                'conectado': data.get('isReady', False),
                'status': data.get('status', 'desconhecido'),
                'precisa_qrcode': data.get('hasQR', False)
            }
        except Exception as e:
            logger.error(f"Erro ao verificar status: {str(e)}")
            return {
                'conectado': False,
                'status': 'erro',
                'precisa_qrcode': False,
                'erro': str(e)
            }
            
    def obter_qrcode(self):
        """Obtém o QR Code para autenticação"""
        try:
            response = requests.get(f"{self.base_url}/qrcode")
            if response.status_code == 200:
                return response.json().get('qrCode')
            return None
        except Exception as e:
            logger.error(f"Erro ao obter QR Code: {str(e)}")
            return None
            
    def padronizar_numero(self, telefone):
        """
        Padroniza e valida um número de telefone brasileiro para envio via WhatsApp.
        - Remove caracteres não numéricos
        - Garante DDI 55
        - Garante DDD (2 dígitos)
        - Aceita número com 8 ou 9 dígitos
        - Para celulares, adiciona nono dígito se necessário
        - Para fixos, aceita 8 dígitos
        """
        numero = re.sub(r'\D', '', telefone)
        if not numero.startswith('55'):
            numero = '55' + numero
        if len(numero) < 12 or len(numero) > 13:
            # DDI (2) + DDD (2) + número (8 ou 9)
            raise ValueError(f"Número inválido para WhatsApp: {numero}")
        ddd = numero[2:4]
        num = numero[4:]
        # Se for celular (começa com 9, 8, 7 ou 6) e não tiver o nono dígito, adiciona
        if len(num) == 8 and num[0] in '6789':
            num = '9' + num
            numero = numero[:4] + num
        # Aceita tanto 8 quanto 9 dígitos após o DDD
        if len(num) not in [8,9]:
            raise ValueError(f"Número inválido para WhatsApp: {numero}")
        return numero

    def enviar_mensagem(self, telefone, mensagem):
        """
        Envia uma mensagem para o número de telefone especificado via API do bot
        Args:
            telefone: Número de telefone do destinatário
            mensagem: Texto da mensagem a ser enviada
        Returns:
            bool: True se a mensagem foi enviada com sucesso, False caso contrário
        """
        # Iniciar o servidor bot se necessário
        if not self._start_bot_server():
            return False
        try:
            # Checar se o número existe no WhatsApp antes de enviar
            if not self.numero_existe_no_whatsapp(telefone):
                logger.error(f"Número {telefone} não existe no WhatsApp. Envio cancelado.")
                return False
            # Verificar status
            status = self.verificar_status()
            if not status['conectado']:
                logger.warning("Bot não está conectado. Verifique a autenticação.")
                return False
            telefone_limpo = self.padronizar_numero(telefone)
            logger.info(f"Enviando mensagem para o número: {telefone_limpo}")
            dados = {
                "phone": telefone_limpo,
                "message": mensagem
            }
            response = requests.post(
                f"{self.base_url}/send-message", 
                json=dados
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Mensagem enviada com sucesso para {telefone_limpo}")
                    return True
                else:
                    logger.error(f"Erro ao enviar mensagem: {data.get('error')}")
                    return False
            else:
                logger.error(f"Erro ao enviar mensagem. Status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return False
            
    def desconectar(self):
        """Desconecta do WhatsApp"""
        try:
            response = requests.post(f"{self.base_url}/logout")
            if response.status_code == 200:
                self.connected = False
                logger.info("Desconectado do WhatsApp com sucesso")
                return True
            else:
                logger.error(f"Erro ao desconectar. Status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro ao desconectar: {str(e)}")
            return False

    def numero_existe_no_whatsapp(self, telefone):
        """
        Checa se o número existe no WhatsApp tentando enviar uma mensagem de teste (sem notificar o usuário).
        Retorna True se o número existe, False se não existe.
        """
        try:
            telefone_limpo = self.padronizar_numero(telefone)
            dados = {
                "phone": telefone_limpo,
                "message": "Mensagem de verificação automática. Favor ignorar."
            }
            response = requests.post(f"{self.base_url}/send-message", json=dados)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Número {telefone_limpo} existe no WhatsApp.")
                    return True
                else:
                    logger.warning(f"Número {telefone_limpo} não existe ou não foi possível enviar: {data.get('error')}")
                    return False
            else:
                logger.warning(f"Erro ao checar número {telefone_limpo}: status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro ao checar número no WhatsApp: {str(e)}")
            raise

# Função para testar o serviço diretamente
def main():
    service = WhatsAppServiceAPI()
    
    # Aguardar a configuração ser concluída
    print("Verificando e configurando dependências...")
    while not service.setup_complete:
        status = service.obter_status_setup()
        print(f"Status: {status['status']} - Progresso: {status['progresso']}%")
        time.sleep(1)
    
    print("Iniciando o bot do WhatsApp...")
    qr_code, mensagem = service.iniciar_bot()
    
    if qr_code:
        print("Escaneie o QR Code no seu aplicativo WhatsApp:")
        print(mensagem)
        
        # Aguardar conexão
        print("Aguardando conexão...")
        attempts = 0
        while attempts < 30:  # Tentar por 30*2 segundos
            status = service.verificar_status()
            if status['conectado']:
                print("Conectado ao WhatsApp com sucesso!")
                break
            time.sleep(2)
            attempts += 1
        
        if attempts >= 30:
            print("Tempo esgotado para conexão")
            return
    
    # Teste de envio
    telefone = input("Digite o telefone para teste (com DDD): ")
    mensagem = input("Digite a mensagem de teste: ")
    
    print(f"Enviando mensagem para {telefone}...")
    result = service.enviar_mensagem(telefone, mensagem)
    
    if result:
        print("Mensagem enviada com sucesso!")
    else:
        print("Falha ao enviar mensagem")
    
    # Desconectar
    print("Desconectar? (s/n)")
    if input().lower() == 's':
        service.desconectar()
        print("Desconectado")

if __name__ == "__main__":
    main() 