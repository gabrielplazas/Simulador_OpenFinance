# Como Rodar o Simulador de Open Finance

Este documento explica os passos e comandos necessários para executar o projeto localmente, tanto utilizando **Docker Compose** (ambiente recomendado) quanto executando **localmente na máquina**.

---

## 🚀 Como Rodar via Docker Compose (Recomendado)

O projeto está configurado para rodar a aplicação Django e o banco PostgreSQL isoladamente em containers.

### Pré-requisitos
* Certifique-se de que o **Docker** e o **Docker Compose** (ou Docker Desktop) estão instalados e em execução em sua máquina.

### Passos para Inicializar

1. **Subir os containers em background (Detached):**
   ```bash
   docker compose up --build -d
   ```
   *Este comando compilará a imagem da aplicação Django (`web`) e baixará a imagem oficial do Postgres (`db`), inicializando ambos os serviços.*

2. **Executar as Migrações Iniciais:**
   Para criar as tabelas e a estrutura inicial no banco de dados Postgres:
   ```bash
   docker compose exec web python manage.py migrate
   ```

3. **Criar um Superusuário (Admin):**
   Caso precise acessar o painel de administração do Django (`http://localhost:8000/admin`):
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

4. **Validar o Funcionamento (Healthcheck):**
   Envie uma requisição HTTP GET para testar o endpoint de saúde:
   ```bash
   curl http://localhost:8000/health
   ```
   **Resposta Esperada (Status 200 OK):**
   ```json
   {
     "status": "ok"
   }
   ```

5. **Parar a Execução:**
   Para desligar os containers mantendo os dados persistidos no banco de dados local:
   ```bash
   docker compose down
   ```

---

## 💻 Como Rodar Localmente (Sem Docker)

Se preferir rodar a aplicação diretamente no seu host (por exemplo, para debugging local):

### 1. Inicializar e Ativar o Ambiente Virtual
* No Windows (PowerShell):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
* No Linux/macOS (Terminal):
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 2. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
Copie o arquivo de exemplo e edite as credenciais caso utilize uma conexão de banco local diferente:
```bash
cp .env.example .env
```

### 4. Executar Migrações e Inicializar o Servidor local
```bash
python manage.py migrate
python manage.py runserver
```
A aplicação local estará disponível em `http://localhost:8000/`.

---

## 📂 Estrutura de Apps do Projeto
O projeto está organizado com uma estrutura modular sob o diretório `apps/`:
* **`apps/core/`**: Lógica de infraestrutura e utilitários compartilhados (como o endpoint `/health`).
* **`apps/accounts/`**: Gerenciamento de contas e saldos.
* **`apps/transactions/`**: Gerenciamento de extrato e transações financeiras.
* **`apps/consents/`**: Fluxo e registro de consentimentos do Open Finance.
