import json
import os
import sys
import requests
import subprocess
import tempfile
import shutil
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QWidget
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QSize

class UpdateChecker(QObject):
    """Classe para verificar e baixar atualizações"""
    update_available = Signal(str, str, list)  # versão, data, changelog
    update_error = Signal(str)  # mensagem de erro
    download_progress = Signal(int)  # progresso do download
    download_complete = Signal(str)  # caminho do arquivo baixado

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.version_url = "https://api.github.com/repos/Bixcoitoo/SistemaFiado-Updates/releases/latest"
        self.temp_dir = tempfile.gettempdir()

    def check_for_updates(self):
        """Verifica se há atualizações disponíveis"""
        try:
            # Obter informações da versão mais recente
            response = requests.get(self.version_url)
            response.raise_for_status()
            update_info = response.json()

            # Ajustar para os campos da API do GitHub
            nova_versao = update_info['tag_name']
            data_lancamento = update_info['published_at'][:10]  # só a data
            changelog = update_info['body'].split('\n') if update_info['body'] else []

            # Comparar versões
            if self._compare_versions(nova_versao, self.current_version) > 0:
                self.update_available.emit(
                    nova_versao,
                    data_lancamento,
                    changelog
                )
                return True
            return False

        except Exception as e:
            self.update_error.emit(f"Erro ao verificar atualizações: {str(e)}")
            return False

    def download_update(self, url):
        """Baixa a atualização"""
        try:
            # Criar nome temporário para o arquivo
            temp_file = os.path.join(self.temp_dir, "Sistema_Fiado_Update.exe")

            # Baixar o arquivo com barra de progresso
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0

            with open(temp_file, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.download_progress.emit(progress)

            self.download_complete.emit(temp_file)
            return True

        except Exception as e:
            self.update_error.emit(f"Erro ao baixar atualização: {str(e)}")
            return False

    def install_update(self, update_file):
        """Instala a atualização"""
        try:
            # Criar script de atualização
            script_path = os.path.join(self.temp_dir, "update.bat")
            current_exe = sys.executable
            update_exe = update_file

            # Criar script batch para atualizar
            with open(script_path, 'w') as f:
                f.write('@echo off\n')
                f.write('timeout /t 2 /nobreak > nul\n')  # Esperar 2 segundos
                f.write(f'del "{current_exe}"\n')
                f.write(f'copy "{update_exe}" "{current_exe}"\n')
                f.write(f'del "{update_exe}"\n')
                f.write(f'del "{script_path}"\n')
                f.write(f'start "" "{current_exe}"\n')

            # Executar script de atualização
            subprocess.Popen(['cmd', '/c', script_path], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            return True

        except Exception as e:
            self.update_error.emit(f"Erro ao instalar atualização: {str(e)}")
            return False

    def _compare_versions(self, version1, version2):
        """Compara duas versões no formato x.y.z"""
        v1 = list(map(int, version1.split('.')))
        v2 = list(map(int, version2.split('.')))
        
        for i in range(max(len(v1), len(v2))):
            n1 = v1[i] if i < len(v1) else 0
            n2 = v2[i] if i < len(v2) else 0
            
            if n1 > n2:
                return 1
            elif n1 < n2:
                return -1
        return 0

class UpdateDialog(QDialog):
    """Diálogo moderno para mostrar informações de atualização"""
    def __init__(self, version, date, changelog, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setObjectName("UpdateDialog")
        self.setFixedSize(700, 500)
        self.setStyleSheet("""
            #UpdateDialog {
                background-color: #23272f;
                border-radius: 16px;
                border: 1.5px solid #3498db;
            }
            QLabel#TituloLabel {
                color: #ecf0f1;
                font-size: 15pt;
                font-weight: bold;
            }
            QLabel#MensagemLabel {
                color: #bdc3c7;
                font-size: 10pt;
            }
            QPushButton#BtnAtualizar {
                min-height: 38px;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 15px;
                font-size: 11pt;
                background-color: #3498db;
                color: white;
                border: none;
            }
            QPushButton#BtnAtualizar:hover {
                background-color: #2980b9;
            }
            QPushButton#BtnFechar {
                min-height: 38px;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 15px;
                font-size: 11pt;
                background-color: #34495e;
                color: white;
                border: none;
            }
            QPushButton#BtnFechar:hover {
                background-color: #435c78;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(32, 28, 32, 28)

        # Título
        titulo = QLabel("Atualização Disponível")
        titulo.setObjectName("TituloLabel")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Mensagem
        mensagem = QLabel(f"<b>Uma nova versão ({version}) está disponível!</b><br>Data de lançamento: {date}")
        mensagem.setObjectName("MensagemLabel")
        mensagem.setAlignment(Qt.AlignCenter)
        mensagem.setWordWrap(True)
        layout.addWidget(mensagem)

        # Changelog
        changelog_label = QLabel("Novidades nesta versão:")
        changelog_label.setStyleSheet("color: #ecf0f1; font-weight: bold; font-size: 11pt;")
        changelog_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(changelog_label)

        # Scroll para changelog
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        changelog_widget = QWidget()
        changelog_layout = QVBoxLayout(changelog_widget)
        changelog_layout.setContentsMargins(0, 0, 0, 0)
        changelog_layout.setSpacing(6)
        for item in changelog:
            item_label = QLabel(f"• {item}")
            item_label.setStyleSheet("color: #bdc3c7; font-size: 10pt;")
            item_label.setWordWrap(True)
            changelog_layout.addWidget(item_label)
        changelog_layout.addStretch()
        scroll.setWidget(changelog_widget)
        layout.addWidget(scroll, stretch=1)

        # Linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #34495e; min-height: 1px;")
        layout.addWidget(separator)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(18)
        btn_layout.addStretch()
        self.btn_fechar = QPushButton("Mais Tarde")
        self.btn_fechar.setObjectName("BtnFechar")
        self.btn_fechar.setCursor(Qt.PointingHandCursor)
        self.btn_fechar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_fechar)
        self.btn_atualizar = QPushButton("Atualizar Agora")
        self.btn_atualizar.setObjectName("BtnAtualizar")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_atualizar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Centralizar na tela principal
        if parent:
            center_point = parent.mapToGlobal(parent.rect().center())
            self.move(center_point.x() - self.width() // 2, center_point.y() - self.height() // 2)

    def mousePressEvent(self, event):
        # Não permite arrastar a janela
        event.ignore()

    def mouseMoveEvent(self, event):
        # Não permite arrastar a janela
        event.ignore()

    def mouseReleaseEvent(self, event):
        # Não permite arrastar a janela
        event.ignore()

class UpdateProgressDialog(QProgressDialog):
    """Diálogo para mostrar progresso do download"""
    def __init__(self, parent=None):
        super().__init__("Baixando atualização...", "Cancelar", 0, 100, parent)
        self.setWindowTitle("Atualização")
        self.setWindowModality(True)
        self.setMinimumDuration(0)
        self.setAutoClose(True)
        self.setAutoReset(True) 