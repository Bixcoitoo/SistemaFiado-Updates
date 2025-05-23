import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QFrame, QSizePolicy, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, Property, QRect, QEvent, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import QFont, QIcon, QPixmap
import subprocess
import time
import requests
import os
import logging
import json

from database import Database
from views.cliente_view import ClienteView
from views.lista_clientes_view import ListaClientesView
from views.venda_view import VendaView
from views.historico_vendas_view import HistoricoVendasView
from views.relatorio_view import RelatorioView
from views.config_view import ConfigView
from views.home_view import HomeView
from views.detalhe_cliente_view import DetalheClienteView
from views.notificacoes_view import NotificacoesView
from views.whatsapp_bot_view import WhatsAppBotView
from styles import STYLE
from updater import UpdateChecker, UpdateDialog, UpdateProgressDialog

# Configurar logging
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

    def start(self):
        try:
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
                        # Emitir sinal para a interface atualizar
                        if hasattr(self, 'qr_code_received'):
                            self.qr_code_received.emit(self.qr_code, self.status_message)
                    
                    elif data.get('type') == 'status':
                        status = data.get('status')
                        message = data.get('message')
                        self.status_message = message
                        
                        # Tratar status específicos
                        if status == 'reconnecting':
                            logger.info(f"\nTentando reconectar... ({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
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
                            time.sleep(5)  # Aguardar 5 segundos antes de tentar novamente
                            continue
            except requests.exceptions.ConnectionError:
                pass
            
            retry_count += 1
            time.sleep(2)
        
        logger.error("\n")
        logger.error("Timeout aguardando servidor ficar pronto")
        return False

    def stop(self):
        if self.process:
            try:
                logger.info("\n")
                logger.info("Encerrando bot do WhatsApp...")
                # Tentar encerrar o processo de forma limpa
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

# Função utilitária para carregar ícones
def icon_path(name):
    return os.path.join(os.path.dirname(__file__), 'icons', name)

class MenuButton(QPushButton):
    def __init__(self, text, icon_file=None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(48)
        self.setFont(QFont('Segoe UI', 11))
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if icon_file:
            self.setIcon(QIcon(icon_path(icon_file)))
            self.setIconSize(QSize(22, 22))

class AnimatedButton(QPushButton):
    def __init__(self, icon_file=None, tooltip="", parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(icon_path(icon_file)))
        self.setIconSize(QSize(22, 22))
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        
        # Configurações de animação
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Estado inicial
        self._hover = False
        self._rotation = 0
        
    def enterEvent(self, event):
        # Quando o mouse entrar no botão
        rect = self.geometry()
        self._animation.setStartValue(rect)
        
        # Aumentar o tamanho
        new_rect = QRect(rect.x()-2, rect.y()-2, rect.width()+4, rect.height()+4)
        self._animation.setEndValue(new_rect)
        self._animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        # Quando o mouse sair do botão
        rect = self.geometry()
        self._animation.setStartValue(rect)
        
        # Voltar ao tamanho original
        new_rect = QRect(rect.x()+2, rect.y()+2, rect.width()-4, rect.height()-4)
        self._animation.setEndValue(new_rect)
        self._animation.start()
        super().leaveEvent(event)

class SistemaFiado(QMainWindow):
    def __init__(self):
        super().__init__(flags=Qt.FramelessWindowHint)
        self.db = Database()
        self.init_ui()
        self.carregar_configuracoes()
        # Configurar versão atual
        self.current_version = "1.0.0"
        # Inicializar verificador de atualizações
        self.update_checker = UpdateChecker(self.current_version)
        self.update_checker.update_available.connect(self.show_update_dialog)
        self.update_checker.update_error.connect(self.show_update_error)
        self.update_checker.download_progress.connect(self.update_progress)
        self.update_checker.download_complete.connect(self.install_update)
        # Controle para não buscar atualização mais de uma vez
        self._att_checked = False
    
    def closeEvent(self, event):
        """Evento chamado quando o programa está sendo fechado"""
        try:
            # Fazer backup do banco de dados
            sucesso, mensagem = self.db.fazer_backup_automatico()
            if sucesso:
                print(f"Backup realizado com sucesso ao fechar o programa: {mensagem}")
            else:
                print(f"Erro ao fazer backup ao fechar o programa: {mensagem}")
        except Exception as e:
            print(f"Erro ao fazer backup ao fechar o programa: {str(e)}")
        
        # Aceitar o evento de fechamento
        event.accept()
    
    def carregar_configuracoes(self):
        """Carrega as configurações salvas"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Encontrar e configurar a visibilidade dos botões
                    for button in self.findChildren(QPushButton):
                        if button.text() == "Bot de WhatsApp":
                            button.setVisible(not config.get('ocultar_whatsapp', False))
                        elif button.text() == "Notificações de Pagamento":
                            button.setVisible(not config.get('ocultar_notificacoes', False))
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {str(e)}")
    
    def changeEvent(self, event):
        # Permitir que a janela seja minimizada quando o botão for clicado
        if event.type() == QEvent.Type.WindowStateChange:
            # Não fazemos nada aqui para permitir a minimização
            pass
        super().changeEvent(event)
    
    def moveEvent(self, event):
        # Garantir que a janela permaneça maximizada
        if not self.isMaximized():
            self.showMaximized()
        super().moveEvent(event)
    
    def resizeEvent(self, event):
        # Garantir que a janela permaneça maximizada
        if not self.isMaximized():
            self.showMaximized()
        super().resizeEvent(event)
    
    def init_ui(self):
        self.setWindowTitle("Sistema de Fiado")
        self.setMinimumSize(1200, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de título personalizada
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(50)
        self.title_bar.setStyleSheet("""
            #TitleBar {
                background-color: #1e293b;
                border-bottom: 1px solid #34495e;
            }
        """)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        # Logo pequeno na barra de título
        title_logo = QLabel()
        title_logo.setPixmap(QIcon(icon_path("ICONE-LOGO.png")).pixmap(QSize(120, 35)))
        title_layout.addWidget(title_logo)
        
        # Título da janela
        title_label = QLabel("Sistema de Fiado")
        title_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Botão de minimizar
        btn_minimize = QPushButton("–")
        btn_minimize.setObjectName("MinimizeButton")
        btn_minimize.setFixedSize(40, 40)
        btn_minimize.setStyleSheet("""
            #MinimizeButton {
                color: white;
                background: transparent;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
            }
            #MinimizeButton:hover {
                background: #3498db;
            }
        """)
        btn_minimize.clicked.connect(self.showMinimized)
        title_layout.addWidget(btn_minimize)
        
        # Botão de fechar
        btn_close = QPushButton("×")
        btn_close.setObjectName("CloseButton")
        btn_close.setFixedSize(40, 40)
        btn_close.setStyleSheet("""
            #CloseButton {
                color: white;
                background: transparent;
                font-size: 20px;
                border: none;
                border-radius: 20px;
            }
            #CloseButton:hover {
                background: #e74c3c;
            }
        """)
        btn_close.clicked.connect(self.close)
        title_layout.addWidget(btn_close)
        
        main_layout.addWidget(self.title_bar)
        
        # Área de conteúdo principal (com menu lateral e conteúdo)
        main_content = QWidget()
        content_layout = QHBoxLayout(main_content)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Menu lateral
        menu_frame = QFrame()
        menu_frame.setObjectName("MenuLateral")
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setSpacing(0)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo
        logo_frame = QFrame()
        logo_frame.setObjectName("LogoArea")
        logo_frame.setFixedHeight(150)

        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_img = QLabel()
        logo_img.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(icon_path("BANER-FIADO.png"))
        pixmap = pixmap.scaledToHeight(120, Qt.SmoothTransformation)
        logo_img.setPixmap(pixmap)
        logo_layout.addWidget(logo_img)
        menu_layout.addWidget(logo_frame)
        
        # Container para os botões do menu
        buttons_container = QFrame()
        buttons_container.setObjectName("MenuButtonsContainer")
        buttons_container.setStyleSheet("background: transparent;")
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(12, 20, 12, 20)
        
        # Botões do menu
        btn_novo_cliente = MenuButton("Novo Cliente", "user-add.svg")
        btn_novo_cliente.setProperty("colorClass", "Verde")

        btn_lista_clientes = MenuButton("Lista de Clientes", "users.svg")
        btn_lista_clientes.setProperty("colorClass", "Vermelho")

        btn_registrar_venda = MenuButton("Registrar Venda", "shopping-cart.svg")
        btn_registrar_venda.setProperty("colorClass", "Amarelo")

        btn_relatorios = MenuButton("Relatórios", "pie-chart.svg")
        btn_relatorios.setProperty("colorClass", "Roxo")
        
        btn_historico = MenuButton("Histórico de Vendas", "history.svg")
        btn_historico.setProperty("colorClass", "Azul")
        
        btn_notificacoes = MenuButton("Notificações de Pagamento", "bell.svg")
        btn_notificacoes.setProperty("colorClass", "Laranja")

        btn_whatsapp_bot = MenuButton("Bot de WhatsApp", "message-circle.svg")
        btn_whatsapp_bot.setProperty("colorClass", "Verde")

        buttons_layout.addWidget(btn_novo_cliente)
        buttons_layout.addWidget(btn_lista_clientes)
        buttons_layout.addWidget(btn_registrar_venda)
        buttons_layout.addWidget(btn_relatorios)
        buttons_layout.addWidget(btn_historico)
        buttons_layout.addWidget(btn_notificacoes)
        buttons_layout.addWidget(btn_whatsapp_bot)
        buttons_layout.addStretch()
        
        menu_layout.addWidget(buttons_container)
        
        # Área de opções no final
        options_frame = QFrame()
        options_frame.setStyleSheet("background: transparent;")
        options_layout = QHBoxLayout(options_frame)
        options_layout.setContentsMargins(16, 8, 16, 16)
        options_layout.setSpacing(18)
        
        btn_config = AnimatedButton("settings.svg", "Configurações")
        btn_config.setObjectName("FooterButtonSettings")
        
        btn_ajuda = AnimatedButton("help-circle.svg", "Ajuda")
        btn_ajuda.setObjectName("FooterButtonHelp")
        
        btn_atualizar = AnimatedButton("refresh.svg", "Atualizar")
        btn_atualizar.setObjectName("FooterButtonRefresh")
        
        options_layout.addWidget(btn_config)
        options_layout.addWidget(btn_ajuda)
        options_layout.addWidget(btn_atualizar)
        menu_layout.addWidget(options_frame)
        
        content_layout.addWidget(menu_frame)
        
        # Área de conteúdo
        content_frame = QFrame()
        content_frame.setObjectName("ContentArea")
        content_layout_inner = QVBoxLayout(content_frame)
        content_layout_inner.setContentsMargins(30, 30, 30, 30)
        content_layout_inner.setSpacing(20)
        
        self.stacked_widget = QStackedWidget()
        
        # Inicializa as views
        self.home_view = HomeView(self.db)
        self.cliente_view = ClienteView(self.db)
        self.lista_clientes_view = ListaClientesView(self.db)
        self.venda_view = VendaView(self.db)
        self.relatorio_view = RelatorioView(self.db)
        self.historico_view = HistoricoVendasView(self.db)
        self.config_view = ConfigView(self.db, self)
        self.notificacoes_view = NotificacoesView(self.db)
        self.whatsapp_bot_view = WhatsAppBotView()
        
        # Adiciona as views ao stacked widget (home_view como primeira)
        self.stacked_widget.addWidget(self.home_view)
        self.stacked_widget.addWidget(self.cliente_view)
        self.stacked_widget.addWidget(self.lista_clientes_view)
        self.stacked_widget.addWidget(self.venda_view)
        self.stacked_widget.addWidget(self.relatorio_view)
        self.stacked_widget.addWidget(self.historico_view)
        self.stacked_widget.addWidget(self.config_view)
        self.stacked_widget.addWidget(self.notificacoes_view)
        self.stacked_widget.addWidget(self.whatsapp_bot_view)
        
        # Define a tela inicial como a primeira a ser exibida
        self.stacked_widget.setCurrentWidget(self.home_view)
        
        content_layout_inner.addWidget(self.stacked_widget)
        content_layout.addWidget(content_frame)
        
        # Adiciona o container de conteúdo ao layout principal
        main_layout.addWidget(main_content, 1)  # 1 = esticar para preencher espaço
        
        # Conecta os botões
        btn_novo_cliente.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.cliente_view))
        btn_lista_clientes.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.lista_clientes_view))
        btn_registrar_venda.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.venda_view))
        btn_relatorios.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.relatorio_view))
        btn_historico.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.historico_view))
        btn_config.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.config_view))
        btn_notificacoes.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.notificacoes_view))
        btn_whatsapp_bot.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.whatsapp_bot_view))
        
        # Botão atualizar conectado à busca manual de atualização
        btn_atualizar.clicked.connect(self.check_for_updates)
        
        # Configurar o sinal da home_view para atualizar outras views
        self.home_view.atualizar_sistema.connect(self.atualizar_todas_views)
        
        # Conectar o manipulador de eventos de teclado
        self.installEventFilter(self)
        
        # Conectar o sinal venda_registrada para atualizar os relatórios
        self.venda_view.venda_registrada.connect(self.relatorio_view.carregar_relatorio_vendas)
        # Conectar o sinal venda_registrada para atualizar todas as telas de detalhes
        self.venda_view.venda_registrada.connect(self.relatorio_view.atualizar_telas_detalhes)
        # Conectar o sinal venda_registrada para atualizar o histórico de vendas
        self.venda_view.venda_registrada.connect(self.historico_view.carregar_produtos_registrados)
        
        # Conectar o sinal venda_alterada do histórico para atualizar os relatórios
        self.historico_view.venda_alterada.connect(self.relatorio_view.carregar_relatorio_vendas)
        # Conectar o sinal venda_alterada para atualizar todas as telas de detalhes
        self.historico_view.venda_alterada.connect(self.relatorio_view.atualizar_telas_detalhes)
        # Conectar o sinal venda_alterada para atualizar o histórico de vendas
        self.historico_view.venda_alterada.connect(self.historico_view.carregar_produtos_registrados)
        self.historico_view.venda_alterada.connect(self.historico_view.carregar_vendas_excluidas)
        
        # Configurar o sinal da lista_clientes_view para atualizar relatórios quando um cliente for editado
        self.lista_clientes_view.cliente_alterado.connect(self.relatorio_view.carregar_relatorio_vendas)
        # Conectar o sinal cliente_alterado para atualizar todas as telas de detalhes
        self.lista_clientes_view.cliente_alterado.connect(self.relatorio_view.atualizar_telas_detalhes)
        
        # Conectar o sinal notificacao_enviada da notificacoes_view para atualizar as views relevantes
        self.notificacoes_view.notificacao_enviada.connect(self.home_view.atualizar_sistema)
        
        # Após configurar todos os widgets, agora sim aplicamos o estilo
        self.setStyleSheet(STYLE)
        
        # Force a atualização dos estilos
        QApplication.processEvents()
        btn_novo_cliente.style().polish(btn_novo_cliente)
        btn_lista_clientes.style().polish(btn_lista_clientes)
        btn_registrar_venda.style().polish(btn_registrar_venda) 
        btn_relatorios.style().polish(btn_relatorios)
        btn_historico.style().polish(btn_historico)

    # Adicionar um manipulador de eventos de teclado para lidar com a tecla ESC
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            # Ao pressionar ESC, mostrar a tela inicial
            self.mostrar_tela_inicial()
            return True
        return super().eventFilter(obj, event)
    
    def mostrar_tela_inicial(self):
        """Mostra a tela inicial e atualiza os dados"""
        self.stacked_widget.setCurrentWidget(self.home_view)
        # A atualização será feita pelo evento showEvent na HomeView
    
    def atualizar_todas_views(self):
        """Atualiza todas as views do sistema"""
        # Atualizar as views com os dados mais recentes
        self.lista_clientes_view.carregar_clientes()
        self.venda_view.carregar_clientes()
        self.relatorio_view.carregar_relatorio_devedores()
        self.relatorio_view.carregar_relatorio_vendas()
        self.historico_view.carregar_produtos_registrados()
        self.historico_view.carregar_vendas_excluidas()
        self.notificacoes_view.carregar_clientes_pendentes()
        self.notificacoes_view.carregar_historico_notificacoes()
        
        # Conectar ou reconectar os sinais para garantir que as atualizações ocorram
        # Procurar por instâncias de DetalheClienteView em todos os widgets do stacked_widget
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if isinstance(widget, DetalheClienteView):
                # Reconectar o sinal venda_alterada do DetalheClienteView
                try:
                    widget.venda_alterada.disconnect()
                except:
                    pass
                widget.venda_alterada.connect(self.relatorio_view.carregar_relatorio_vendas)
                widget.venda_alterada.connect(self.relatorio_view.atualizar_telas_detalhes)
                widget.venda_alterada.connect(self.historico_view.carregar_produtos_registrados)
                widget.venda_alterada.connect(self.historico_view.carregar_vendas_excluidas)

    def check_for_updates(self):
        """Verifica se há atualizações disponíveis"""
        self.update_checker.check_for_updates()

    def show_update_dialog(self, version, date, changelog):
        """Mostra diálogo de atualização disponível"""
        dialog = UpdateDialog(version, date, changelog, self)
        if dialog.exec() == QMessageBox.Yes:
            self.start_update_download()

    def show_update_error(self, message):
        """Mostra erro de atualização"""
        QMessageBox.critical(self, "Erro de Atualização", message)

    def start_update_download(self):
        """Inicia o download da atualização"""
        self.progress_dialog = UpdateProgressDialog(self)
        self.progress_dialog.canceled.connect(self.cancel_update)
        self.progress_dialog.show()

    def update_progress(self, value):
        """Atualiza a barra de progresso"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setValue(value)

    def install_update(self, update_file):
        """Instala a atualização"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        if self.update_checker.install_update(update_file):
            QMessageBox.information(self, "Atualização", 
                "A atualização será instalada agora. O programa será reiniciado.")
            self.close()
        else:
            QMessageBox.critical(self, "Erro de Atualização",
                "Não foi possível instalar a atualização.")

    def cancel_update(self):
        """Cancela o download da atualização"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.information(self, "Atualização Cancelada",
            "A atualização foi cancelada. Você pode tentar novamente mais tarde.")

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_att_checked', False):
            self._att_checked = True
            QTimer.singleShot(10000, self.check_for_updates)

def main():
    try:
        # Verificar se já existe uma instância em execução
        socket_name = "SistemaFiadoInstance"
        local_socket = QLocalSocket()
        local_socket.connectToServer(socket_name)
        
        if local_socket.waitForConnected(500):
            # Se conseguir conectar, significa que já existe uma instância
            QMessageBox.warning(None, "Aviso", 
                              "Já existe uma instância do Sistema de Fiado em execução!\n\n"
                              "Por favor, feche a janela existente antes de abrir uma nova.")
            local_socket.disconnectFromServer()
            return
        
        # Se não conseguiu conectar, criar um servidor local para esta instância
        local_server = QLocalServer()
        local_server.removeServer(socket_name)  # Remove qualquer servidor antigo
        local_server.listen(socket_name)
        
        # Seu código principal aqui
        app = QApplication(sys.argv)
        
        # Definir o ícone usando caminho absoluto
        icon_path_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'ICONE-LOGO.ico')
        app.setWindowIcon(QIcon(icon_path_abs))
        
        # Inicializar e verificar o banco de dados
        db = Database()
        
        # Verificar a estrutura da tabela vendas
        try:
            estrutura = db.verificar_estrutura_tabela('vendas')
            colunas = [col[1] for col in estrutura]  # Nome das colunas
            
            # Verifica se a coluna 'valor_unitario' existe
            if 'valor_unitario' not in colunas:
                print("AVISO: Coluna 'valor_unitario' não encontrada na tabela vendas.")
                print("Colunas encontradas:", colunas)
        except Exception as e:
            print(f"Erro ao verificar estrutura do banco: {str(e)}")
        
        window = SistemaFiado()
        # Configurar para tela cheia
        window.showMaximized()
        
        # Conectar o sinal aboutToQuit para limpar o servidor local
        app.aboutToQuit.connect(lambda: local_server.removeServer(socket_name))
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"Erro ao iniciar aplicação: {str(e)}")

if __name__ == "__main__":
    main() 