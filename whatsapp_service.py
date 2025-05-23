import webbrowser
import re
import urllib.parse
from datetime import datetime
import time
import os

class WhatsAppService:
    """
    Serviço para enviar mensagens pelo WhatsApp Web.
    Esta versão usa o método de URL direta do WhatsApp sem depender de bibliotecas externas.
    """
    def __init__(self):
        # Usar a URL oficial do WhatsApp
        self.base_url = "https://wa.me"
    
    def formatar_numero_telefone(self, telefone):
        """
        Formata o número de telefone para o formato que o WhatsApp usa
        Remove todos os caracteres não-numéricos e adiciona o código do país (+55) se não estiver presente
        
        Args:
            telefone: Número de telefone do cliente (pode conter formatação)
            
        Returns:
            Número formatado para uso com WhatsApp
        """
        # Remover todos os caracteres não-numéricos
        numero_limpo = re.sub(r'\D', '', telefone)
        
        # Garantir que o número inclui o código do país (55 para Brasil)
        if not numero_limpo.startswith('55'):
            numero_limpo = '55' + numero_limpo
            print(f"Adicionado prefixo 55: {numero_limpo}")
        else:
            print(f"Número já contém prefixo 55: {numero_limpo}")
        
        return numero_limpo
    
    def enviar_mensagem_instantanea(self, telefone, mensagem):
        """
        Abre o WhatsApp Web com uma mensagem pré-preenchida
        
        Args:
            telefone: Número de telefone do destinatário
            mensagem: Texto da mensagem a ser enviada
            
        Returns:
            bool: True se a operação foi iniciada com sucesso, False caso contrário
        """
        try:
            # Formatar o número do telefone
            numero_formatado = self.formatar_numero_telefone(telefone)
            
            # Codificar a mensagem para uso em URL
            mensagem_codificada = urllib.parse.quote(mensagem)
            
            # Existem dois formatos de URL para o WhatsApp:
            # 1. Mobile/App: https://wa.me/NUMERO?text=MENSAGEM
            # 2. Web: https://web.whatsapp.com/send/?phone=NUMERO&text=MENSAGEM
            
            # Construir a URL para dispositivos móveis
            mobile_url = f"{self.base_url}/{numero_formatado}?text={mensagem_codificada}"
            
            # Construir a URL para o WhatsApp Web (geralmente funciona melhor para abrir no navegador desktop)
            web_url = f"https://web.whatsapp.com/send/?phone={numero_formatado}&text={mensagem_codificada}&type=phone_number&app_absent=0"
            
            print(f"Abrindo WhatsApp para o número: {numero_formatado}")
            print(f"URL Mobile: {mobile_url}")
            print(f"URL Web: {web_url}")
            
            # Tentar acessar a URL do WhatsApp Web - geralmente mais confiável para computadores
            print("Abrindo WhatsApp Web. Por favor, espere o navegador carregar...")
            webbrowser.open(web_url)
            
            print("WhatsApp Web aberto com sucesso. Por favor, confirme o envio da mensagem no navegador.")
            return True
            
        except Exception as e:
            print(f"Erro ao abrir WhatsApp Web: {str(e)}")
            return False
    
    def enviar_mensagem(self, telefone, mensagem):
        """
        Alias para enviar_mensagem_instantanea
        Mantido para compatibilidade com a versão anterior
        """
        return self.enviar_mensagem_instantanea(telefone, mensagem)

# Função para testar o serviço diretamente
def main():
    service = WhatsAppService()
    numero = input("Digite o número de telefone (com DDD): ")
    mensagem = input("Digite a mensagem: ")
    
    print("Abrindo WhatsApp Web...")
    service.enviar_mensagem_instantanea(numero, mensagem)

if __name__ == "__main__":
    main() 