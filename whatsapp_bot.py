import subprocess
import time
import requests
import os
import logging
import json
import shutil
import signal
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WhatsAppBot')

class WhatsAppBot:
    def __init__(self):
        self.process = None
        self.port = 3000
        self.is_ready = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.start_time = None
        self.last_status = None
        self.qr_code = None
        self.status_message = None
        self.reconnect_timer = None
        self.session_path = os.path.join(os.path.dirname(__file__), 'whatsapp_bot', '.wwebjs_auth')
        self.backup_path = os.path.join(os.path.dirname(__file__), 'whatsapp_bot', 'session_backups')

    def _backup_session(self):
        """Faz backup da pasta de sessão do WhatsApp"""
        try:
            if not os.path.exists(self.session_path):
                logger.info("Nenhuma sessão para fazer backup")
                return False

            # Verificar se a sessão é válida antes de fazer backup
            if not self._is_session_valid():
                logger.warning("Sessão inválida, não será feito backup")
                return False

            # Criar pasta de backups se não existir
            if not os.path.exists(self.backup_path):
                os.makedirs(self.backup_path)

            # Nome do backup com timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'session_backup_{timestamp}'
            backup_dir = os.path.join(self.backup_path, backup_name)

            # Fazer backup
            shutil.copytree(self.session_path, backup_dir)
            logger.info(f"Backup da sessão criado em: {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Erro ao fazer backup da sessão: {str(e)}")
            return False

    def _restore_latest_session(self):
        """Restaura o backup mais recente da sessão"""
        try:
            if not os.path.exists(self.backup_path):
                logger.info("Nenhum backup disponível para restaurar")
                return False

            # Listar backups
            backups = [d for d in os.listdir(self.backup_path) 
                      if os.path.isdir(os.path.join(self.backup_path, d)) 
                      and d.startswith('session_backup_')]
            
            if not backups:
                logger.info("Nenhum backup encontrado")
                return False

            # Ordenar por data (mais recente primeiro)
            backups.sort(reverse=True)
            latest_backup = os.path.join(self.backup_path, backups[0])

            # Verificar se o backup é válido
            temp_session_path = os.path.join(self.backup_path, 'temp_session')
            try:
                # Copiar para uma pasta temporária primeiro
                shutil.copytree(latest_backup, temp_session_path)
                
                # Verificar se a estrutura é válida
                if not self._is_session_valid():
                    logger.warning("Backup inválido, não será restaurado")
                    shutil.rmtree(temp_session_path)
                    return False
                
                # Se chegou aqui, o backup é válido
                # Remover sessão atual se existir
                if os.path.exists(self.session_path):
                    shutil.rmtree(self.session_path)
                
                # Mover a pasta temporária para a localização final
                shutil.move(temp_session_path, self.session_path)
                logger.info(f"Sessão restaurada do backup: {latest_backup}")
                return True
            except Exception as e:
                logger.error(f"Erro ao restaurar sessão: {str(e)}")
                if os.path.exists(temp_session_path):
                    shutil.rmtree(temp_session_path)
                return False
        except Exception as e:
            logger.error(f"Erro ao restaurar sessão: {str(e)}")
            return False

    def _is_session_valid(self):
        """Verifica se a sessão atual é válida"""
        try:
            if not os.path.exists(self.session_path):
                logger.info("Pasta de sessão não encontrada")
                return False

            # Verificar estrutura da pasta de sessão
            session_dir = os.path.join(self.session_path, 'session')
            if not os.path.exists(session_dir):
                logger.info("Pasta 'session' não encontrada")
                return False

            # Verificar se existem as pastas essenciais
            required_dirs = ['Default', 'Crashpad']
            for dir_name in required_dirs:
                dir_path = os.path.join(session_dir, dir_name)
                if not os.path.exists(dir_path):
                    logger.info(f"Pasta essencial não encontrada: {dir_name}")
                    return False

            # Verificar se o arquivo DevToolsActivePort existe
            devtools_port = os.path.join(session_dir, 'DevToolsActivePort')
            if not os.path.exists(devtools_port):
                logger.info("Arquivo DevToolsActivePort não encontrado")
                return False

            # Verificar se a pasta Default contém os arquivos necessários
            default_dir = os.path.join(session_dir, 'Default')
            required_files = ['Cookies', 'Local Storage', 'Session Storage']
            for file_name in required_files:
                file_path = os.path.join(default_dir, file_name)
                if not os.path.exists(file_path):
                    logger.info(f"Arquivo/pasta essencial não encontrado em Default: {file_name}")
                    return False

            logger.info("Sessão válida encontrada")
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar sessão: {str(e)}")
            return False

    def start(self):
        try:
            # Verificar se já existe uma sessão válida
            if self._is_session_valid():
                logger.info("Usando sessão existente")
            else:
                # Tentar restaurar do backup mais recente
                if self._restore_latest_session():
                    logger.info("Sessão restaurada do backup")
                    if not self._is_session_valid():
                        logger.warning("Sessão restaurada não é válida")
                else:
                    logger.info("Nenhuma sessão válida encontrada, será necessário novo login")
            
            # Caminho para o arquivo server.js
            server_path = os.path.join(os.path.dirname(__file__), 'whatsapp_bot', 'server.js')
            
            logger.info("\n")
            logger.info("==================================================")
            logger.info("INICIANDO BOT DO WHATSAPP")
            logger.info("==================================================")
            logger.info("\n")
            
            # Iniciar o servidor Node.js
            self.process = subprocess.Popen(
                ['node', server_path, str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.start_time = time.time()
            
            # Iniciar thread para monitorar a saída do processo
            import threading
            threading.Thread(target=self._monitor_output, daemon=True).start()
            
            # Aguardar o servidor ficar pronto
            if self._wait_for_server():
                self.reconnect_attempts = 0
                logger.info("\n")
                logger.info("==================================================")
                logger.info("BOT INICIADO COM SUCESSO")
                logger.info("==================================================")
                logger.info("\n")
                return True
            
            logger.error("\n")
            logger.error("==================================================")
            logger.error("FALHA AO INICIAR BOT")
            logger.error("==================================================")
            logger.error("\n")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {str(e)}")
            return False

    def _monitor_output(self):
        """Monitora a saída do processo Node.js"""
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                try:
                    # Tentar interpretar a linha como JSON
                    data = json.loads(line)
                    
                    if data.get('type') == 'qr_code':
                        self.qr_code = data.get('qrCode')
                        self.status_message = data.get('message')
                        # Log para debug
                        logger.info(f"[DEBUG] QR Code recebido: {str(self.qr_code)[:60]}...")
                        logger.info(f"[DEBUG] Mensagem: {self.status_message}")
                        # Emitir sinal para a interface atualizar
                        if hasattr(self, 'qr_code_received'):
                            self.qr_code_received.emit(self.qr_code, self.status_message)
                    
                    elif data.get('type') == 'status':
                        status = data.get('status')
                        message = data.get('message')
                        self.status_message = message
                        
                        # Log detalhado do status
                        logger.info(f"\n[DEBUG] Status recebido: {status}")
                        logger.info(f"[DEBUG] Mensagem: {message}")
                        
                        # Tratar status específicos
                        if status == 'reconnecting':
                            logger.info(f"\nTentando reconectar... ({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                            # Verificar estado do cliente
                            try:
                                client_status = requests.get(f'http://localhost:{self.port}/api/client-status')
                                if client_status.status_code == 200:
                                    client_data = client_status.json()
                                    logger.info(f"[DEBUG] Estado do cliente: {client_data.get('state', 'desconhecido')}")
                                    logger.info(f"[DEBUG] Detalhes: {client_data.get('details', 'nenhum')}")
                            except Exception as e:
                                logger.error(f"[DEBUG] Erro ao verificar estado do cliente: {str(e)}")
                        elif status == 'error':
                            logger.error(f"\nErro: {message}")
                            self.reconnect_attempts += 1
                            if self.reconnect_attempts >= self.max_reconnect_attempts:
                                logger.error("\nNúmero máximo de tentativas de reconexão atingido")
                                self.stop()
                                return
                        
                        # Emitir sinal para a interface atualizar
                        if hasattr(self, 'status_changed'):
                            self.status_changed.emit(status, message)
                
                except json.JSONDecodeError:
                    # Se não for JSON, é um log normal
                    logger.debug(f"[DEBUG] Log normal: {line.strip()}")
                    pass

    def _wait_for_server(self):
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(f'http://localhost:{self.port}/api/status')
                if response.status_code == 200:
                    data = response.json()
                    current_status = data.get('status')
                    
                    # Log detalhado do status
                    logger.info(f"\nStatus atual: {current_status}")
                    logger.info(f"isReady: {data.get('isReady', False)}")
                    logger.info(f"hasQR: {data.get('hasQR', False)}")
                    
                    # Se o status mudou, mostrar mensagem
                    if current_status != self.last_status:
                        self.last_status = current_status
                        if current_status == 'qr_received':
                            logger.info("\n")
                            logger.info("==================================================")
                            logger.info("QR CODE GERADO - AGUARDANDO ESCANEAMENTO")
                            logger.info("==================================================")
                            logger.info("\n")
                        elif current_status == 'authenticated':
                            logger.info("\n")
                            logger.info("==================================================")
                            logger.info("AUTENTICADO - AGUARDANDO CONEXAO")
                            logger.info("==================================================")
                            logger.info("\n")
                    
                    if data.get('isReady'):
                        self.is_ready = True
                        return True
                    elif current_status == 'disconnected':
                        # Se desconectado, tentar reconectar
                        if self.reconnect_attempts < self.max_reconnect_attempts:
                            self.reconnect_attempts += 1
                            logger.info(f"\nTentativa de reconexao {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                            
                            # Verificar estado do cliente antes de reconectar
                            try:
                                client_status = requests.get(f'http://localhost:{self.port}/api/client-status')
                                if client_status.status_code == 200:
                                    client_data = client_status.json()
                                    logger.info(f"Estado do cliente: {client_data.get('state', 'desconhecido')}")
                                    logger.info(f"Detalhes: {client_data.get('details', 'nenhum')}")
                            except Exception as e:
                                logger.error(f"Erro ao verificar estado do cliente: {str(e)}")
                            
                            # Tentar reinicializar o cliente
                            try:
                                logger.info("Tentando reinicializar o cliente...")
                                init_response = requests.post(f'http://localhost:{self.port}/api/initialize')
                                if init_response.status_code == 200:
                                    logger.info("Cliente reinicializado com sucesso")
                                else:
                                    logger.error(f"Erro ao reinicializar cliente: {init_response.text}")
                            except Exception as e:
                                logger.error(f"Erro ao reinicializar cliente: {str(e)}")
                            
                            time.sleep(5)  # Aguardar 5 segundos antes de tentar novamente
                            continue
            except requests.exceptions.ConnectionError:
                logger.error("Erro de conexão com o servidor")
                pass
            
            retry_count += 1
            time.sleep(2)
        
        logger.error("\n")
        logger.error("Timeout aguardando servidor ficar pronto")
        return False

    def stop(self, remove_session=False):
        if self.process:
            try:
                logger.info("\n")
                logger.info("Encerrando bot do WhatsApp...")
                
                # Fazer backup da sessão antes de encerrar
                if not remove_session:
                    if self._is_session_valid():
                        self._backup_session()
                    else:
                        logger.warning("Sessão inválida, pulando backup")
                
                # Enviar sinal SIGINT para encerrar de forma limpa
                try:
                    self.process.send_signal(signal.SIGINT)
                except Exception:
                    self.process.terminate()
                self.process.wait(timeout=5)  # Aguardar até 5 segundos
                logger.info("Bot do WhatsApp encerrado com sucesso")
            except subprocess.TimeoutExpired:
                # Se não conseguir encerrar limpo, forçar o encerramento
                logger.warning("Forçando encerramento do bot...")
                self.process.kill()
            self.is_ready = False
            self.reconnect_attempts = 0
            self.last_status = None
            self.qr_code = None
            self.status_message = None
            
            # Remover a pasta de sessão SOMENTE se remove_session=True
            if remove_session:
                if os.path.exists(self.session_path):
                    try:
                        shutil.rmtree(self.session_path)
                        logger.info("Pasta .wwebjs_auth removida com sucesso.")
                    except Exception as e:
                        logger.error(f"Erro ao remover a pasta .wwebjs_auth: {str(e)}")

    def restart(self):
        logger.info("\n")
        logger.info("Reiniciando bot do WhatsApp...")
        self.stop()
        time.sleep(2)  # Aguardar um pouco antes de reiniciar
        return self.start()

    def check_status(self):
        try:
            response = requests.get(f'http://localhost:{self.port}/api/status')
            if response.status_code == 200:
                data = response.json()
                return data.get('isReady', False)
        except:
            pass
        return False 