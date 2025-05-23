import sqlite3
from datetime import datetime
import os
import shutil
from PySide6.QtCore import QTimer
import sys

class Database:
    def __init__(self):
        # Obter o diretório do executável ou do script
        if getattr(sys, 'frozen', False):
            # Se estiver rodando como executável
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Se estiver rodando como script
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Criar pasta database se não existir
        self.database_dir = os.path.join(self.base_dir, 'database')
        if not os.path.exists(self.database_dir):
            os.makedirs(self.database_dir)
            print(f"Pasta database criada em: {self.database_dir}")
            
        # Criar pasta backups se não existir
        self.backups_dir = os.path.join(self.database_dir, 'backups')
        if not os.path.exists(self.backups_dir):
            os.makedirs(self.backups_dir)
            print(f"Pasta backups criada em: {self.backups_dir}")
            
        self.database_path = os.path.join(self.database_dir, 'sistema_fiado.db')
        self.conn = sqlite3.connect(self.database_path)
        # Cache para estrutura das tabelas
        self.cache_estrutura = {}
        # Flag para controlar mensagens
        self.mostrou_info_valor_unitario = False
        self.criar_tabelas()
        # Verificar e atualizar estrutura se necessário
        self.verificar_e_atualizar_estrutura()
        # Verificar tabela de vendas excluídas
        self.verificar_tabela_vendas_excluidas()
        # Verificar tabela de notificações
        self.verificar_tabela_notificacoes()
        
        # Configurar backup automático
        self.configurar_backup_automatico()
    
    def configurar_backup_automatico(self):
        """Configura o backup automático para ser executado periodicamente"""
        # Criar timer para backup automático (a cada 6 horas)
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.executar_backup_automatico)
        # 6 horas em milissegundos (6 * 60 * 60 * 1000)
        self.backup_timer.start(21600000)
        
    def executar_backup_automatico(self):
        """Executa o backup automático e limpa backups antigos"""
        try:
            # Fazer o backup
            sucesso, mensagem = self.fazer_backup_automatico()
            
            if sucesso:
                print(f"Backup automático realizado com sucesso: {mensagem}")
                # Limpar backups antigos (manter apenas os últimos 7 dias)
                self.limpar_backups_antigos()
            else:
                print(f"Erro no backup automático: {mensagem}")
                
        except Exception as e:
            print(f"Erro ao executar backup automático: {str(e)}")
    
    def limpar_backups_antigos(self):
        """Remove backups mais antigos que 7 dias"""
        try:
            backup_dir = self.backups_dir
            if not os.path.exists(backup_dir):
                return
                
            # Data limite (7 dias atrás)
            data_limite = datetime.now().timestamp() - (7 * 24 * 60 * 60)
            
            # Listar todos os arquivos de backup
            for arquivo in os.listdir(backup_dir):
                if arquivo.startswith('backup_') and arquivo.endswith('.db'):
                    caminho_arquivo = os.path.join(backup_dir, arquivo)
                    # Verificar data de criação
                    if os.path.getctime(caminho_arquivo) < data_limite:
                        os.remove(caminho_arquivo)
                        print(f"Backup antigo removido: {arquivo}")
                        
        except Exception as e:
            print(f"Erro ao limpar backups antigos: {str(e)}")
    
    def criar_tabelas(self):
        cursor = self.conn.cursor()
        
        # Tabela de Clientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            nota TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de Vendas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        ''')
        
        # Tabela de Vendas Excluídas (para histórico)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas_excluidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            cliente_id INTEGER,
            cliente_nome TEXT,
            produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_total REAL NOT NULL,
            data_venda TEXT,
            data_exclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
        ''')
        
        self.conn.commit()
    
    def verificar_estrutura_tabela(self, nome_tabela):
        """
        Verifica a estrutura de uma tabela e retorna suas colunas
        """
        # Se já temos esta estrutura em cache, usar o cache
        if nome_tabela in self.cache_estrutura:
            return self.cache_estrutura[nome_tabela]
            
        # Caso contrário, consultar o banco
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        resultado = cursor.fetchall()
        
        # Salvar no cache
        self.cache_estrutura[nome_tabela] = resultado
        
        # Exibir informações sobre a estrutura apenas na inicialização
        if nome_tabela == 'vendas' and not self.mostrou_info_valor_unitario:
            colunas = [col[1] for col in resultado]
            if 'valor_unitario' not in colunas and 'preco' in colunas:
                print("INFORMAÇÃO: Sistema usando coluna 'preco' no lugar de 'valor_unitario' na tabela vendas.")
                print(f"Colunas disponíveis: {colunas}")
                self.mostrou_info_valor_unitario = True
        
        return resultado
    
    def verificar_e_atualizar_estrutura(self):
        """Verifica e atualiza a estrutura do banco de dados se necessário"""
        cursor = self.conn.cursor()
        
        # Verificar a estrutura da tabela clientes
        colunas_clientes = [col[1] for col in self.verificar_estrutura_tabela('clientes')]
        
        # Verificar se a coluna data_cadastro existe
        if 'data_cadastro' not in colunas_clientes:
            try:
                # SQLite não permite CURRENT_TIMESTAMP em ALTER TABLE,
                # então adicionamos a coluna sem valor padrão
                cursor.execute("ALTER TABLE clientes ADD COLUMN data_cadastro TEXT")
                self.conn.commit()
                print("Coluna data_cadastro adicionada à tabela clientes")
                # Atualizar o cache
                self.cache_estrutura.pop('clientes', None)
            except Exception as e:
                print(f"Erro ao adicionar coluna data_cadastro: {e}")
        
        # Verificar se nomes de colunas mudaram de 'notas' para 'nota'
        if 'notas' in colunas_clientes and 'nota' not in colunas_clientes:
            try:
                # SQLite não permite renomear colunas diretamente, então vamos criar uma tabela temporária
                cursor.execute("""
                    CREATE TABLE clientes_temp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        telefone TEXT,
                        nota TEXT,
                        data_cadastro TEXT
                    )
                """)
                
                # Copiar dados com o novo nome de coluna
                cursor.execute("""
                    INSERT INTO clientes_temp (id, nome, telefone, nota, data_cadastro)
                    SELECT id, nome, telefone, notas, data_cadastro FROM clientes
                """)
                
                # Remover tabela antiga
                cursor.execute("DROP TABLE clientes")
                
                # Renomear tabela temporária
                cursor.execute("ALTER TABLE clientes_temp RENAME TO clientes")
                
                self.conn.commit()
                print("Coluna 'notas' renomeada para 'nota'")
                # Atualizar o cache
                self.cache_estrutura.pop('clientes', None)
            except Exception as e:
                print(f"Erro ao renomear coluna notas para nota: {e}")
        
        # Verificar estrutura da tabela vendas uma única vez
        # Apenas chamar para garantir que está em cache
        self.verificar_estrutura_tabela('vendas')
        
        cursor.close()
    
    def verificar_tabela_vendas_excluidas(self):
        """Verifica se a tabela de vendas excluídas existe e está correta"""
        try:
            cursor = self.conn.cursor()
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendas_excluidas'")
            tabela_existe = cursor.fetchone() is not None
            
            if not tabela_existe:
                print("ALERTA: Tabela vendas_excluidas não existe. Criando...")
                # Recriar a tabela
                cursor.execute('''
                CREATE TABLE vendas_excluidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id INTEGER,
                    cliente_id INTEGER,
                    cliente_nome TEXT,
                    produto TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    valor_total REAL NOT NULL,
                    data_venda TEXT,
                    data_exclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
                ''')
                self.conn.commit()
                print("INFO: Tabela vendas_excluidas criada com sucesso")
            else:
                # Verificar estrutura da tabela
                cursor.execute("PRAGMA table_info(vendas_excluidas)")
                colunas = [col[1] for col in cursor.fetchall()]
                colunas_esperadas = ['id', 'venda_id', 'cliente_id', 'cliente_nome', 'produto', 
                                   'quantidade', 'valor_total', 'data_venda', 'data_exclusao']
                
                colunas_faltantes = [col for col in colunas_esperadas if col not in colunas]
                if colunas_faltantes:
                    print(f"ALERTA: Faltam colunas na tabela vendas_excluidas: {colunas_faltantes}")
                    # Aqui poderíamos adicionar código para corrigir a estrutura
                else:
                    print("INFO: Tabela vendas_excluidas verificada com sucesso")
            
            cursor.close()
        except Exception as e:
            print(f"ERRO ao verificar tabela vendas_excluidas: {e}")
    
    def verificar_tabela_notificacoes(self):
        """Verifica se a tabela de notificações de pagamentos pendentes existe e a cria se necessário"""
        try:
            cursor = self.conn.cursor()
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notificacoes_pagamento'")
            tabela_existe = cursor.fetchone() is not None
            
            if not tabela_existe:
                print("ALERTA: Tabela notificacoes_pagamento não existe. Criando...")
                # Criar a tabela
                cursor.execute('''
                CREATE TABLE notificacoes_pagamento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    data_notificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pendente',
                    valor_pendente REAL,
                    observacao TEXT,
                    tipo TEXT DEFAULT 'sistema',
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
                ''')
                self.conn.commit()
                print("INFO: Tabela notificacoes_pagamento criada com sucesso")
            else:
                # Verificar se a coluna 'tipo' existe na tabela
                cursor.execute("PRAGMA table_info(notificacoes_pagamento)")
                colunas = [col[1] for col in cursor.fetchall()]
                
                if 'tipo' not in colunas:
                    print("ALERTA: Coluna 'tipo' não encontrada na tabela notificacoes_pagamento. Adicionando...")
                    cursor.execute("ALTER TABLE notificacoes_pagamento ADD COLUMN tipo TEXT DEFAULT 'sistema'")
                    self.conn.commit()
                    print("INFO: Coluna 'tipo' adicionada com sucesso na tabela notificacoes_pagamento")
            
            cursor.close()
        except Exception as e:
            print(f"ERRO ao verificar tabela notificacoes_pagamento: {e}")
    
    def adicionar_cliente(self, nome, telefone, notas=""):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO clientes (nome, telefone, nota)
        VALUES (?, ?, ?)
        ''', (nome, telefone, notas))
        self.conn.commit()
        return cursor.lastrowid
    
    def listar_clientes(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM clientes ORDER BY nome')
        return cursor.fetchall()
    
    def adicionar_venda(self, cliente_id, produto, quantidade, valor_unitario):
        valor_total = quantidade * valor_unitario
        cursor = self.conn.cursor()
        
        # Verificando a estrutura da tabela para determinar o nome correto da coluna
        colunas = [col[1] for col in self.verificar_estrutura_tabela('vendas')]
        
        # Se tiver coluna preco, usa preco; senão, tenta valor_unitario
        if 'preco' in colunas:
            cursor.execute('''
            INSERT INTO vendas (cliente_id, produto, quantidade, preco, valor_total)
            VALUES (?, ?, ?, ?, ?)
            ''', (cliente_id, produto, quantidade, valor_unitario, valor_total))
        elif 'valor_unitario' in colunas:
            cursor.execute('''
            INSERT INTO vendas (cliente_id, produto, quantidade, valor_unitario, valor_total)
            VALUES (?, ?, ?, ?, ?)
            ''', (cliente_id, produto, quantidade, valor_unitario, valor_total))
        else:
            raise ValueError("Estrutura de tabela incompatível: não encontrada coluna para valor unitário")
            
        self.conn.commit()
        return cursor.lastrowid
    
    def listar_vendas_cliente(self, cliente_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.id, c.nome, v.produto, v.quantidade, v.valor_total, v.data_venda 
            FROM vendas v 
            JOIN clientes c ON v.cliente_id = c.id 
            WHERE v.cliente_id = ? 
            ORDER BY v.data_venda DESC
        """, (cliente_id,))
        vendas = cursor.fetchall()
        cursor.close()
        return vendas
    
    def registrar_exclusao_venda(self, venda_id):
        """
        Registra a exclusão de uma venda na tabela de histórico
        """
        cursor = self.conn.cursor()
        
        # Obter os dados da venda antes de excluí-la
        try:
            # Obter informações da venda e do cliente
            cursor.execute("""
                SELECT v.id, v.cliente_id, c.nome, v.produto, v.quantidade, 
                       v.valor_total, v.data_venda
                FROM vendas v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.id = ?
            """, (venda_id,))
            
            venda = cursor.fetchone()
            if not venda:
                print(f"ERRO: Venda ID {venda_id} não encontrada para registro de exclusão")
                return False
                
            # Inserir na tabela de vendas excluídas
            cursor.execute("""
                INSERT INTO vendas_excluidas 
                (venda_id, cliente_id, cliente_nome, produto, quantidade, 
                 valor_total, data_venda)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (venda[0], venda[1], venda[2], venda[3], venda[4], venda[5], venda[6]))
            
            self.conn.commit()
            print(f"INFO: Venda ID {venda_id} registrada na tabela de exclusões com sucesso")
            return True
            
        except Exception as e:
            print(f"ERRO ao registrar exclusão de venda {venda_id}: {e}")
            return False
    
    def excluir_venda(self, venda_id):
        """Exclui uma venda específica sem registrar a exclusão (deve ser chamado após registrar_exclusao_venda)"""
        cursor = self.conn.cursor()
        
        # Excluir a venda diretamente, sem chamar registrar_exclusao_venda novamente
        # pois isso já deve ter sido feito pelo método que está chamando esta função
        cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
        
        self.conn.commit()
        cursor.close()
        return True
    
    def atualizar_venda(self, venda_id, produto, quantidade, valor):
        """Atualiza os dados de uma venda"""
        cursor = self.conn.cursor()
        
        # Verificar qual é o nome da coluna de preço (usando o cache)
        colunas = [col[1] for col in self.verificar_estrutura_tabela('vendas')]
        valor_total = quantidade * valor
        
        # Não exibir mensagens repetitivas, apenas usar as colunas corretas
        if 'preco' in colunas:
            cursor.execute("""
                UPDATE vendas 
                SET produto = ?, quantidade = ?, preco = ?, valor_total = ? 
                WHERE id = ?
            """, (produto, quantidade, valor, valor_total, venda_id))
        elif 'valor_unitario' in colunas:
            cursor.execute("""
                UPDATE vendas 
                SET produto = ?, quantidade = ?, valor_unitario = ?, valor_total = ? 
                WHERE id = ?
            """, (produto, quantidade, valor, valor_total, venda_id))
        else:
            # Fallback: tentar usar valor apenas, sem exibir mensagem (já exibimos na inicialização)
            cursor.execute("""
                UPDATE vendas 
                SET produto = ?, quantidade = ?, valor = ? 
                WHERE id = ?
            """, (produto, quantidade, valor, venda_id))
        
        self.conn.commit()
        cursor.close()
        return True
    
    def atualizar_notas_cliente(self, cliente_id, notas):
        """Atualiza as notas de um cliente"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE clientes 
            SET nota = ? 
            WHERE id = ?
        """, (notas, cliente_id))
        self.conn.commit()
        cursor.close()
        return True
    
    def obter_ultima_venda(self, cliente_id):
        """
        Retorna a última venda de um cliente específico
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, data_venda, produto, quantidade, preco, valor_total 
        FROM vendas 
        WHERE cliente_id = ? 
        ORDER BY data_venda DESC
        LIMIT 1
        ''', (cliente_id,))
        return cursor.fetchone()
    
    def obter_total_vendas_cliente(self, cliente_id):
        """
        Calcula o total de todas as vendas de um cliente
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT SUM(valor_total) 
        FROM vendas 
        WHERE cliente_id = ?
        ''', (cliente_id,))
        resultado = cursor.fetchone()[0]
        return resultado if resultado else 0.0
    
    def obter_id_cliente(self, nome_cliente):
        """
        Obtém o ID de um cliente a partir do nome
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM clientes WHERE nome = ?', (nome_cliente,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    
    def fazer_backup(self, caminho_destino):
        """
        Cria uma cópia de backup do banco de dados atual
        """
        try:
            # Garantir que o diretório de destino existe
            os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
            
            # Fecha a conexão para garantir que todas as operações foram concluídas
            self.conn.close()
            
            # Copia o arquivo para o destino
            shutil.copy2(self.database_path, caminho_destino)
            
            # Reabre a conexão
            self.conn = sqlite3.connect(self.database_path)
            
            print(f"Backup criado com sucesso em: {caminho_destino}")
            return True, "Backup criado com sucesso!"
        except Exception as e:
            # Reabre a conexão em caso de erro
            self.conn = sqlite3.connect(self.database_path)
            print(f"Erro ao criar backup: {str(e)}")
            return False, f"Erro ao criar backup: {str(e)}"
    
    def restaurar_backup(self, caminho_backup):
        """
        Restaura o banco de dados a partir de um arquivo de backup
        """
        try:
            # Verifica se o arquivo de backup existe
            if not os.path.exists(caminho_backup):
                return False, "Arquivo de backup não encontrado!"
            
            # Fecha a conexão atual
            self.conn.close()
            
            # Cria um backup do banco atual antes de substituir (por segurança)
            if os.path.exists(self.database_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_seguranca = os.path.join(os.path.dirname(self.database_path), f"sistema_fiado.db.bak_{timestamp}")
                shutil.copy2(self.database_path, backup_seguranca)
            
            # Substitui o arquivo atual pelo backup
            shutil.copy2(caminho_backup, self.database_path)
            
            # Reconecta ao banco de dados
            self.conn = sqlite3.connect(self.database_path)
            
            return True, "Banco de dados restaurado com sucesso!"
        except Exception as e:
            # Tenta reconectar ao banco de dados original em caso de erro
            try:
                self.conn = sqlite3.connect(self.database_path)
            except:
                pass
            return False, f"Erro ao restaurar backup: {str(e)}"
    
    def obter_id_cliente_por_venda(self, venda_id):
        """
        Obtém o ID do cliente de uma venda específica
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT cliente_id FROM vendas WHERE id = ?', (venda_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    
    def atualizar_cliente(self, cliente_id, nome, telefone):
        """
        Atualiza o nome e telefone de um cliente
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE clientes 
        SET nome = ?, telefone = ?
        WHERE id = ?
        ''', (nome, telefone, cliente_id))
        self.conn.commit()
    
    def fazer_backup_automatico(self):
        """
        Cria um backup automático do banco de dados na pasta 'database/backups'
        """
        try:
            # Garantir que a pasta de backups existe
            if not os.path.exists(self.backups_dir):
                os.makedirs(self.backups_dir)
                print(f"Pasta backups criada em: {self.backups_dir}")
            
            # Gera nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho_destino = os.path.join(self.backups_dir, f"backup_{timestamp}.db")
            
            # Realiza o backup
            return self.fazer_backup(caminho_destino)
        except Exception as e:
            print(f"Erro ao criar backup automático: {str(e)}")
            return False, f"Erro ao criar backup automático: {str(e)}"
    
    def gerar_relatorio_vendas(self, data_inicio=None, data_fim=None, cliente_id=None):
        """
        Gera um relatório de vendas por período e/ou cliente
        
        Args:
            data_inicio: Data inicial do relatório (opcional)
            data_fim: Data final do relatório (opcional)
            cliente_id: ID do cliente para filtrar (opcional)
            
        Returns:
            Lista de vendas no período especificado
        """
        cursor = self.conn.cursor()
        
        # Base da consulta SQL
        sql = '''
        SELECT v.id, c.nome, v.produto, v.quantidade, v.valor_total, v.data_venda
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE 1=1
        '''
        
        # Parâmetros para a consulta
        params = []
        
        # Adiciona filtro de data inicial
        if data_inicio:
            sql += " AND v.data_venda >= ?"
            params.append(data_inicio)
        
        # Adiciona filtro de data final
        if data_fim:
            sql += " AND v.data_venda <= ?"
            params.append(data_fim)
        
        # Adiciona filtro de cliente
        if cliente_id:
            sql += " AND v.cliente_id = ?"
            params.append(cliente_id)
        
        # Ordena por data
        sql += " ORDER BY v.data_venda DESC"
        
        # Executa a consulta
        cursor.execute(sql, params)
        return cursor.fetchall()
    
    def gerar_relatorio_clientes_devedores(self):
        """
        Gera um relatório de clientes com valores pendentes
        
        Returns:
            Lista de clientes com o total devido por cada um
        """
        cursor = self.conn.cursor()
        
        sql = '''
        SELECT c.id, c.nome, c.telefone, SUM(v.valor_total) as total_devido
        FROM clientes c
        JOIN vendas v ON c.id = v.cliente_id
        GROUP BY c.id
        ORDER BY total_devido DESC
        '''
        
        cursor.execute(sql)
        return cursor.fetchall()
    
    def cliente_tem_vendas(self, cliente_id):
        """
        Verifica se o cliente possui vendas registradas
        
        Returns:
            bool: True se o cliente tiver vendas, False caso contrário
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM vendas WHERE cliente_id = ?', (cliente_id,))
        resultado = cursor.fetchone()[0]
        return resultado > 0
    
    def excluir_cliente(self, cliente_id):
        """
        Exclui um cliente do banco de dados apenas se não tiver vendas vinculadas
        
        Returns:
            tuple: (bool, str) - Sucesso da operação e mensagem
        """
        cursor = self.conn.cursor()
        
        try:
            # Verificar se o cliente existe
            cursor.execute('SELECT nome FROM clientes WHERE id = ?', (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                return False, "Cliente não encontrado"
            
            # Verificar se o cliente possui vendas
            tem_vendas = self.cliente_tem_vendas(cliente_id)
            
            # Se o cliente tiver vendas, não permitir a exclusão
            if tem_vendas:
                return False, "Não é possível excluir o cliente porque ele possui vendas registradas. Remova as vendas primeiro."
            
            # Se não tiver vendas, pode excluir o cliente
            cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
            self.conn.commit()
            
            return True, "Cliente excluído com sucesso."
                
        except Exception as e:
            self.conn.rollback()
            return False, f"Erro ao excluir cliente: {str(e)}"
    
    def excluir_vendas_cliente(self, cliente_id):
        """
        Remove todas as vendas associadas a um cliente, mas mantém o cliente cadastrado
        """
        cursor = self.conn.cursor()
        
        # Primeiro obter todas as vendas do cliente
        cursor.execute('SELECT id FROM vendas WHERE cliente_id = ?', (cliente_id,))
        vendas = cursor.fetchall()
        
        # Registrar cada venda no histórico antes de excluir
        for venda in vendas:
            venda_id = venda[0]
            self.registrar_exclusao_venda(venda_id)
        
        # Excluir as vendas associadas ao cliente
        cursor.execute('DELETE FROM vendas WHERE cliente_id = ?', (cliente_id,))
        
        self.conn.commit()
    
    def exportar_dados_csv(self, caminho):
        """
        Exporta os dados completos de clientes e vendas para um arquivo CSV
        """
        try:
            import csv
            from datetime import datetime
            
            # Gerar nome do arquivo com data/hora se não for especificado
            if not caminho.lower().endswith('.csv'):
                caminho += '.csv'
            
            with open(caminho, 'w', newline='', encoding='utf-8') as arquivo:
                writer = csv.writer(arquivo)
                
                # Escrever cabeçalho
                writer.writerow(['RELATÓRIO COMPLETO DO SISTEMA'])
                writer.writerow([f'Data de exportação: {datetime.now().strftime("%d/%m/%Y %H:%M")}'])
                writer.writerow([])
                
                # Seção de clientes
                writer.writerow(['CLIENTES'])
                writer.writerow(['ID', 'Nome', 'Telefone', 'Total em Vendas', 'Data de Cadastro'])
                
                cursor = self.conn.cursor()
                clientes = self.listar_clientes()
                
                for cliente in clientes:
                    cliente_id = cliente[0]
                    nome = cliente[1]
                    telefone = cliente[2] or ""
                    data_cadastro = cliente[4]
                    
                    # Calcular total em vendas
                    total = self.obter_total_vendas_cliente(cliente_id)
                    
                    writer.writerow([cliente_id, nome, telefone, f"R$ {total:.2f}", data_cadastro])
                
                writer.writerow([])
                
                # Seção de vendas
                writer.writerow(['VENDAS'])
                writer.writerow(['ID', 'Cliente', 'Produto', 'Quantidade', 'Valor Unitário', 'Valor Total', 'Data'])
                
                # Obter todas as vendas
                cursor.execute('''
                SELECT v.id, c.nome, v.produto, v.quantidade, v.preco, v.valor_total, v.data_venda
                FROM vendas v
                JOIN clientes c ON v.cliente_id = c.id
                ORDER BY v.data_venda DESC
                ''')
                
                vendas = cursor.fetchall()
                
                for venda in vendas:
                    venda_id = venda[0]
                    cliente_nome = venda[1]
                    produto = venda[2]
                    quantidade = venda[3]
                    valor_unitario = venda[4]
                    valor_total = venda[5]
                    data = venda[6]
                    
                    writer.writerow([
                        venda_id, 
                        cliente_nome, 
                        produto, 
                        quantidade, 
                        f"R$ {valor_unitario:.2f}", 
                        f"R$ {valor_total:.2f}", 
                        data
                    ])
                
                return True, "Dados exportados com sucesso para CSV!"
                
        except Exception as e:
            return False, f"Erro ao exportar dados: {str(e)}"
    
    def __del__(self):
        """
        Fecha a conexão com o banco de dados quando o objeto é destruído
        """
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def obter_cliente(self, cliente_id):
        """Obtém um cliente pelo ID de forma adaptável à estrutura existente"""
        cursor = self.conn.cursor()
        
        # Usar o cache para evitar consultas repetitivas
        colunas = [col[1] for col in self.verificar_estrutura_tabela('clientes')]
        
        # Construir uma consulta SQL que se adapta às colunas existentes
        # Não mostrar mensagens repetitivas, apenas construir a consulta correta
        colunas_seguras = [col for col in ['id', 'nome', 'telefone', 'nota', 'notas', 'data_cadastro'] if col in colunas]
        consulta = f"SELECT {', '.join(colunas_seguras)} FROM clientes WHERE id = ?"
        
        try:
            cursor.execute(consulta, (cliente_id,))
            cliente = cursor.fetchone()
            
            # Se temos 'notas' em vez de 'nota', adaptar o resultado para o formato esperado
            if cliente and 'notas' in colunas_seguras and 'nota' not in colunas_seguras:
                # Criar uma lista com os valores
                valores = list(cliente)
                # Encontrar o índice da coluna 'notas'
                idx_notas = colunas_seguras.index('notas')
                # Inserir o valor na posição onde o código espera a coluna 'nota' (posição 3)
                if len(valores) <= 3:
                    valores.append(cliente[idx_notas])
                else:
                    valores[3] = cliente[idx_notas]
                cliente = tuple(valores)
            
            cursor.close()
            return cliente
        except sqlite3.OperationalError as e:
            print(f"Erro na consulta SQL: {e}")
            # Fallback para uma consulta básica
            try:
                cursor.execute("SELECT id, nome, telefone, '' FROM clientes WHERE id = ?", (cliente_id,))
                cliente = cursor.fetchone()
                cursor.close()
                return cliente
            except Exception as e2:
                print(f"Erro no fallback: {e2}")
                cursor.close()
                # Retornar uma tupla com valores padrão
                return (cliente_id, "", "", "")
    
    def remover_venda(self, venda_id):
        """Método legado - Agora apenas chama excluir_venda depois de registrar a exclusão"""
        print(f"INFO: Método legado remover_venda chamado para venda ID {venda_id}")
        
        # Se o chamador não registrou a exclusão explicitamente, fazê-lo aqui
        self.registrar_exclusao_venda(venda_id)
        
        # Excluir a venda
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM vendas WHERE id = ?', (venda_id,))
        self.conn.commit()
    
    # Métodos para a HomeView
    def contar_clientes(self):
        """Retorna o número total de clientes cadastrados"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clientes")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Erro ao contar clientes: {str(e)}")
            return 0
    
    def calcular_total_vendas(self):
        """Retorna o valor total de todas as vendas"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT SUM(valor_total) FROM vendas")
            total = cursor.fetchone()[0]
            return total if total is not None else 0
        except Exception as e:
            print(f"Erro ao calcular total de vendas: {str(e)}")
            return 0
    
    def contar_produtos_vendidos(self):
        """Retorna a quantidade total de produtos vendidos"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT SUM(quantidade) FROM vendas")
            total = cursor.fetchone()[0]
            return int(total) if total is not None else 0
        except Exception as e:
            print(f"Erro ao contar produtos vendidos: {str(e)}")
            return 0
            
    def listar_produtos_registrados(self):
        """Retorna lista de produtos únicos com quantidade total vendida e valor total"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    produto, 
                    SUM(quantidade) as total_quantidade,
                    SUM(valor_total) as total_valor
                FROM vendas 
                GROUP BY produto
                ORDER BY total_quantidade DESC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao listar produtos registrados: {str(e)}")
            return []
            
    def contar_pendencias(self):
        """Retorna o número de clientes com pendências"""
        devedores = self.gerar_relatorio_clientes_devedores()
        return len(devedores)
    
    def obter_vendas_excluidas(self, data_inicio=None, data_fim=None, cliente_id=None):
        """
        Obtém as vendas excluídas com filtros opcionais de período e cliente
        """
        cursor = self.conn.cursor()
        
        # Primeiro verificar se a tabela existe
        try:
            # Verificar quantidade de registros para diagnóstico
            cursor.execute("SELECT COUNT(*) FROM vendas_excluidas")
            count = cursor.fetchone()[0]
            print(f"INFO: Encontrados {count} registros na tabela vendas_excluidas")
            
            query = """
                SELECT 
                    id, venda_id, cliente_nome, produto, quantidade, 
                    valor_total, data_venda, data_exclusao
                FROM vendas_excluidas
                WHERE 1=1
            """
            
            params = []
            
            # Adicionar filtros se fornecidos
            if data_inicio and data_fim:
                query += " AND date(data_exclusao) BETWEEN ? AND ?"
                params.extend([data_inicio, data_fim])
                print(f"DEBUG: Aplicando filtro de data de {data_inicio} até {data_fim}")
            else:
                print("DEBUG: Sem filtro de data, mostrando todos os registros")
                
            if cliente_id:
                query += " AND cliente_id = ?"
                params.append(cliente_id)
                print(f"DEBUG: Aplicando filtro de cliente ID {cliente_id}")
                
            query += " ORDER BY data_exclusao DESC"
            
            print(f"DEBUG: Executando query: {query} com params: {params}")
            cursor.execute(query, params)
            vendas = cursor.fetchall()
            print(f"INFO: Consulta retornou {len(vendas)} vendas excluídas")
            
            # Imprimir detalhes dos registros para diagnóstico se não retornou nada
            if len(vendas) == 0 and count > 0:
                print("DEBUG: Nenhuma venda foi retornada apesar de haver registros na tabela. Listando todos:")
                cursor.execute("SELECT id, cliente_nome, produto, data_exclusao FROM vendas_excluidas LIMIT 10")
                debug_vendas = cursor.fetchall()
                for v in debug_vendas:
                    print(f"  - ID: {v[0]}, Cliente: {v[1]}, Produto: {v[2]}, Excluído em: {v[3]}")
                    
            cursor.close()
            return vendas
            
        except Exception as e:
            print(f"ERRO ao obter vendas excluídas: {e}")
            cursor.close()
            return []
    
    def limpar_vendas_excluidas(self):
        """
        Remove todos os registros da tabela de vendas excluídas
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            cursor = self.conn.cursor()
            
            # Verificar quantos registros existem
            cursor.execute("SELECT COUNT(*) FROM vendas_excluidas")
            count = cursor.fetchone()[0]
            
            # Limpar a tabela
            cursor.execute("DELETE FROM vendas_excluidas")
            self.conn.commit()
            
            cursor.close()
            return True, f"Histórico de {count} vendas excluídas foi limpo com sucesso!"
        except Exception as e:
            print(f"ERRO ao limpar vendas excluídas: {e}")
            return False, f"Erro ao limpar histórico: {str(e)}"
    
    def obter_clientes_com_pagamentos_pendentes(self, valor_minimo=0):
        """
        Obtém a lista de clientes com pagamentos pendentes com informações para contato
        
        Args:
            valor_minimo: Valor mínimo em reais para filtrar os clientes (padrão: 0)
            
        Returns:
            Lista de tuplas (id, nome, telefone, total_devido)
        """
        cursor = self.conn.cursor()
        
        try:
            sql = '''
            SELECT c.id, c.nome, c.telefone, SUM(v.valor_total) as total_devido
            FROM clientes c
            JOIN vendas v ON c.id = v.cliente_id
            GROUP BY c.id
            HAVING total_devido >= ?
            ORDER BY total_devido DESC
            '''
            
            cursor.execute(sql, (valor_minimo,))
            clientes_devedores = cursor.fetchall()
            
            # Filtrar apenas clientes com telefone cadastrado
            clientes_com_telefone = [cliente for cliente in clientes_devedores if cliente[2] and cliente[2].strip()]
            
            return clientes_com_telefone
        except Exception as e:
            print(f"ERRO ao obter clientes com pagamentos pendentes: {e}")
            return []
        finally:
            cursor.close()
    
    def registrar_notificacao(self, cliente_id, valor_pendente, observacao=None, tipo='sistema'):
        """
        Registra uma notificação enviada a um cliente sobre pagamento pendente
        
        Args:
            cliente_id: ID do cliente notificado
            valor_pendente: Valor total pendente de pagamento
            observacao: Observação adicional sobre a notificação (opcional)
            tipo: Tipo de notificação ('sistema', 'whatsapp', etc.) (padrão: 'sistema')
            
        Returns:
            bool: True se a notificação foi registrada com sucesso, False caso contrário
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO notificacoes_pagamento (cliente_id, valor_pendente, observacao, status, tipo)
            VALUES (?, ?, ?, 'enviada', ?)
            ''', (cliente_id, valor_pendente, observacao, tipo))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"ERRO ao registrar notificação: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()
    
    def obter_historico_notificacoes(self, cliente_id=None, dias=30):
        """
        Obtém o histórico de notificações enviadas
        
        Args:
            cliente_id: ID do cliente para filtrar (opcional)
            dias: Número de dias para trás a considerar (padrão: 30)
            
        Returns:
            Lista de notificações enviadas
        """
        cursor = self.conn.cursor()
        
        try:
            sql = '''
            SELECT n.id, c.nome, n.data_notificacao, n.valor_pendente, n.status, n.observacao, n.tipo
            FROM notificacoes_pagamento n
            JOIN clientes c ON n.cliente_id = c.id
            WHERE date(n.data_notificacao) >= date('now', ?)
            '''
            
            params = [f'-{dias} days']
            
            if cliente_id:
                sql += " AND n.cliente_id = ?"
                params.append(cliente_id)
            
            sql += " ORDER BY n.data_notificacao DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"ERRO ao obter histórico de notificações: {e}")
            return []
        finally:
            cursor.close() 