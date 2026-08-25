# Projeto de Portfólio: Simulador de Open Finance Brasil

## O que é o projeto

Este projeto é uma simulação funcional do ecossistema **Open Finance Brasil** — o padrão regulatório que permite compartilhar dados financeiros entre instituições diferentes, com o consentimento explícito e controlado do usuário.

Na prática, é o mesmo mecanismo que permite que um app como Mobills, Guiabolso ou o próprio Nubank mostre, numa única tela, o saldo e as transações de contas que o usuário tem em bancos diferentes — sem que o usuário precise informar login e senha de cada banco no app terceiro.

O projeto simula os **dois lados** dessa relação:

- **Detentor de dados ("Banco")**: sistema que guarda contas, saldos e transações de usuários fictícios, e expõe uma API seguindo o contrato oficial do Open Finance Brasil.
- **Agregador/Iniciador**: aplicação que, mediante consentimento do usuário, consome essa API e apresenta os dados de forma consolidada em um dashboard.

## Para que serve (objetivo do projeto)

O projeto foi criado como peça de portfólio técnico, para aprimorar os conhecimentos em Python e Django, e também como forma de estudar o Open Finance Brasil.

- Modelagem de domínio financeiro (dinheiro, saldos, transações, consentimento)
- Design de API RESTful seguindo um contrato de mercado real e rígido (Open Finance Brasil), não um CRUD genérico
- Implementação de fluxo de autorização (OAuth2) com escopos e expiração
- Cuidado com segurança e privacidade de dados sensíveis
- Testes automatizados cobrindo regras de negócio críticas

## Status de Implementação

### ✅ Concluído

| Componente | Detalhes |
|---|---|
| **Modelos de domínio** | `User`, `Account`, `Balance`, `Transaction`, `Consent` com validações e índices |
| **Migrações** | Aplicadas e funcionando no PostgreSQL via Docker |
| **Admin Django** | Painel configurado com filtros, busca e inline para todos os apps |
| **Seed de dados** | `python manage.py seed_data` — popula banco com dados realistas |
| **Infraestrutura** | Docker Compose com serviços `web` (Django) e `db` (Postgres) |
| **Healthcheck** | `GET /health` → `{ "status": "ok" }` |

### 🔄 Em desenvolvimento

| Componente | Detalhes |
|---|---|
| **Endpoints de API** | Serializers criados; views e rotas a implementar |
| **Fluxo de consentimento** | Lógica de criação, aprovação e revogação via API |
| **Autenticação OAuth2** | Token de acesso com escopos e expiração |
| **Testes automatizados** | pytest-django cobrindo regras de negócio |
| **Frontend** | Dashboard React/TypeScript (fase futura) |

## Funcionalidades principais

1. **Cadastro e login de usuários** (fictícios, para fins de demonstração)
2. **Fluxo de consentimento**: o usuário autoriza explicitamente quais dados (contas, transações) podem ser acessados, e por quanto tempo
3. **Consulta de contas e saldos**, seguindo o formato de dados oficial do padrão
4. **Consulta de extrato de transações**, com paginação padronizada
5. **Revogação de consentimento**: o usuário pode cancelar o acesso a qualquer momento
6. **Dashboard consolidado**: visualização unificada de saldo e transações das contas conectadas

## Tecnologias e linguagens utilizadas

**Backend:**
- **Python** como linguagem principal
- **Django** como framework web
- **Django REST Framework (DRF)**: serializers, autenticação, paginação e permissões
- **PostgreSQL** como banco de dados
- **Docker / Docker Compose** para padronizar o ambiente de desenvolvimento
- **OAuth2** (via django-oauth-toolkit ou implementação simplificada com JWT) para o fluxo de autorização e consentimento
- **drf-spectacular** para gerar documentação Swagger/OpenAPI automaticamente
- **pytest-django** para os testes automatizados

**Frontend:**
- **React** como biblioteca de interface
- **TypeScript** para tipagem estática, incluindo tipagem dos dados retornados pela API
- **Vite** como ferramenta de build/desenvolvimento

**Infraestrutura e entrega:**
- Deploy do backend em serviço com camada gratuita (Railway ou Render)
- Deploy do frontend na Vercel
- CI simples via GitHub Actions, rodando os testes automatizados a cada push
- Repositório público no GitHub, com README documentado, licença MIT e boas práticas de segurança

## Por que segue o padrão Open Finance Brasil

O projeto não inventa um formato de API próprio — ele segue as convenções reais definidas pelo padrão brasileiro, entre elas:

- Estrutura de URI padronizada (`/open-banking/<api>/<versão>/<recurso>`)
- Envelope de resposta padronizado, com blocos `data`, `links` e `meta`
- Formato de erros padronizado
- Convenções de nomenclatura (camelCase, tipos como `AmountString` e `DateTimeString`)
- Paginação padronizada

Isso significa que, tecnicamente, a API construída neste projeto se parece com a API real de uma instituição participante do Open Finance — o que reforça, para quem avaliar o portfólio, que o projeto foi construído com pesquisa real sobre o mercado.

## Como executar

Veja o arquivo [como_rodar.md](./como_rodar.md) para instruções completas de execução com Docker Compose, seed de dados e testes via Insomnia.

```bash
# Início rápido
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data
# Acesse http://localhost:8000/admin
```


Itens mais avançados do padrão real — como mTLS, assinatura de payloads via JWS e certificação FAPI — não são implementados, mas são documentados aqui como requisitos de produção que o autor compreende, ainda que estejam fora do escopo de um projeto de portfólio.