import os
import sys
import subprocess
import time
import json
import requests

def log(message):
    print(f"[DIAGNÓSTICO] {message}")

def verificar_nodejs():
    log("Verificando instalação do Node.js...")
    try:
        result = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            log(f"Node.js encontrado: {result.stdout.strip()}")
            return True
        else:
            log(f"Erro ao executar Node.js: {result.stderr}")
            return False
    except Exception as e:
        log(f"Erro ao verificar Node.js: {str(e)}")
        return False

def verificar_diretorio_bot():
    log("Verificando diretório do bot...")
    bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_bot")
    if os.path.exists(bot_dir):
        log(f"Diretório do bot encontrado: {bot_dir}")
        # Listar arquivos no diretório
        files = os.listdir(bot_dir)
        log(f"Arquivos encontrados: {', '.join(files)}")
        return True
    else:
        log(f"Diretório do bot não encontrado: {bot_dir}")
        return False

def verificar_servidor():
    log("Verificando se o servidor está rodando...")
    try:
        response = requests.get("http://localhost:3000/api/status", timeout=2)
        log(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            log(f"Resposta do servidor: {json.dumps(data, indent=2)}")
            return True
        else:
            log(f"Resposta inesperada do servidor: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        log(f"Erro ao conectar ao servidor: {str(e)}")
        return False

def iniciar_servidor():
    log("Tentando iniciar o servidor bot manualmente...")
    bot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_bot")
    server_js = os.path.join(bot_dir, "server.js")
    
    if not os.path.exists(server_js):
        log(f"Arquivo server.js não encontrado: {server_js}")
        return False
    
    try:
        # Iniciar o servidor em segundo plano
        if sys.platform == 'win32':
            process = subprocess.Popen(
                ["node", server_js],
                cwd=bot_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen(
                ["node", server_js],
                cwd=bot_dir
            )
        
        log(f"Servidor iniciado com PID: {process.pid}")
        log("Aguardando o servidor iniciar (10 segundos)...")
        time.sleep(10)
        return True
    except Exception as e:
        log(f"Erro ao iniciar o servidor: {str(e)}")
        return False

def main():
    log("Iniciando diagnóstico do WhatsApp Bot...")
    
    # 1. Verificar Node.js
    if not verificar_nodejs():
        log("PROBLEMA: Node.js não está instalado ou não está disponível no PATH")
        log("SOLUÇÃO: Instale o Node.js ou configure o PATH corretamente")
        return

    # 2. Verificar diretório do bot
    if not verificar_diretorio_bot():
        log("PROBLEMA: Diretório do bot não foi encontrado")
        log("SOLUÇÃO: Verifique se a pasta whatsapp_bot existe no diretório do projeto")
        return
    
    # 3. Verificar se o servidor já está rodando
    if verificar_servidor():
        log("Servidor já está rodando, mas pode estar com problemas")
    else:
        log("Servidor não está rodando. Tentando iniciar...")
        iniciar_servidor()
        # Verificar novamente se o servidor está rodando
        if verificar_servidor():
            log("Servidor iniciado com sucesso!")
        else:
            log("PROBLEMA: Não foi possível iniciar o servidor")
            log("SOLUÇÃO: Verifique as dependências do Node.js e reinstale-as com 'npm install'")
    
    log("Diagnóstico concluído!")

if __name__ == "__main__":
    main() 