# E-commerce Microservices

Um ecossistema de microsserviços para e-commerce robusto e escalável construído sob os princípios da **Clean Architecture**.

O projeto consiste em duas APIs independentes que se comunicam através de chamadas HTTP (com Circuit Breaker e Retries) e eventos assíncronos (Message Broker), garantindo alta disponibilidade e consistência eventual.

## Motivação

Alguns anos atrás, participei de um processo seletivo para uma vaga de desenvolvedor cujo desafio técnico exigia a construção de uma arquitetura de microsserviços. Naquela época, por ainda não possuir a maturidade técnica necessária, não consegui concluir o teste e acabei não passando na vaga. 

Hoje, com a experiência que adquiri ao longo dos anos, decidi revisitar aquele mesmo desafio como um projeto pessoal. O objetivo não é provar nada grandioso, mas simplesmente fechar esse ciclo e construir a solução da forma correta, aplicando conceitos que utilizo no meu dia a dia.

## 🏗 Arquitetura & Tecnologias

O sistema é dividido em dois serviços principais:

### 1. User API
- **Framework**: FastAPI (Python assíncrono)
- **Banco de Dados**: PostgreSQL (via SQLAlchemy assíncrono)
- **Busca Avançada**: Elasticsearch
- **Cache**: Redis
- **Responsabilidades**: Gerenciamento completo de usuários, encriptação reversível (Fernet) de dados sensíveis (CPF, Telefone, E-mail) no banco de dados e indexação de dados para busca.

### 2. Order API
- **Framework**: Flask (Python)
- **Banco de Dados**: MySQL (via Flask-SQLAlchemy)
- **Busca Avançada**: Elasticsearch
- **Cache**: Redis
- **Integração**: Circuit Breaker para consultar a User API
- **Responsabilidades**: Gerenciamento de pedidos de e-commerce, validações de usuário e cálculo de totais.

### Infraestrutura Compartilhada
- **Identity Provider (Keycloak)**: Responsável por centralizar toda a autenticação do ecossistema. Fornece tokens JWT assinados com criptografia assimétrica (RS256) para os clientes e gerencia a comunicação segura (Machine-to-Machine) entre os microsserviços via Client Credentials.
- **Observabilidade (OpenTelemetry)**: Stack completa configurada para rastreamento distribuído e monitoramento.
  - **Grafana**: Visualização e Dashboards.
  - **Prometheus**: Armazenamento de Métricas (TSDB).
  - **Loki**: Agregação de Logs centralizados.
  - **Tempo**: Armazenamento de Traces (Rastreamento distribuído).
  - **OTel Collector**: Receptor central que coleta, processa e exporta a telemetria das APIs.
- **RabbitMQ**: Message Broker utilizado para publicar e consumir eventos assíncronos (ex: `user.created`, `user.updated`).
- **Padrão Cache-Aside**: Ambas as APIs utilizam o Redis extensivamente para aliviar chamadas a banco e a serviços externos. A invalidação do cache inter-serviços é feita via RabbitMQ (ex: se a User API atualiza um usuário, a Order API recebe o evento e invalida seu cache local de forma transparente).
- **ID Generation**: Todos os recursos utilizam UUIDv4 em vez de IDs incrementais para evitar ataques de enumeração e facilitar a geração distribuída.
- **Docker**: Orquestração completa de todos os containers via `docker-compose`.

---

## Como rodar o projeto

Todo o setup foi simplificado através do `Makefile`. Certifique-se de ter o Docker, Docker Compose e o Make instalados na sua máquina.

1. Clone o repositório:
```bash
git clone https://github.com/freitas-dg/cqrs-ecommerce-microservices.git
cd cqrs-ecommerce-microservices
```

2. Execute o setup automatizado (ele fará o build, subirá os containers e executará as migrations dos dois bancos de dados):
```bash
make setup
```

3. Acesse as APIs:
- **RabbitMQ (Painel Admin)**: http://localhost:15672 (user: `ecommercemq`, pass: `ecommerce_mq_2026`)


## Testes
Os testes unitários (cobrem domínio e casos de uso via mocks) podem ser executados com:
```bash
make test
```

## Design Patterns & Boas Práticas
- **Clean Architecture**: Código dividido em Domain, Application, Infrastructure e Presentation.
- **Circuit Breaker & Retry**: A Order API suporta resiliência ao consultar a User API.
- **Criptografia de Dados em Repouso**: Dados sensíveis são encriptados/decriptados automaticamente pelos Repositories.
- **UUIDs**: Evita vazamento de volumetria.

---
Desenvolvido por Douglas Freitas.
