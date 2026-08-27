# Como Rodar o Simulador de Open Finance

Este documento explica os passos e comandos necessários para executar o projeto, rodar a suíte de testes automatizados e testar os endpoints da API via **Docker Compose** ou diretamente na máquina.

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
   *Compila a imagem da aplicação Django (`web`) e inicializa o PostgreSQL (`db`).*

2. **Aplicar as Migrações:**
   ```bash
   docker compose exec web python manage.py migrate
   ```

3. **Popular o Banco com Dados de Teste (Seed):**
   ```bash
   docker compose exec web python manage.py seed_data
   ```
   Cria automaticamente 4 usuários, contas bancárias, consentimentos e dezenas de transações realistas.

   *Para resetar o banco e popular novamente do zero:*
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
   Painel administrativo disponível em: `http://localhost:8000/admin`

5. **Validar o Funcionamento (Healthcheck):**
   ```bash
   curl http://localhost:8000/health
   ```
   *Resposta esperada:* `{ "status": "ok" }`

6. **Parar a Execução:**
   ```bash
   docker compose down
   ```

---

## 🧪 Executando os Testes Automatizados

O projeto utiliza **`pytest-django`** para testar regras de negócio, ciclo de vida do consentimento e proteções de autorização.

### Rodar no Docker:
```bash
docker compose exec web pytest
```

### Rodar localmente (no venv):
```bash
pytest
```

---

## 📡 Testando os Endpoints da API (Insomnia / Postman / cURL)

### Configuração Básica
* **Base URL:** `http://localhost:8000`
* **Autenticação:** Basic Auth (ex: usuário `ana.silva` e senha `Senha@123`)
* **Headers Padrão:**
  * `Content-Type: application/json`

---

### 1. Módulo de Consentimentos

#### A. Criar Consentimento
* **`POST /open-banking/consents/v1/consents/`**
* **Payload:**
  ```json
  {
    "permissions": [
      "ACCOUNTS_READ",
      "ACCOUNTS_BALANCES_READ",
      "ACCOUNTS_TRANSACTIONS_READ"
    ],
    "expirationDays": 90
  }
  ```
* **Resposta (201 Created):**
  ```json
  {
    "data": {
      "consentId": "c4b1d5a8-2041-47ec-a4dc-86e5898bc57d",
      "status": "AWAITING_AUTHORISATION",
      "permissions": [
        "ACCOUNTS_READ",
        "ACCOUNTS_BALANCES_READ",
        "ACCOUNTS_TRANSACTIONS_READ"
      ],
      "creationDateTime": "2026-08-27T14:30:00Z",
      "expirationDateTime": "2026-11-25T14:30:00Z",
      "statusUpdateDateTime": "2026-08-27T14:30:00Z"
    }
  }
  ```

#### B. Autorizar Consentimento
* **`PATCH /open-banking/consents/v1/consents/{consentId}/`**
* **Payload:**
  ```json
  {
    "status": "AUTHORISED"
  }
  ```

#### C. Consultar Consentimento
* **`GET /open-banking/consents/v1/consents/{consentId}/`**

#### D. Revogar Consentimento
* **`DELETE /open-banking/consents/v1/consents/{consentId}/`**
* **Resposta:** `204 No Content`

---

### 2. Módulo de Contas e Saldos (Protegido por Consentimento)

> ⚠️ **Importante:** Todos os endpoints de contas e transações **exigem** o cabeçalho HTTP:
> `X-Consent-Id: <UUID_DO_CONSENTIMENTO_AUTORIZADO>`

#### A. Listar Contas
* **`GET /open-banking/accounts/v1/accounts/`**
* **Header:** `X-Consent-Id: c4b1d5a8-2041-47ec-a4dc-86e5898bc57d`
* **Escopo Exigido:** `ACCOUNTS_READ`
* **Resposta (200 OK):**
  ```json
  {
    "data": [
      {
        "accountId": "a1b2c3d4-0000-0000-0000-000000000001",
        "brandName": "Banco Itaú S.A.",
        "companyCnpj": "60701190000104",
        "type": "CONTA_DEPOSITO_A_VISTA",
        "subtype": "INDIVIDUAL",
        "number": "54321",
        "branchCode": "0001",
        "checkDigit": "7",
        "currency": "BRL"
      }
    ],
    "links": { "self": "..." },
    "meta": { "totalRecords": 1, "totalPages": 1 }
  }
  ```

#### B. Detalhar Conta
* **`GET /open-banking/accounts/v1/accounts/{accountId}/`**
* **Header:** `X-Consent-Id: <UUID_DO_CONSENTIMENTO>`
* **Escopo Exigido:** `ACCOUNTS_READ`

#### C. Consultar Saldo
* **`GET /open-banking/accounts/v1/accounts/{accountId}/balances/`**
* **Header:** `X-Consent-Id: <UUID_DO_CONSENTIMENTO>`
* **Escopo Exigido:** `ACCOUNTS_BALANCES_READ`
* **Resposta (200 OK):**
  ```json
  {
    "data": {
      "availableAmount": "15420.50",
      "blockedAmount": "0.00",
      "automaticallyInvestedAmount": "2500.00",
      "currency": "BRL",
      "updateDateTime": "2026-08-27T10:00:00Z"
    }
  }
  ```

---

### 3. Módulo de Extrato e Transações (Protegido por Consentimento)

#### A. Consultar Extrato da Conta
* **`GET /open-banking/accounts/v1/accounts/{accountId}/transactions/`**
* **Header:** `X-Consent-Id: <UUID_DO_CONSENTIMENTO>`
* **Escopo Exigido:** `ACCOUNTS_TRANSACTIONS_READ`
* **Parâmetros Opcionais de Query:**
  * `?fromDate=2026-01-01&toDate=2026-08-27&page=1&page-size=25`
* **Resposta (200 OK):**
  ```json
  {
    "data": [
      {
        "transactionId": "f9e8d7c6-1111-2222-3333-444455556666",
        "amount": "250.00",
        "currency": "BRL",
        "creditDebitType": "DEBITO",
        "transactionStatus": "LANCADO",
        "transactionDate": "2026-08-25",
        "transactionDateTime": "2026-08-25T14:30:00Z",
        "transactionType": "PIX",
        "description": "Transferência enviada via PIX",
        "payeeCnpjCpf": "12345678901",
        "payeeName": "João Ferreira"
      }
    ],
    "links": { "self": "..." },
    "meta": { "totalRecords": 18, "totalPages": 1 }
  }
  ```

---

## 💻 Como Rodar Localmente (Sem Docker)

Se preferir rodar o Django diretamente no host:

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

### 3. Configurar o `.env` e Iniciar o Banco
```bash
cp .env.example .env
# Certifique-se de que o host aponta para localhost no DATABASE_URL
docker compose up -d db
```

### 4. Executar Migrações, Seed e Servidor
```bash
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

---

## 📡 Documentação OpenAPI 3.0 (Swagger)

O projeto inclui documentação interativa da API com Swagger UI:

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **Schema OpenAPI:** http://localhost:8000/api/schema/

### Autenticação no Swagger

A documentação suporta duas formas de autenticação:

#### 1. Basic Auth (Recomendado para testes rápidos)
1. Clique no botão **Authorize** (🔒) no topo da página Swagger
2. Selecione **basicAuth**
3. Insira:
   - **Username:** 
   - **Password:** 
4. Clique em **Authorize** → **Close**

#### 2. Session Auth via cookie (mais próximo do real)
1. Faça login na API:
   - Vá para 
   - Clique em **Try
