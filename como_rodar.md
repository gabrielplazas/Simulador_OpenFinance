# Como Rodar o Simulador de Open Finance

Este documento explica os passos e comandos necessários para executar o projeto localmente, tanto utilizando **Docker Compose** (ambiente recomendado) quanto executando **localmente na máquina**.

---

## 🚀 Como Rodar via Docker Compose (Recomendado)

O projeto está configurado para rodar a aplicação Django e o banco PostgreSQL isoladamente em containers.

### Pré-requisitos
* **Docker** e **Docker Compose** (ou Docker Desktop) instalados e em execução.

### Passos para Inicializar

1. **Subir os containers em background (Detached):**
   ```bash
   docker compose up --build -d
   ```
   *Compila a imagem da aplicação Django (`web`) e sobe o Postgres (`db`).*

2. **Aplicar as Migrações:**
   ```bash
   # Gerar arquivos de migração (caso haja alterações em modelos)
   docker compose exec web python manage.py makemigrations

   # Aplicar migrações no banco de dados
   docker compose exec web python manage.py migrate
   ```

3. **Popular o Banco com Dados de Teste (Seed):**
   ```bash
   docker compose exec web python manage.py seed_data
   ```
   Cria automaticamente 4 usuários, ~5 contas, ~10 consentimentos e ~80 transações realistas.

   Para limpar tudo e popular novamente do zero:
   ```bash
   docker compose exec web python manage.py seed_data --clear
   ```

   **Usuários criados pelo seed:**

   | Usuário | Senha |
   |---|---|
   | `ana.silva` | `Senha@123` |
   | `carlos.souza` | `Senha@123` |
   | `mariana.lima` | `Senha@123` |
   | `pedro.costa` | `Senha@123` |

4. **Criar um Superusuário (Admin):**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
   Acesso ao painel: `http://localhost:8000/admin`

   Para remover um admin depois:
   ```bash
   docker compose exec web python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='NOME_DO_ADMIN').delete()"
   ```

5. **Validar o Funcionamento (Healthcheck):**
   ```bash
   curl http://localhost:8000/health
   ```
   **Resposta esperada (Status 200 OK):**
   ```json
   { "status": "ok" }
   ```

6. **Parar a Execução:**
   ```bash
   docker compose down
   ```

---

## 🧪 Testando a API (Insomnia / curl)

### Configuração básica no Insomnia

1. Crie um **Environment** com a variável `base_url = http://localhost:8000`
2. Em cada requisição, configure **Auth → Basic Auth**:
   - **Username:** `Gabriel_Admin`
   - **Password:** sua senha de admin
3. Header obrigatório: `Content-Type: application/json`

---

### Endpoints disponíveis

#### Healthcheck

| Método | URL | Descrição |
|---|---|---|
| `GET` | `{{base_url}}/health` | Verifica se o servidor está no ar |

**Resposta:**
```json
{ "status": "ok" }
```

---

#### Consentimentos *(endpoints a implementar — contrato já definido)*

Os serializers estão implementados. As views e rotas ainda serão criadas. Quando prontas, os contratos serão:

**`POST /open-banking/consents/v1/consents`** — Criar consentimento
```json
// Request body
{
  "permissions": ["ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ"],
  "expirationDays": 90
}
```
```json
// Response 201 Created
{
  "consentId": "urn:banco:consent:uuid",
  "status": "AWAITING_AUTHORISATION",
  "permissions": ["ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ"],
  "creationDateTime": "2026-08-25T20:00:00Z",
  "expirationDateTime": "2026-11-23T20:00:00Z",
  "statusUpdateDateTime": "2026-08-25T20:00:00Z"
}
```

**Escopos válidos para `permissions`:**

| Escopo | Descrição |
|---|---|
| `ACCOUNTS_READ` | Leitura de dados da conta |
| `ACCOUNTS_BALANCES_READ` | Leitura de saldo |
| `ACCOUNTS_TRANSACTIONS_READ` | Leitura de transações |
| `ACCOUNTS_OVERDRAFT_LIMITS_READ` | Leitura de limite de cheque especial |
| `CUSTOMERS_PERSONAL_IDENTIFICATIONS_READ` | Dados cadastrais pessoais |
| `CUSTOMERS_PERSONAL_ADITTIONAL_INFO_READ` | Dados cadastrais adicionais |
| `CUSTOMERS_BUSINESS_IDENTIFICATIONS_READ` | Dados cadastrais PJ |
| `CUSTOMERS_BUSINESS_ADITTIONAL_INFO_READ` | Dados cadastrais adicionais PJ |

**`GET /open-banking/consents/v1/consents/{consentId}`** — Consultar consentimento

> Enquanto as views não estão prontas, navegue pelos consentimentos em: `http://localhost:8000/admin/consents/consent/`

---

## 💻 Como Rodar Localmente (Sem Docker)

Se preferir rodar o Django diretamente no host (ex: para debugging com breakpoints):

### 1. Inicializar e Ativar o Ambiente Virtual
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
* **Linux/macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 2. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
```bash
cp .env.example .env
```

> ⚠️ **Atenção ao Host do Banco de Dados:**
> O `.env.example` vem com `@db:5432` (hostname do container Docker).
> Ao rodar o Django fora do Docker, mantenha o Postgres rodando via container
> (`docker compose up -d db`) e altere o host para `localhost` no `.env`:
> ```env
> DATABASE_URL=postgres://postgres:postgres@localhost:5432/openfinance
> ```
> Ou passe inline no PowerShell antes de rodar:
> ```powershell
> $env:DATABASE_URL="postgres://postgres:postgres@localhost:5432/openfinance"
> ```

### 4. Executar Migrações e Iniciar o Servidor
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data   # popular dados de teste
python manage.py runserver
```
Aplicação disponível em `http://localhost:8000/`.

---

## 📂 Estrutura de Apps do Projeto

```
apps/
├── core/           # Infraestrutura, utilitários e management commands
│   └── management/
│       └── commands/
│           └── seed_data.py   # Comando para popular dados de teste
├── accounts/       # Contas bancárias e saldos
├── transactions/   # Extrato e transações financeiras
└── consents/       # Fluxo de consentimento Open Finance
```

### Comandos úteis de desenvolvimento

```bash
# Ver logs da aplicação em tempo real
docker compose logs -f web

# Acessar o shell do Django (REPL interativo com ORM)
docker compose exec web python manage.py shell

# Acessar o banco de dados diretamente
docker compose exec db psql -U postgres -d openfinance

# Verificar migrations pendentes
docker compose exec web python manage.py showmigrations
```
