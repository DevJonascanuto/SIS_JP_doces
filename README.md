# 🍬 JP Doces — Sistema de Pedidos

Sistema web completo para gestão de pedidos, produtos e clientes da **JP Doces**, desenvolvido em Python com Flask, banco de dados MySQL e interface moderna com Bootstrap 5.

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Como Usar](#-como-usar)
- [Banco de Dados](#-banco-de-dados)
- [Geração de PDF](#-geração-de-pdf)
- [Categorias de Produtos](#-categorias-de-produtos)

---

## ✅ Funcionalidades

| Módulo | Descrição |
|---|---|
| 📊 **Dashboard** | Painel com contadores (produtos, clientes, pedidos, receita total) e últimos pedidos |
| 📦 **Produtos** | Cadastro completo com código, nome, categoria, preço e unidade |
| 🔍 **Busca Inteligente** | Autocomplete em tempo real por **nome** ou **código** do produto |
| 👥 **Clientes** | Cadastro de clientes com CPF/CNPJ, telefone, endereço e histórico |
| 🛒 **Novo Pedido** | Interface de carrinho — adicione produtos, ajuste quantidades, aplique desconto |
| 📋 **Histórico** | Lista todos os pedidos com filtro por status e busca por cliente/número |
| 📄 **PDF Profissional** | Gera PDF do pedido com layout colorido, tabela de itens e totais |
| 🔄 **Status de Pedido** | Controle de fluxo: Pendente → Confirmado → Entregue / Cancelado |

---

## 🛠 Tecnologias

- **Backend:** Python 3.9+ · Flask 3.x · SQLAlchemy
- **Banco de Dados:** MySQL 8 via PyMySQL
- **Frontend:** Bootstrap 5.3 · Bootstrap Icons · Google Fonts (Poppins)
- **PDF:** ReportLab
- **Animações:** CSS animations · JavaScript vanilla

---

## 📁 Estrutura do Projeto

```
SIS_JP_doces/
│
├── app.py                   # Aplicação Flask principal (rotas, lógica)
├── config.py                # Configurações (banco, chave secreta)
├── extensions.py            # Instância do SQLAlchemy
├── models.py                # Modelos do banco (Produto, Cliente, Pedido, Item)
├── seed_data.py             # 161 produtos do catálogo JP Doces
├── setup.py                 # Script de instalação e configuração inicial
├── requirements.txt         # Dependências Python
├── .env                     # Variáveis de ambiente (credenciais)
│
├── utils/
│   └── pdf_generator.py     # Gerador de PDF com ReportLab
│
├── static/
│   ├── css/
│   │   └── style.css        # Estilos completos (tema pink/purple)
│   └── js/
│       └── main.js          # JavaScript (sidebar, counters, ripple)
│
└── templates/
    ├── base.html            # Layout base (sidebar + topbar)
    ├── dashboard.html       # Painel principal
    ├── produtos/
    │   ├── lista.html       # Listagem com filtros
    │   └── form.html        # Formulário de cadastro/edição
    ├── clientes/
    │   ├── lista.html       # Listagem de clientes
    │   └── form.html        # Formulário de cadastro/edição
    └── pedidos/
        ├── lista.html       # Histórico de pedidos
        ├── novo.html        # Criação de pedido (carrinho)
        └── detalhe.html     # Visualização detalhada do pedido
```

---

## ⚙️ Pré-requisitos

- **Python 3.9** ou superior
- **MySQL Server 8.x** instalado e rodando
- **pip** (gerenciador de pacotes Python)

---

## 🚀 Instalação e Configuração

### 1. Configure o banco de dados

Edite o arquivo `.env` na raiz do projeto com suas credenciais do MySQL:

```env
SECRET_KEY=jp-doces-chave-super-secreta-2024
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha_aqui
DB_NAME=jp_doces
```

> **Nota:** Se o MySQL não tem senha, deixe `DB_PASSWORD=` em branco.

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

Pacotes instalados:
- `Flask` — Framework web
- `Flask-SQLAlchemy` — ORM para banco de dados
- `PyMySQL` + `cryptography` — Driver MySQL
- `reportlab` — Geração de PDF
- `python-dotenv` — Leitura do arquivo `.env`
- `Pillow` — Suporte a imagens (PDF)

### 3. Configure o banco e importe os produtos

```bash
python setup.py
```

Este script vai:
- ✅ Criar o banco de dados `jp_doces` automaticamente
- ✅ Criar todas as tabelas necessárias
- ✅ Importar os **161 produtos** do catálogo JP Doces

### 4. Inicie o sistema

```bash
python app.py
```

Acesse no navegador: **http://localhost:5000**

---

## 📖 Como Usar

### Criando um Pedido

1. Acesse **"Novo Pedido"** no menu lateral
2. **Selecione o cliente** — Digite o nome para busca automática
3. **Adicione produtos** — Digite o nome ou código (ex: `2221` ou `AMENDOIM`)
4. Ajuste as **quantidades** com os botões + e −
5. Clique em **"Adicionar"** para incluir no carrinho
6. Repita para quantos produtos quiser
7. Opcionalmente, adicione um **desconto** e **observações**
8. Clique em **"Finalizar Pedido"**
9. Clique em **"Gerar PDF"** para baixar o pedido formatado

### Cadastrando Produtos

1. Acesse **"Produtos"** → **"Novo Produto"**
2. Preencha: Código, Nome, Categoria, Preço e Unidade
3. Salve — o produto já estará disponível na busca de pedidos

### Gerenciando Pedidos

- Na listagem de pedidos, use filtros por **status** ou **busca por nome/número**
- Clique no ícone de olho para ver o **detalhe completo**
- Clique no ícone PDF para **gerar o documento**
- Na tela de detalhe, altere o **status** do pedido

---

## 🗄 Banco de Dados

### Tabelas

#### `produtos`
| Campo | Tipo | Descrição |
|---|---|---|
| id | INT | Chave primária |
| codigo | VARCHAR(20) | Código único do produto |
| nome | VARCHAR(120) | Nome completo |
| categoria | VARCHAR(50) | Categoria (AMENDOIM, BALA, etc.) |
| descricao | TEXT | Descrição adicional |
| preco | DECIMAL(10,2) | Preço unitário |
| unidade | VARCHAR(20) | Unidade (UN, CX, PT, DP, etc.) |
| ativo | BOOLEAN | Produto ativo/inativo |

#### `clientes`
| Campo | Tipo | Descrição |
|---|---|---|
| id | INT | Chave primária |
| nome | VARCHAR(120) | Nome / Razão Social |
| cpf_cnpj | VARCHAR(20) | CPF ou CNPJ |
| telefone | VARCHAR(20) | Telefone / WhatsApp |
| email | VARCHAR(100) | E-mail |
| endereco | VARCHAR(200) | Endereço completo |
| cidade | VARCHAR(80) | Cidade |
| estado | VARCHAR(2) | UF |

#### `pedidos`
| Campo | Tipo | Descrição |
|---|---|---|
| id | INT | Chave primária |
| numero | VARCHAR(20) | Número do pedido (PED00001) |
| cliente_id | INT | FK → clientes |
| data | DATETIME | Data/hora do pedido |
| status | VARCHAR(20) | pendente/confirmado/entregue/cancelado |
| total | DECIMAL(10,2) | Valor total |
| desconto | DECIMAL(10,2) | Desconto aplicado |
| observacoes | TEXT | Observações |

#### `itens_pedido`
| Campo | Tipo | Descrição |
|---|---|---|
| id | INT | Chave primária |
| pedido_id | INT | FK → pedidos |
| produto_id | INT | FK → produtos |
| quantidade | DECIMAL(10,3) | Quantidade |
| preco_unitario | DECIMAL(10,2) | Preço no momento da venda |
| subtotal | DECIMAL(10,2) | quantidade × preço_unitario |

---

## 📄 Geração de PDF

O PDF é gerado pelo **ReportLab** com design profissional JP Doces:

- **Cabeçalho** em roxo com o nome do pedido e número
- **Dados do cliente** em tabela organizada
- **Tabela de itens** com código, produto, categoria, quantidade, preço e subtotal
- **Totais** com destaque em rosa
- **Rodapé** com data de geração

Para gerar o PDF de qualquer pedido:
```
GET /pedidos/<id>/pdf
```

---

## 🗂 Categorias de Produtos

O sistema suporta 8 categorias (todas pré-cadastradas com produtos do catálogo):

| Categoria | Exemplos |
|---|---|
| **AMENDOIM** | Doce Delícia, Crock Rio, Felipe, Salgamar |
| **BALA** | Dadinho, Dimbinho, Santa Fé, Fini Tubes, Halls |
| **CHICLETE** | Trident, Poosh Arcor, Chicletão Danny |
| **PIRULITO** | Pop Kiss, Santa Fé Big Pop, Flopito |
| **CHOCOLATE** | Nestlé, Trento, Lacta, Snickers, Twix, Kit Kat |
| **SALGADINHO** | Wanflo, Pingolitos, Bisconobre, Formigão, Fritop |
| **POTE** | Zézinho, Doce Delícia, Ouro Minas, Famoso |
| **DIVERSOS** | Galvani, Nicolinha, Portão de Cambuí, Icegurtt |

---

## 🌐 Rotas da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/produtos` | Lista produtos |
| GET/POST | `/produtos/novo` | Cadastrar produto |
| GET/POST | `/produtos/<id>/editar` | Editar produto |
| POST | `/produtos/<id>/excluir` | Desativar produto |
| **GET** | **`/api/produtos/buscar?q=`** | **API autocomplete de produtos** |
| GET | `/clientes` | Lista clientes |
| GET/POST | `/clientes/novo` | Cadastrar cliente |
| GET/POST | `/clientes/<id>/editar` | Editar cliente |
| **GET** | **`/api/clientes/buscar?q=`** | **API autocomplete de clientes** |
| GET | `/pedidos` | Lista pedidos |
| GET/POST | `/pedidos/novo` | Criar pedido (POST aceita JSON) |
| GET | `/pedidos/<id>` | Detalhe do pedido |
| POST | `/pedidos/<id>/status` | Atualizar status |
| **GET** | **`/pedidos/<id>/pdf`** | **Gerar PDF do pedido** |

---

## 🎨 Identidade Visual

O sistema usa a paleta de cores da JP Doces:

- **Rosa Principal:** `#e91e8c`
- **Roxo:** `#6a0dad` / `#7c3aed`
- **Sidebar:** Gradiente escuro roxo
- **Fonte:** Poppins (Google Fonts)

---

*Sistema desenvolvido para JP Doces — 2024*
