# Sistema de Gestão de Vendas e Clientes

## Melhorias Implementadas

### Validação de Campos do Cliente
1. **Validação do Nome do Cliente**:
   - Implementação de validação para permitir apenas letras, espaços e caracteres acentuados
   - Uso de `QRegularExpressionValidator` com expressão regular `[A-Za-zÀ-ú ]+`
   - Aplicado em ambos os formulários: cadastro e edição de cliente

2. **Formatação e Validação do Telefone**:
   - Validação para permitir apenas números
   - Formatação automática para o padrão brasileiro: (00) 00000-0000
   - Na tela de cadastro: implementação via eventos `textChanged`
   - Na tela de edição: implementação via `inputMask`

### Melhorias na Interface de Vendas
1. **Estrutura e Layout**:
   - Adição de tamanho mínimo à janela (900x700)
   - Implementação de área de rolagem para todos os elementos
   - Reorganização de elementos para evitar sobreposição
   - Reposicionamento dos botões para fora do card principal

2. **Aprimoramentos Visuais**:
   - Remoção de bordas/contornos desnecessários em textos e ícones
   - Aplicação de estilos consistentes
   - Aumento da altura de botões para melhor interatividade
   - Adição de espaçamento adequado entre elementos

3. **Funcionalidades de Entrada de Dados**:
   - Conversão automática para maiúsculas no campo de produto
   - Quantidade padrão iniciando em 1
   - Validação numérica para quantidade (apenas números inteiros positivos)
   - Formatação monetária em tempo real para o campo de valor

4. **Seção de Resumo da Venda**:
   - Implementação de cálculo automático (quantidade × preço = total)
   - Uso de QLabels com formatação HTML para melhor visualização
   - Atualização em tempo real dos valores
   - Destaque visual para o valor total

## Stack Tecnológica
- **Framework GUI**: PySide6 (Qt para Python)
- **Backend**: Python com SQLite (sistema_fiado.db)
- **Estrutura**: Arquitetura MVC simplificada

## Recursos
- Cadastro e edição de clientes
- Registro de vendas
- Histórico de vendas
- Relatórios
- Gerenciamento de backup

## Melhorias Adicionais
1. **Consistência na Interface**:
   - Adicionado ícone à seção de resumo da venda para manter consistência visual
   - Corrigido problema de caracteres inválidos no título da seção de resumo

2. **Simplificação da Validação de Telefone**:
   - Implementação unificada do campo de telefone usando inputMask
   - Substituição da formatação manual via eventos por máscara de entrada
   - Mantém a mesma funcionalidade com código mais limpo e manutenível

## Funcionalidades

- Cadastro de clientes com nome, telefone e notas
- Lista de clientes cadastrados
- Registro de vendas com produto, quantidade e valor
- Histórico de vendas por cliente
- Edição e remoção de vendas
- Cálculo automático de valores totais
- Relatórios de vendas por período
- Relatório de clientes devedores
- Exportação de relatórios para CSV
- Sistema de backup e restauração

## Requisitos

- Python 3.8 ou superior
- PyQt6
- SQLite3

## Instalação

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando o Sistema

Para iniciar o sistema, execute:
```bash
python main.py
```

## Estrutura do Projeto

- `main.py`: Arquivo principal do sistema
- `database.py`: Gerenciamento do banco de dados
- `styles.py`: Estilos CSS para a interface
- `views/`: Diretório contendo as interfaces do sistema
  - `cliente_view.py`: Interface de cadastro de clientes
  - `venda_view.py`: Interface de registro de vendas
  - `lista_clientes_view.py`: Interface de listagem de clientes
  - `historico_vendas_view.py`: Interface de histórico de vendas
  - `relatorio_view.py`: Interface de relatórios e análises

## Banco de Dados

O sistema utiliza SQLite como banco de dados, armazenando os dados localmente no arquivo `sistema_fiado.db`. O banco é criado automaticamente na primeira execução do sistema.

## Backup e Restauração

O sistema permite fazer backup do banco de dados a qualquer momento através da interface de relatórios. Os backups são armazenados na pasta `backups/` com timestamp no nome do arquivo. 

Para restaurar um backup, utilize o botão "Restaurar Backup" no rodapé do menu lateral.

## Contribuição

Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Faça push para a branch
5. Abra um Pull Request 