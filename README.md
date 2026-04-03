# Sistema de Medição de Estação Meteorológica IoT

Sistema completo de IoT para coleta, armazenamento e visualização de dados meteorológicos. Um Arduino lê temperatura e umidade via sensor DHT11 e envia os dados por Serial USB para um servidor Flask, que os persiste em SQLite e os expõe em uma API REST com interface web.

---

## Decisões de Arquitetura

| Elemento | Decisão |
|---|---|
| Hardware | Arduino Uno + DHT11 (temperatura e umidade). Sem BMP180 — campo `pressao` suportado mas opcional |
| Leitura Serial | `serial_reader.py` roda como processo separado e faz POST para a API Flask |
| Banco de dados | SQLite com WAL mode para permitir escrita simultânea do Flask e do serial_reader |
| Interface | Jinja2 (server-side rendering) + Chart.js para o gráfico temporal |

---

## Estrutura do Projeto

```
src/
├── app.py              # Aplicação Flask — API REST e rotas HTML
├── database.py         # Funções de acesso ao SQLite (CRUD)
├── serial_reader.py    # Leitura da porta serial → POST para a API
├── schema.sql          # DDL da tabela leituras
├── config.py           # Configurações centralizadas (porta, baud, URLs)
├── populate_db.py      # Script para inserir 30 leituras de exemplo
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/
│   ├── base.html
│   ├── index.html      # Painel principal com gráfico e auto-refresh
│   ├── historico.html  # Histórico paginado
│   ├── detalhe.html    # Leitura individual
│   ├── editar.html     # Formulário de edição (PUT)
│   └── erro.html
└── arduino/
    └── estacao.ino
```

---

## Instalação

### 1. Pré-requisitos

- Python 3.10 ou superior
- Arduino IDE 2.x (para gravar o sketch)

### 2. Ambiente virtual e dependências Python

```bash
# Na raiz do projeto (pasta Sistema-IoT)
python -m venv venv

# Ativar — Windows
venv\Scripts\activate

# Ativar — Linux/macOS
source venv/bin/activate

# Instalar dependências
pip install flask pyserial requests
```

### 3. Variáveis de configuração (opcional)

As configurações padrão estão em `src/config.py`. Você pode sobrescrevê-las com variáveis de ambiente:

```bash
# Windows (PowerShell)
$env:SERIAL_PORTA = "COM5"
$env:FLASK_DEBUG  = "false"

# Linux/macOS
export SERIAL_PORTA=/dev/ttyUSB0
export FLASK_DEBUG=false
```

---

## Como Executar

### 1. Inicializar o banco de dados com dados de exemplo

```bash
cd src
python populate_db.py
```

### 2. Iniciar o servidor Flask

```bash
cd src
python app.py
```

Acesse: http://localhost:5000

### 3. Iniciar a leitura serial (em outro terminal, com Arduino conectado)

```bash
cd src
python serial_reader.py
```

> Se não tiver o Arduino, o sistema funciona normalmente via POST manual (Postman/curl) ou pela interface web.

---

## Rotas da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Painel com últimas 10 leituras + gráfico |
| GET | `/leituras` | Histórico paginado (`?pagina=1&limite=20`) |
| POST | `/leituras` | Cria leitura — body JSON: `{"temperatura": 25.0, "umidade": 60.0}` |
| GET | `/leituras/<id>` | Detalhe de uma leitura |
| GET | `/leituras/<id>/editar` | Formulário de edição |
| PUT | `/leituras/<id>` | Atualiza campos — body JSON |
| DELETE | `/leituras/<id>` | Remove a leitura |
| GET | `/api/estatisticas` | Média, mín e máx (`?desde=2024-01-01&ate=2024-12-31`) |

Todos os endpoints GET aceitam `?formato=json` para retornar JSON em vez de HTML.

### Exemplo de POST (curl)

```bash
curl -X POST http://localhost:5000/leituras \
  -H "Content-Type: application/json" \
  -d '{"temperatura": 27.3, "umidade": 65.0, "pressao": 1013.2}'
```

---

## Formato do JSON enviado pelo Arduino

```json
{"temperatura": 25.5, "umidade": 61.0}
```

Com BMP180:

```json
{"temperatura": 25.5, "umidade": 61.0, "pressao": 1013.2}
```