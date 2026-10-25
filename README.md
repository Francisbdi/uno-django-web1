# 🃏 UNO Web 1v1 (Jogador vs Computador) — Django

Projeto desenvolvido para a avaliação **N1** da disciplina de **Desenvolvimento Web 1** (Sistemas de Informação).  
Trata-se de uma implementação web completa e responsiva do clássico jogo de cartas **UNO** no modo **1 contra 1 (Jogador vs IA do Computador)**, construída com **Python**, **Django**, **SQLite** e **JavaScript (ES6+)**.

---

## 🎯 Funcionalidades e Regras Implementadas

- **Baralho Clássico de 100 Cartas Coloridas:**
  - 4 cores oficiais: **Vermelho**, **Azul**, **Verde** e **Amarelo**.
  - Cartas numéricas de `0` a `9`.
  - Cartas de ação especiais:
    - **⊘ Pular Vez (`skip`):** O adversário perde o turno e quem jogou joga novamente.
    - **⇄ Inverter (`reverse`):** Em duelos de 2 jogadores (1v1), equivale a pular a vez do oponente, devolvendo o turno para quem descartou.
    - **+2 Comprar 2 (`draw2`):** O adversário compra 2 cartas imediatamente e perde a vez.
- **Mecânica Oficial de Jogo:**
  - Distribuição inicial de **7 cartas** para o Jogador e **7 cartas** para o Bot, além de **1 carta numérica** inicial no topo do descarte.
  - Validação no servidor (Backend) garantindo que apenas cartas da mesma **cor** ou mesmo **número/símbolo** possam ser descartadas.
  - Destaque visual automático nas cartas da mão do jogador que são válidas no turno atual.
  - **Monte de Compra inteligente:** caso não possua jogada válida, o jogador clica no monte para comprar 1 carta (com reembaralhamento automático do descarte caso o monte se esgote).
  - **IA Estratégica do Bot:** o computador prioriza cartas de ação quando o jogador está próximo de vencer, encadeia combos e escolhe a cor predominante em sua mão.
- **Persistência em Banco de Dados (SQLite):**
  - Registro automático de todas as partidas concluídas através do model `Partida` (`data_hora`, `vencedor`, `turnos` e `cartas_restantes_perdedor`).
  - Painel lateral em tempo real com **Placar Geral acumulado**, taxa de vitórias (%) e histórico detalhado das últimas partidas.

---

## 🏗️ Arquitetura do Projeto

```text
WEB1/
├── core/                           # Aplicação principal do jogo UNO
│   ├── migrations/                 # Migrações do banco de dados SQLite
│   ├── static/core/
│   │   ├── css/style.css           # Estilização moderna das cartas e mesa de jogo
│   │   └── js/game.js              # Consumo da API, animações de turno e efeitos sonoros
│   ├── templates/core/
│   │   └── index.html              # Interface principal responsiva
│   ├── admin.py                    # Configuração do Django Admin para o model Partida
│   ├── models.py                   # Model Partida (histórico e estatísticas no SQLite)
│   ├── tests.py                    # Testes automatizados do motor de jogo e endpoints
│   ├── uno_engine.py               # Motor de regras do UNO, baralho e IA do Bot
│   └── views.py                    # Views e endpoints JSON/API baseados em request.session
├── meu_site/                       # Configurações globais do projeto Django
│   ├── settings.py                 # Configurações do Django, SQLite, pt-br e apps
│   ├── urls.py                     # Roteamento das páginas e endpoints da API
│   └── wsgi.py / asgi.py           # Pontos de entrada para deploy
├── manage.py                       # Utilitário de linha de comando do Django
├── requirements.txt                # Dependências do projeto Python
├── .gitignore                      # Arquivos ignorados pelo Git
└── README.md                       # Documentação do projeto
```

### Endpoints da API (Django Views + Session)

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/` | Renderiza a mesa do jogo UNO e o placar inicial |
| `GET` | `/api/state/` | Retorna o estado atual da partida na sessão (`request.session`) e o placar do SQLite |
| `POST` | `/api/new-game/` | Embaralha um novo baralho e inicia uma nova partida |
| `POST` | `/api/play-card/` | Valida e executa o descarte de uma carta do jogador e aciona o turno do Bot |
| `POST` | `/api/draw-card/` | Compra 1 carta do monte para o jogador |
| `POST` | `/api/pass-turn/` | Passa a vez caso o jogador compre uma carta jogável e decida mantê-la |
| `POST` | `/api/clear-history/` | Limpa o histórico de partidas salvo no banco SQLite |

---

## 🚀 Como Rodar o Projeto Localmente

### 1. Pré-requisitos
- **Python 3.10+** instalado
- **Git** instalado

### 2. Clonar o repositório (ou acessar a pasta do projeto)
```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd WEB1
```

### 3. Criar e ativar o ambiente virtual (`.venv`)

No **Windows (PowerShell)**:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No **Linux / macOS**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 5. Executar as migrações do banco de dados (SQLite)
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Executar os testes automatizados (Opcional)
```bash
python manage.py test
```

### 7. Iniciar o servidor de desenvolvimento
```bash
python manage.py runserver
```

Acesse no navegador: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

