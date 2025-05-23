# Roteiro Completo: Expondo Serviços Internos com Cloudflare Tunnel

## 1. Pré-requisitos
- Conta no Cloudflare e domínio já adicionado.
- Acesso root ou sudo na máquina que irá rodar o tunnel.
- Serviços rodando nas portas internas (ex: Portainer, Cockpit, Webmin, etc).

---

## 2. Instalação do cloudflared
```bash
wget -O cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
cloudflared --version
```

---

## 3. Autenticação e criação do túnel
```bash
cloudflared tunnel login
cloudflared tunnel create NOME_TUNEL
cloudflared tunnel list
```

---

## 4. Configuração do arquivo config.yml
```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```
Exemplo:
```yaml
tunnel: SEU_ID_DO_TUNEL
credentials-file: /home/SEU_USUARIO/.cloudflared/SEU_ID_DO_TUNEL.json

ingress:
  - hostname: portainer.magalha.space
    service: http://192.168.0.145:9000
  - hostname: painel.magalha.space
    service: http://192.168.0.145
  - hostname: cockpit.magalha.space
    service: https://192.168.0.145:9090
  - hostname: webmin.magalha.space
    service: https://192.168.0.145:10000
  - service: http_status:404
```

---

## 5. Configuração do serviço systemd
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sudo systemctl status cloudflared
```

---

## 6. Configuração dos registros DNS no Cloudflare
No painel do Cloudflare, crie um registro **CNAME** para cada subdomínio:

| Tipo   | Nome         | Conteúdo                                 | Proxy |
|--------|--------------|------------------------------------------|-------|
| CNAME  | portainer    | SEU_ID_DO_TUNEL.cfargotunnel.com         | Ativo |
| CNAME  | painel       | SEU_ID_DO_TUNEL.cfargotunnel.com         | Ativo |
| CNAME  | cockpit      | SEU_ID_DO_TUNEL.cfargotunnel.com         | Ativo |
| CNAME  | webmin       | SEU_ID_DO_TUNEL.cfargotunnel.com         | Ativo |

---

## 7. Testando o acesso
Acesse:
- http://portainer.magalha.space
- http://painel.magalha.space
- https://cockpit.magalha.space
- https://webmin.magalha.space

---

## 8. Comandos úteis
- **Status do serviço:**
  ```bash
  sudo systemctl status cloudflared
  ```
- **Logs em tempo real:**
  ```bash
  sudo journalctl -u cloudflared -f
  ```
- **Reiniciar serviço:**
  ```bash
  sudo systemctl restart cloudflared
  ```
- **Verificar túneis:**
  ```bash
  cloudflared tunnel list
  ```

---

## 9. Possíveis erros e soluções
- **"hostname not found"**
  - Verifique o registro CNAME no Cloudflare.
  - Verifique se o tunnel está rodando.
- **"Bad Gateway"**
  - Serviço interno pode estar parado ou porta errada.
  - Teste localmente: `curl http://192.168.0.145:9000`
- **"Tunnel not found"**
  - ID do túnel no config.yml está errado.
  - Use `cloudflared tunnel list` para conferir.
- **"credentials-file not found"**
  - Caminho do arquivo de credenciais está errado.
  - Veja onde o arquivo .json foi criado.
- **Página não abre externamente**
  - Verifique se o proxy (nuvem laranja) está ativado no Cloudflare.
  - Verifique se o serviço cloudflared está rodando.

---

## 10. Dicas finais
- Não precisa abrir portas no roteador/firewall para os serviços internos.
- O Cloudflare Tunnel faz a ponte segura entre a internet e sua rede local.
- Para adicionar mais subdomínios, basta editar o config.yml, reiniciar o cloudflared e criar o registro DNS correspondente. 