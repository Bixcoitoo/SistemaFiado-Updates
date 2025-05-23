from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMainWindow, QApplication)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
import os

def icon_path(name):
    return os.path.join(os.path.dirname(__file__), 'icons', name)

class AvisoDialog(QDialog):
    """
    Diálogo personalizado para substituir QMessageBox com visual consistente com o sistema
    """
    TIPO_INFO = "info"
    TIPO_SUCESSO = "sucesso"
    TIPO_AVISO = "aviso"
    TIPO_ERRO = "erro"
    
    def __init__(self, titulo, mensagem, tipo=TIPO_INFO, parent=None):
        """
        Inicializa o diálogo de aviso personalizado
        
        Args:
            titulo: Título do aviso
            mensagem: Texto da mensagem
            tipo: Tipo de aviso (info, sucesso, aviso, erro)
            parent: Widget pai (preferencialmente a janela principal)
        """
        # Buscar a janela principal, se não for fornecida
        if parent is None:
            app = QApplication.instance()
            parent = next((w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)), None)
            
        super().__init__(parent)
        self.titulo = titulo
        self.mensagem = mensagem
        self.tipo = tipo
        
        # Remover barra de título e tornar modal
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        
        self.init_ui()
        
        # Centralizar o diálogo em relação ao parent
        if parent:
            center_point = parent.mapToGlobal(parent.rect().center())
            self.move(center_point.x() - self.width() // 2, center_point.y() - self.height() // 2)
    
    def init_ui(self):
        self.setFixedSize(450, 300)
        
        # Configurar cores e ícones com base no tipo
        cores = {
            self.TIPO_INFO: {"bg": "#3498db", "border": "#2980b9", "icone": "info-circle.svg"},
            self.TIPO_SUCESSO: {"bg": "#2ecc71", "border": "#27ae60", "icone": "check-circle.svg"},
            self.TIPO_AVISO: {"bg": "#f39c12", "border": "#e67e22", "icone": "alert-triangle.svg"},
            self.TIPO_ERRO: {"bg": "#e74c3c", "border": "#c0392b", "icone": "x-circle.svg"}
        }
        
        cor = cores.get(self.tipo, cores[self.TIPO_INFO])
        
        # Aplicar estilo
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 10px;
            }}
            QLabel#TituloLabel {{
                color: #ecf0f1;
                font-size: 14pt;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#MensagemLabel {{
                color: #ecf0f1;
                font-size: 11pt;
                background: transparent;
            }}
            QPushButton {{
                min-height: 40px;
                border-radius: 8px;
                font-weight: bold;
                padding: 10px 20px;
                font-size: 12pt;
                background-color: {cor['bg']};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {cor['border']};
            }}
            QFrame#IconeFrame {{
                background-color: {cor['bg']};
                border-radius: 35px;
                border: 2px solid {cor['border']};
            }}
        """)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Ícone
        icone_frame = QFrame()
        icone_frame.setObjectName("IconeFrame")
        icone_frame.setFixedSize(70, 70)
        
        icone_layout = QHBoxLayout(icone_frame)
        icone_layout.setContentsMargins(0, 0, 0, 0)
        icone_layout.setAlignment(Qt.AlignCenter)
        
        # Versão branca do ícone para usar em fundos coloridos
        icone_branco = cor['icone'].replace('.svg', '-white.svg')
        
        # Tentar usar o ícone branco, se não existir, usar o normal
        icone_path_branco = icon_path(icone_branco)
        icone_path_normal = icon_path(cor['icone'])
        
        icone_real = icone_path_branco if os.path.exists(icone_path_branco) else icone_path_normal
        
        icone_label = QLabel()
        icone_label.setPixmap(QIcon(icone_real).pixmap(40, 40))
        icone_label.setStyleSheet("background: transparent;")
        icone_layout.addWidget(icone_label)
        
        # Adicionar o ícone ao layout centralizado
        icone_container = QHBoxLayout()
        icone_container.setAlignment(Qt.AlignCenter)
        icone_container.addWidget(icone_frame)
        layout.addLayout(icone_container)
        
        # Título
        titulo_label = QLabel(self.titulo)
        titulo_label.setObjectName("TituloLabel")
        titulo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo_label)
        
        # Mensagem
        mensagem_label = QLabel(self.mensagem)
        mensagem_label.setObjectName("MensagemLabel")
        mensagem_label.setAlignment(Qt.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet("background: transparent;")
        layout.addWidget(mensagem_label)
        
        # Linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #34495e; min-height: 1px;")
        layout.addWidget(separator)
        
        # Botão
        botao_layout = QHBoxLayout()
        botao_layout.setAlignment(Qt.AlignCenter)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setMinimumWidth(120)
        self.btn_ok.clicked.connect(self.accept)
        
        botao_layout.addWidget(self.btn_ok)
        layout.addLayout(botao_layout)

# Funções utilitárias para mostrar diálogos facilmente

def mostrar_info(titulo, mensagem, parent=None):
    """Mostra um diálogo de informação personalizado"""
    dialog = AvisoDialog(titulo, mensagem, AvisoDialog.TIPO_INFO, parent)
    return dialog.exec_()

def mostrar_sucesso(titulo, mensagem, parent=None):
    """Mostra um diálogo de sucesso personalizado"""
    dialog = AvisoDialog(titulo, mensagem, AvisoDialog.TIPO_SUCESSO, parent)
    return dialog.exec_()

def mostrar_aviso(titulo, mensagem, parent=None):
    """Mostra um diálogo de aviso personalizado"""
    dialog = AvisoDialog(titulo, mensagem, AvisoDialog.TIPO_AVISO, parent)
    return dialog.exec_()

def mostrar_erro(titulo, mensagem, parent=None):
    """Mostra um diálogo de erro personalizado"""
    dialog = AvisoDialog(titulo, mensagem, AvisoDialog.TIPO_ERRO, parent)
    return dialog.exec_()

# Função para criar um diálogo de confirmação personalizado
class ConfirmacaoDialog(QDialog):
    """
    Diálogo personalizado para substituir QMessageBox.question com visual consistente
    """
    def __init__(self, titulo, mensagem, text_cancelar="Cancelar", text_confirmar="Confirmar", parent=None):
        """
        Inicializa o diálogo de confirmação personalizado
        
        Args:
            titulo: Título do diálogo
            mensagem: Texto da mensagem
            text_cancelar: Texto do botão cancelar
            text_confirmar: Texto do botão confirmar
            parent: Widget pai (preferencialmente a janela principal)
        """
        # Buscar a janela principal, se não for fornecida
        if parent is None:
            app = QApplication.instance()
            parent = next((w for w in app.topLevelWidgets() if isinstance(w, QMainWindow)), None)
            
        super().__init__(parent)
        self.titulo = titulo
        self.mensagem = mensagem
        self.text_cancelar = text_cancelar
        self.text_confirmar = text_confirmar
        
        # Remover barra de título e tornar modal
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        
        self.init_ui()
        
        # Centralizar o diálogo em relação ao parent
        if parent:
            center_point = parent.mapToGlobal(parent.rect().center())
            self.move(center_point.x() - self.width() // 2, center_point.y() - self.height() // 2)
    
    def init_ui(self):
        self.setFixedSize(450, 300)
        
        # Aplicar estilo
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 10px;
            }
            QLabel#TituloLabel {
                color: #ecf0f1;
                font-size: 14pt;
                font-weight: bold;
                background: transparent;
            }
            QLabel#MensagemLabel {
                color: #ecf0f1;
                font-size: 11pt;
            }
            QPushButton#BtnConfirmar {
                min-height: 35px;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 15px;
                font-size: 11pt;
                background-color: #3498db;
                color: white;
                border: none;
            }
            QPushButton#BtnConfirmar:hover {
                background-color: #2980b9;
            }
            QPushButton#BtnCancelar {
                min-height: 35px;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 15px;
                font-size: 11pt;
                background-color: #34495e;
                color: white;
                border: none;
            }
            QPushButton#BtnCancelar:hover {
                background-color: #435c78;
            }
            QFrame#IconeFrame {
                background-color: #f39c12;
                border-radius: 30px;
                border: 2px solid #e67e22;
            }
        """)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # Ícone
        icone_frame = QFrame()
        icone_frame.setObjectName("IconeFrame")
        icone_frame.setFixedSize(60, 60)
        
        icone_layout = QHBoxLayout(icone_frame)
        icone_layout.setContentsMargins(0, 0, 0, 0)
        icone_layout.setAlignment(Qt.AlignCenter)
        
        icone_label = QLabel()
        icone_label.setPixmap(QIcon(icon_path("alert-triangle-white.svg")).pixmap(35, 35))
        icone_label.setStyleSheet("background: transparent;")
        icone_layout.addWidget(icone_label)
        
        # Adicionar o ícone ao layout centralizado
        icone_container = QHBoxLayout()
        icone_container.setAlignment(Qt.AlignCenter)
        icone_container.addWidget(icone_frame)
        layout.addLayout(icone_container)
        
        # Título
        titulo_label = QLabel(self.titulo)
        titulo_label.setObjectName("TituloLabel")
        titulo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo_label)
        
        # Mensagem
        mensagem_label = QLabel(self.mensagem)
        mensagem_label.setObjectName("MensagemLabel")
        mensagem_label.setAlignment(Qt.AlignCenter)
        mensagem_label.setWordWrap(True)
        mensagem_label.setStyleSheet("background: transparent;")
        layout.addWidget(mensagem_label)
        
        # Linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #34495e; min-height: 1px;")
        layout.addWidget(separator)
        
        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(15)
        
        self.btn_cancelar = QPushButton(self.text_cancelar)
        self.btn_cancelar.setObjectName("BtnCancelar")
        self.btn_cancelar.setIcon(QIcon(icon_path("x-circle.svg")))
        self.btn_cancelar.setIconSize(QSize(20, 20))
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.setMinimumWidth(120)
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_confirmar = QPushButton(self.text_confirmar)
        self.btn_confirmar.setObjectName("BtnConfirmar")
        self.btn_confirmar.setIcon(QIcon(icon_path("check-circle.svg")))
        self.btn_confirmar.setIconSize(QSize(20, 20))
        self.btn_confirmar.setCursor(Qt.PointingHandCursor)
        self.btn_confirmar.setMinimumWidth(120)
        self.btn_confirmar.clicked.connect(self.accept)
        
        botoes_layout.addWidget(self.btn_cancelar)
        botoes_layout.addWidget(self.btn_confirmar)
        
        layout.addLayout(botoes_layout)

def mostrar_confirmacao(titulo, mensagem, text_cancelar="Cancelar", text_confirmar="Confirmar", parent=None):
    """Mostra um diálogo de confirmação personalizado"""
    dialog = ConfirmacaoDialog(titulo, mensagem, text_cancelar, text_confirmar, parent)
    return dialog.exec_() 