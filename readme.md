# Projeto de Portfólio: Simulador de Open Finance Brasil

## O que é o projeto

Este projeto é uma simulação funcional do ecossistema **Open Finance Brasil** — o padrão regulatório que permite compartilhar dados financeiros entre instituições diferentes, com o consentimento explícito e controlado do usuário.

Na prática, é o mesmo mecanismo que permite que um app como Mobills, Guiabolso ou o próprio Nubank mostre, numa única tela, o saldo e as transações de contas que o usuário tem em bancos diferentes — sem que o usuário precise informar login e senha de cada banco no app terceiro.

O projeto simula os **dois lados** dessa relação:

- **Detentor de dados ("Banco")**: sistema que guarda contas, saldos e transações de usuários fictícios, e expõe uma API seguindo o contrato oficial do Open Finance Brasil.
- **Agregador/Iniciador**: aplicação que, mediante consentimento do usuário, consome essa API e apresenta os dados de forma consolidada em um dashboard.

## Para que serve (objetivo do projeto)

O projeto foi criado como peça de portfólio técnico, para aprimorar as conhecimentos em Pyhton e Django, e também como forma de estudar o Open Finance Brasil.

- Modelagem de domínio financeiro (dinheiro, saldos, transações, consentimento)
- Design de API RESTful seguindo um contrato de mercado real e rígido (Open Finance Brasil), não um CRUD genérico
- Implementação de fluxo de autorização (OAuth2) com escopos e expiração
- Cuidado com segurança e privacidade de dados sensíveis
- Testes automatizados cobrindo regras de negócio críticas

## Funcionalidades principais

1. **Cadastro e login de usuários** (fictícios, para fins de demonstração)
2. **Fluxo de consentimento**: o usuário autoriza explicitamente quais dados (contas, transações) podem ser acessados, e por quanto tempo
3. **Consulta de contas e saldos**, seguindo o formato de dados oficial do padrão
4. **Consulta de extrato de transações**, com paginação padronizada
5. **Revogação de consentimento**: o usuário pode cancelar o acesso a qualquer momento, cortando o acesso do agregador imediatamente
6. **Dashboard consolidado**: visualização unificada de saldo e transações das contas conectadas

## Tecnologias e linguagens utilizadas

**Backend:**
- **Python** como linguagem principal
- **Django** como framework web
- **Django REST Framework (DRF)**: camada usada para construir a API REST — serializers, autenticação, paginação e permissões
- **PostgreSQL** como banco de dados
- **Docker / Docker Compose** para padronizar o ambiente de desenvolvimento
- **OAuth2** (via django-oauth-toolkit ou implementação simplificada com JWT) para o fluxo de autorização e consentimento
- **drf-spectacular** para gerar documentação Swagger/OpenAPI automaticamente
- **pytest-django** para os testes automatizados

**Frontend:**
- **React** como biblioteca de interface
- **TypeScript** para tipagem estática, incluindo tipagem dos dados retornados pela API (os DTOs seguem exatamente o contrato de dados do Open Finance Brasil)
- **Vite** como ferramenta de build/desenvolvimento

**Infraestrutura e entrega:**
- Deploy do backend em serviço com camada gratuita (Railway ou Render)
- Deploy do frontend na Vercel
- CI simples via GitHub Actions, rodando os testes automatizados a cada push
- Repositório público no GitHub, com README documentado, licença MIT e boas práticas de segurança (segredos fora do versionamento, dados fictícios)

## Por que segue o padrão Open Finance Brasil

O projeto não inventa um formato de API próprio — ele segue as convenções reais definidas pelo padrão brasileiro, entre elas:

- Estrutura de URI padronizada (`/open-banking/<api>/<versão>/<recurso>`)
- Envelope de resposta padronizado, com blocos `data`, `links` e `meta`
- Formato de erros padronizado
- Convenções de nomenclatura (camelCase, tipos como `AmountString` e `DateTimeString`)
- Paginação padronizada

Isso significa que, tecnicamente, a API construída neste projeto se parece com a API real de uma instituição participante do Open Finance — o que reforça, para quem avaliar o portfólio, que o projeto foi construído com pesquisa real sobre o mercado, e não apenas como um exercício acadêmico genérico.

## Escopo e prazo

O projeto foi planejado para ser concluído em **uma semana**, com escopo intencionalmente enxuto: um único "banco" simulado (em vez de vários), fluxo de consentimento completo e funcional, três telas essenciais no frontend (login, consentimento e dashboard) e testes automatizados concentrados nas regras de negócio mais sensíveis (consentimento e acesso a dados).

Itens mais avançados do padrão real — como mTLS, assinatura de payloads via JWS e certificação FAPI — não são implementados, mas são documentados no README como requisitos de produção que o autor do projeto compreende, ainda que estejam fora do escopo de um projeto de portfólio.