# Projeto de Portfólio: Simulador de Open Finance Brasil

## O que é o projeto

Este projeto é uma simulação funcional do ecossistema **Open Finance Brasil** — o padrão regulatório mantido pelo Banco Central do Brasil que permite o compartilhamento seguro de dados financeiros entre instituições, mediante o consentimento explícito e controlado do usuário.

Na prática, é o mesmo mecanismo que permite que aplicativos agregadores e bancos apresentem saldos e extratos de contas de múltiplas instituições em uma interface única — sem expor credenciais bancárias do usuário.

O projeto implementa a arquitetura e os contratos oficiais do Open Finance:

- **Detentor de dados ("Banco Transmissor")**: sistema que gerencia contas, saldos e transações, expondo APIs RESTful protegidas pelo ciclo de vida de consentimento e escopos granulares.
- **Camada de Autorização e Governança**: controle de acesso via *Permission Classes* especializadas (`HasValidConsent`) baseadas em cabeçalhos HTTP padronizados (`X-Consent-Id`).

---

## Para que serve (Objetivo do Projeto)

O projeto foi construído como peça de **portfólio técnico avançado**, demonstrando:

- **Modelagem de Domínio Financeiro**: entidades de contas, saldos contábeis/bloqueados/aplicados, extratos, transações de débito/crédito e ciclo de vida de consentimento.
- **Design de API Corporativa**: contratos rígidos do Open Finance Brasil (envelopes de resposta `{ "data": ... }`, paginação padronizada com `links`/`meta`, `camelCase` explícito nos serializers e tratamento de erros padronizado).
- **Autorização Baseada em Consentimento (*Consent Binding*)**: mecanismo de segurança que vincula o acesso aos dados bancários a consentimentos ativos, não expirados e com escopos autorizados (`ACCOUNTS_READ`, `ACCOUNTS_BALANCES_READ`, `ACCOUNTS_TRANSACTIONS_READ`).
- **Testes Automatizados de Ponta a Ponta**: suíte de testes com `pytest-django` simulando o ciclo de vida completo do consentimento e cenários de proteção de acesso.

---

## Status de Implementação

### ✅ Concluído

| Componente | Detalhes |
|---|---|
| **Modelos de Domínio** | `User`, `Account`, `Balance`, `Transaction`, `Consent` com validações, regras de integridade e índices |
| **API de Consentimentos** | Criação (`POST`), Consulta (`GET`), Autorização (`PATCH`), Revogação (`DELETE`) e Listagem Paginada (`/open-banking/consents/v1/consents/`) |
| **API de Contas e Saldos** | Listagem de contas (`/accounts/`), Detalhes (`/accounts/{id}/`) e Saldos (`/accounts/{id}/balances/`) protegidos por escopo |
| **API de Extrato e Transações** | Extrato paginado (`/accounts/{id}/transactions/`) com filtros de período (`fromDate`, `toDate`) e proteção por escopo |
| **Camada de Autorização (`HasValidConsent`)** | Validação de cabeçalho `X-Consent-Id`, posse do usuário, vigência (`is_valid`) e escopos necessários com retorno 403 padronizado |
| **Testes Automatizados** | Suíte `pytest-django` cobrindo o fluxo completo de consentimento, acesso a dados e casos de borda |
| **Infraestrutura & Docker** | Docker Compose com serviços `web` (Django) e `db` (PostgreSQL 15) |
| **Seed de Dados** | `python manage.py seed_data` populando usuários, contas, saldos, consentimentos e dezenas de transações |
| **Admin Django** | Painel administrativo completo configurado com filtros e inlines |

### 🔄 Próximas Etapas Planejadas

| Componente | Detalhes |
|---|---|
| **Swagger / OpenAPI 3.0** | Documentação interativa via `drf-spectacular` |
| **Dashboard Frontend** | Interface SPA em React + TypeScript para consumo do agregador |
| **Iniciação de Pagamentos Pix** | Simulação da Fase 3 do Open Finance (ITP) |

---

## Decisões Arquiteturais e Padrões Adotados

### 1. Por que o ID do Consentimento via Header (`X-Consent-Id`)?
* **Semântica RESTful:** As URLs dos recursos identificam as entidades de negócio (ex: `/open-banking/accounts/v1/accounts/{accountId}/balances`). Misturar IDs de consentimento nas rotas poluiria a identificação dos recursos.
* **Contexto de Autorização:** O consentimento atua como credencial/metadado de autorização da requisição. O protocolo HTTP reserva os *Headers* exatamente para metadados de autorização e rastreabilidade.

### 2. Validação de Escopos Granulares
Cada endpoint declara seu escopo regulatório exigido:
* `GET /open-banking/accounts/v1/accounts/` → `ACCOUNTS_READ`
* `GET /open-banking/accounts/v1/accounts/{id}/balances/` → `ACCOUNTS_BALANCES_READ`
* `GET /open-banking/accounts/v1/accounts/{id}/transactions/` → `ACCOUNTS_TRANSACTIONS_READ`

Se a requisição for feita com um consentimento sem o escopo correspondente, a API rejeita com HTTP 403 (`INSUFFICIENT_PERMISSIONS`).

### 3. Envelope Padronizado e Formato de Erros
* **Sucesso (Item Único):** `{ "data": { ... } }`
* **Sucesso (Lista Paginada):** `{ "data": [...], "links": { ... }, "meta": { "totalRecords": N, "totalPages": N } }`
* **Erro Regulatório:**
  ```json
  {
    "errors": [
      {
        "code": "CONSENT_REVOKED",
        "title": "Consentimento revogado",
        "detail": "O consentimento informado foi revogado pelo usuário."
      }
    ]
  }
  ```

### 4. Escopo do Portfólio vs. Produção Bancária
Requisitos de infraestrutura corporativa de produção — como autenticação mútua por certificados digitais (**mTLS** padrão ICP-Brasil), assinatura de mensagens via **JWS** e certificação **FAPI Conformance Suite** — são requisitos de mercado corporativo que exigem PKI comercial e estão fora do escopo de execução local/gratuita de um portfólio. O projeto foca em reproduzir fielmente as **regras de negócio, modelos de dados, contratos de API e lógica de autorização**.

---

## Tecnologias Utilizadas

- **Linguagem:** Python 3.11+
- **Framework Web:** Django 5.0 + Django REST Framework 3.15
- **Banco de Dados:** PostgreSQL 15
- **Containerização:** Docker & Docker Compose
- **Testes Automatizados:** pytest & pytest-django
- **Ambiente:** django-environ

---

## Como Executar

Consulte o guia detalhado em [como_rodar.md](./como_rodar.md).

```bash
# Início rápido via Docker
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data

# Executar a suíte de testes automatizados
docker compose exec web pytest
```