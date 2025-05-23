# Estilos para o sistema
STYLE = """
/* Estilos Gerais */
QMainWindow {
    background-color: #1a202c;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

/* Menu Lateral */
QFrame#MenuLateral {
    background-color: #2c3e50;
    min-width: 280px;
    max-width: 280px;
}

/* Logo Area */
QFrame#LogoArea {
    background-color: #243342;
    border-bottom: 1px solid #34495e;
}

/* Botões do Menu */
QFrame#MenuButtonsContainer QPushButton {
    text-align: left;
    padding: 12px 20px;
    margin: 6px 12px;
    border-radius: 10px;
    font-size: 12pt;
    font-weight: 600;
    min-height: 48px;
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.08);
    qproperty-iconSize: 24px;
}

QFrame#MenuButtonsContainer QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.2);
    color: #fff;
    padding-left: 24px;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

QFrame#MenuButtonsContainer QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.1);
    color: #fff;
    padding-left: 20px;
}

/* Botões Coloridos com cores vivas */
QFrame#MenuButtonsContainer QPushButton[colorClass="Verde"] {
    background-color: #2ecc71;
    border: 1px solid #27ae60;
    color: #fff;
}
QFrame#MenuButtonsContainer QPushButton[colorClass="Verde"]:hover {
    background-color: #27ae60;
    border: 1px solid #219d54;
    color: #fff;
    padding-left: 24px;
}

QFrame#MenuButtonsContainer QPushButton[colorClass="Vermelho"] {
    background-color: #e74c3c;
    border: 1px solid #c0392b;
    color: #fff;
}
QFrame#MenuButtonsContainer QPushButton[colorClass="Vermelho"]:hover {
    background-color: #c0392b;
    border: 1px solid #a93226;
    color: #fff;
    padding-left: 24px;
}

QFrame#MenuButtonsContainer QPushButton[colorClass="Amarelo"] {
    background-color: #f1c40f;
    border: 1px solid #e6b90d;
    color: #fff;
}
QFrame#MenuButtonsContainer QPushButton[colorClass="Amarelo"]:hover {
    background-color: #f39c12;
    border: 1px solid #e67e22;
    color: #fff;
    padding-left: 24px;
}

QFrame#MenuButtonsContainer QPushButton[colorClass="Azul"] {
    background-color: #3498db;
    border: 1px solid #2980b9;
    color: #fff;
}
QFrame#MenuButtonsContainer QPushButton[colorClass="Azul"]:hover {
    background-color: #2980b9;
    border: 1px solid #2471a3;
    color: #fff;
    padding-left: 24px;
}

QFrame#MenuButtonsContainer QPushButton[colorClass="Roxo"] {
    background-color: #9b59b6;
    border: 1px solid #8e44ad;
    color: #fff;
}
QFrame#MenuButtonsContainer QPushButton[colorClass="Roxo"]:hover {
    background-color: #8e44ad;
    border: 1px solid #7d3c98;
    color: #fff;
    padding-left: 24px;
}

/* Botões do Rodapé */
QPushButton#FooterButtonSettings,
QPushButton#FooterButtonHelp,
QPushButton#FooterButtonRefresh {
    border: none;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    padding: 10px;
    margin: 0 5px;
}

/* Efeitos hover gerais para todos os botões do rodapé */
QPushButton#FooterButtonSettings:hover,
QPushButton#FooterButtonHelp:hover,
QPushButton#FooterButtonRefresh:hover {
    background: rgba(255, 255, 255, 0.2);
    padding: 12px;
    margin-top: -2px;
    margin-bottom: 2px;
}

/* Efeitos pressed gerais para todos os botões do rodapé */
QPushButton#FooterButtonSettings:pressed,
QPushButton#FooterButtonHelp:pressed,
QPushButton#FooterButtonRefresh:pressed {
    background: rgba(255, 255, 255, 0.15);
    padding: 10px;
    margin-top: 0px;
    margin-bottom: 0px;
}

/* Efeito específico para o botão de configurações */
QPushButton#FooterButtonSettings:hover {
    background: rgba(52, 152, 219, 0.3);
}

/* Efeito específico para o botão de ajuda */
QPushButton#FooterButtonHelp:hover {
    background: rgba(46, 204, 113, 0.3);
}

/* Efeito específico para o botão de atualização */
QPushButton#FooterButtonRefresh:hover {
    background: rgba(155, 89, 182, 0.3);
}

/* Efeito específico para o botão de backup */
QPushButton#FooterButtonBackup:hover {
    background: rgba(241, 196, 15, 0.3);
}

/* Área de Conteúdo */
QFrame#ContentArea {
    background-color: #1a202c;
    padding: 20px;
}

/* Títulos */
QLabel#Title {
    color: #ecf0f1;
    font-size: 24pt;
    font-weight: bold;
}

/* Campos de Entrada */
QLineEdit, QTextEdit, QComboBox {
    border: 2px solid #34495e;
    border-radius: 8px;
    padding: 10px;
    background-color: #243342;
    color: #ecf0f1;
    font-size: 11pt;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #3498db;
    background-color: #2c3e50;
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #95a5a6;
}

/* Tabelas */
QTableWidget {
    border: none;
    background-color: #2c3e50;
    border-radius: 8px;
    gridline-color: #34495e;
    color: #ecf0f1;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #34495e;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: #ecf0f1;
}

QHeaderView::section {
    background-color: #243342;
    padding: 12px;
    border: none;
    font-weight: bold;
    color: #ecf0f1;
}

/* Botões de Ação */
QPushButton#ActionButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 11pt;
    font-weight: 500;
    min-height: 40px;
}

QPushButton#ActionButton:hover {
    background-color: #2980b9;
}

QPushButton#ActionButton:pressed {
    background-color: #2472a4;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #1a202c;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #425069;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #536480;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #1a202c;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #425069;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #536480;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Mensagens e Diálogos */
QMessageBox {
    background-color: #2c3e50;
    color: #ecf0f1;
}

QMessageBox QPushButton {
    min-width: 80px;
    background-color: #3498db;
    color: white;
    border-radius: 4px;
    padding: 8px 16px;
}

QDialog {
    background-color: #2c3e50;
    color: #ecf0f1;
}

/* Tooltips */
QToolTip {
    background-color: #2c3e50;
    color: white;
    border: none;
    padding: 6px;
    border-radius: 4px;
}

/* Estilo para os botões do menu */
QPushButton[colorClass="Laranja"] {
    background-color: #ff7f50;
    border-left: 5px solid #e74c3c;
    text-align: left;
    padding-left: 15px;
}

QPushButton[colorClass="Laranja"]:hover {
    background-color: #e74c3c;
    border-left: 5px solid #c0392b;
}
""" 