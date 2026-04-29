<div align="center">

# 📡 BetRadar

**Sistema de monitoramento de odds esportivas em tempo real com detecção automática de oportunidades de valor (EV+) e arbitragem (Surebet), com alertas via Telegram.**

[![Java](https://img.shields.io/badge/Java-21-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)](https://www.java.com)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.5-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Lógica de Detecção](#-lógica-de-detecção)
- [Módulo Backend (Spring Boot)](#-módulo-backend-spring-boot)
- [Módulo Scraper (Python)](#-módulo-scraper-python)
- [API REST](#-api-rest)
- [Configuração e Instalação](#-configuração-e-instalação)
- [Variáveis de Ambiente](#️-variáveis-de-ambiente)
- [Testes](#-testes)
- [Alertas Telegram](#-alertas-telegram)

---

## 🎯 Visão Geral

O **BetRadar** é uma plataforma de análise de mercados esportivos de apostas que opera de forma totalmente automatizada. O sistema é composto por dois módulos independentes que se comunicam exclusivamente via **Apache Kafka**:

1. **Backend (Spring Boot)** — Consome odds brutas do Kafka, persiste os dados, detecta oportunidades de mercado (EV+ e Surebet) e dispara alertas em tempo real via Telegram Bot.
2. **Scraper (Python)** — Extrai odds de múltiplas casas de apostas de forma paralela e assíncrona, publicando cada dado no tópico Kafka `raw-odds`. O scraper é ativado pelo próprio usuário via comando do Telegram Bot.

```
Usuário (Telegram Bot) → Scraper Python → Kafka → Backend Spring Boot → Alerta Telegram
```

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUÁRIO (Telegram)                          │
│   /start → informa partida → aguarda alertas de oportunidade    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ python-telegram-bot (polling)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     bot/telegram_bot.py                         │
│  Gerencia estados: IDLE → WAITING_MATCH → SCRAPING → DONE       │
│  Chama scraper_runner.py com o nome da partida informada        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ asyncio / ThreadPoolExecutor
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    scraper/scraper_runner.py                     │
│  Orquestra múltiplos extractors em paralelo (asyncio.gather)    │
│  Normaliza e publica cada odd no Kafka (tópico: raw-odds)       │
└────────┬──────────────┬──────────────┬──────────────┬───────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
  extractors/     extractors/    extractors/    extractors/
  bet365.py       betano.py      pinnacle.py    sportingbet.py
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                           │ JSON padronizado
                           ▼
              ┌─────────────────────────┐
              │       Apache Kafka       │
              │   tópico: raw-odds      │
              │   host: localhost:29092 │
              └────────────┬────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│              Spring Boot Backend              │
│  RawOddsKafkaConsumer → OddProcessorService   │
│  → MarketAnalyzerService (EV+ / Surebet)      │
│  → AlertDispatcherService → TelegramSender    │
└──────────────────────────────────────────────┘
```

### Fluxo Automático Principal

```
Scraper externo
  → publica JSON no Kafka tópico "raw-odds"
  → RawOddsKafkaConsumer.consumeRawOdds()
  → OddProcessorService.processAndStore()
      → normaliza nomes (TeamNormalizationService)
      → upsert Match + Bookmaker + OddHistory no PostgreSQL
      → MarketAnalyzerService.calculateExpectedValue()  [EV_PLUS]
      → MarketAnalyzerService.detectSurebet()           [SUREBET]
  → AlertDispatcherService.dispatchOpportunity()
      → salva Alert no PostgreSQL
      → TelegramNotificationSender.send() → Telegram Bot API → mensagem no chat
```

---

## 🛠️ Stack Tecnológica

### Backend

| Tecnologia | Versão | Função |
|---|---|---|
| Java | 21 | Linguagem principal |
| Spring Boot | 3.5 | Framework base |
| Spring Data JPA | — | Persistência ORM |
| Spring Security + JWT | — | Autenticação e autorização |
| Spring Kafka | — | Consumer do tópico `raw-odds` |
| Spring Data Redis | — | Cache de responses |
| PostgreSQL | 17 | Banco de dados relacional |
| Apache Kafka | 7.4.4 (Confluent) | Mensageria entre scraper e backend |
| Redis | 7 | Cache (TTL 15–30s) |
| MapStruct | 1.5.5 | Mapeamento Domain ↔ Entity ↔ DTO |
| Lombok | — | Redução de boilerplate |
| JJWT | 0.12.6 | Geração e validação de tokens JWT |
| SpringDoc / Swagger UI | 2.8.9 | Documentação interativa da API |
| spring-dotenv | 4.0.0 | Carregamento de `.env` |

### Scraper

| Tecnologia | Versão | Função |
|---|---|---|
| Python | 3.11+ | Linguagem principal |
| kafka-python | 2.3.1 | Producer Kafka |
| Playwright | 1.44.0 | Automação de browsers (SPAs) |
| playwright-stealth | 1.0.6 | Evasão de detecção anti-bot |
| httpx | 0.27.0 | Requests HTTP assíncronos |
| python-telegram-bot | 21.3 | Bot de entrada do usuário |
| python-dotenv | 1.0.1 | Variáveis de ambiente |

### Infraestrutura

| Serviço | Porta | Descrição |
|---|---|---|
| PostgreSQL | 5435 | Banco de dados principal |
| Apache Kafka | 29092 | Broker de mensagens |
| Zookeeper | 22181 | Coordenação do Kafka |
| Kafdrop | 9000 | UI de monitoramento do Kafka |
| Redis | 6379 | Cache em memória |

---

## 📂 Estrutura do Projeto

```
BetRadar/
├── docker-compose.yml          # Infraestrutura: PostgreSQL, Kafka, Redis, Kafdrop
│
├── backend/                    # Módulo Spring Boot (Java 21)
│   ├── pom.xml
│   ├── CONTEXT.md              # Contexto técnico do backend
│   └── src/main/java/com/kau4dev/BetRadar/
│       ├── domain/
│       │   ├── model/          → Alert, Match, OddHistory, Bookmaker, User, TelegramChat (records)
│       │   ├── model/enums/    → AlertType (EV_PLUS, SUREBET), UserRole
│       │   ├── repository/     → Contratos (interfaces puras, sem JPA)
│       │   ├── port/           → NotificationSender (interface)
│       │   └── exception/      → DomainValidationException e subclasses
│       │
│       ├── application/
│       │   ├── service/        → AlertDispatcherService, MarketAnalyzerService,
│       │   │                      OddProcessorService, TelegramChatService, AuthService…
│       │   ├── dto/            → RawOddDTO (entrada do Kafka)
│       │   └── port/out/       → TokenGenerator
│       │
│       ├── infrastructure/
│       │   ├── config/redis/   → RedisCacheConfig (ObjectMapper + JavaTimeModule)
│       │   ├── config/security/→ SecurityConfig, JwtAuthFilter, UserSeedConfig
│       │   ├── config/telegram/→ TelegramProperties, TelegramConfig (bean RestClient)
│       │   ├── entity/         → JPA entities + enums separados
│       │   ├── messaging/      → RawOddsKafkaConsumer (@KafkaListener "raw-odds")
│       │   ├── persistence/    → adapter/, mapper/ (MapStruct), repository/ (JpaRepository)
│       │   └── telegram/       → TelegramNotificationSender (implementa NotificationSender)
│       │
│       └── presentation/
│           ├── controller/     → BetRadarController, AuthController, TelegramChatController
│           ├── request/        → RegisterTelegramChatRequest, LoginRequest, CreateUserRequest
│           ├── response/       → AlertResponse, MatchResponse, TelegramChatResponse…
│           ├── mapper/         → MapStruct presentation mappers
│           └── exception/      → GlobalExceptionHandler
│
└── scraper/                    # Módulo Python 3.11+
    ├── .env
    ├── requirements.txt
    ├── scraper-guide.md        # Blueprint técnico do scraper
    ├── scraper_runner.py       # Orquestrador: asyncio.gather sobre todos os extractors
    │
    ├── bot/
    │   ├── telegram_bot.py     # Entry point (python-telegram-bot, ConversationHandler)
    │   └── states.py           # Enum: IDLE, WAITING_MATCH, SCRAPING, DONE
    │
    ├── extractors/
    │   ├── base_extractor.py   # Classe abstrata com interface padrão
    │   ├── pinnacle.py         # API REST pública (httpx) ✅ Prioridade 1
    │   ├── betano.py           # Playwright + intercepção de API interna
    │   ├── bet365.py           # Playwright + Stealth (Cloudflare)
    │   ├── sportingbet.py      # Playwright (esqueleto)
    │   └── superbet.py         # Playwright (esqueleto)
    │
    ├── kafka/
    │   └── producer.py         # KafkaProducer wrapper com retry (20x, backoff 3s)
    │
    ├── utils/
    │   ├── normalizer.py       # Normalização de nomes de times
    │   ├── match_id.py         # Geração de match_id canônico
    │   └── logger.py           # Logging estruturado
    │
    └── tests/
        ├── test_normalizer.py
        ├── test_bet365.py
        └── test_pinnacle.py
```

---

## 🧮 Lógica de Detecção

### EV+ (Expected Value Positivo)

Detecta odds com valor acima da média do mercado, indicando uma aposta com retorno esperado positivo.

```
Threshold: 5%  →  EV_THRESHOLD = 0.05

Fórmula:
  discrepância = (oddAtual / mediaMercado) - 1

  Se discrepância >= 0.05  →  ALERTA EV+

Regras:
  - A média exclui o próprio bookmaker da comparação
  - Requer mínimo 2 casas de aposta no histórico da partida
  - Avaliado para os 3 resultados: HOME (1), DRAW (X), AWAY (2)
```

**Exemplo de alerta:**
```
🎯 Aposta Recomendada: Casa (1)
🏦 Casa de Aposta: Pinnacle
📈 Odd Encontrada: 2.40
📊 Média do Mercado: 2.00
```

---

### Surebet (Arbitragem)

Detecta quando a soma dos inversos das melhores odds de cada casa é menor que 1, garantindo lucro independente do resultado.

```
Fórmula:
  índiceArbitragem = (1/bestHome) + (1/bestDraw) + (1/bestAway)

  Se índiceArbitragem < 1.0  →  ALERTA SUREBET

  Margem de lucro  = (1 - índiceArbitragem) × 100
  Stake casa       = (1/bestHome) / índiceArbitragem × 100
  Stake empate     = (1/bestDraw) / índiceArbitragem × 100
  Stake fora       = (1/bestAway) / índiceArbitragem × 100
```

**Exemplo de alerta:**
```
🏠 Casa (1): Alocar 38.5% na Bet365 (Odd: 2.50)
🤝 Empate (X): Alocar 26.0% na Betano (Odd: 3.70)
✈️ Fora (2): Alocar 35.5% na Pinnacle (Odd: 4.30)
```

---

## ⚙️ Módulo Backend (Spring Boot)

### Princípios de Arquitetura (DDD)

A regra de ouro é: **dependência aponta sempre para dentro**.

```
presentation → application → domain
infrastructure → domain
domain NUNCA importa Spring, JPA, Kafka ou infrastructure
```

### Casas de Apostas Suportadas

| Casa | Estratégia de Extração | Dificuldade Anti-bot |
|---|---|---|
| **Pinnacle** | API REST pública (`httpx`) | ⚠️ Baixa |
| **Betano** | Playwright + intercepção de API interna | ⚠️⚠️ Média |
| **Bet365** | Playwright + Stealth (Cloudflare) | ⚠️⚠️⚠️ Alta |
| **Sportingbet** | Playwright (em implementação) | ⚠️⚠️ Média |
| **Superbet** | Playwright (em implementação) | ⚠️⚠️ Média |

### Schema Kafka — `raw-odds`

O backend espera o seguinte JSON no tópico `raw-odds`:

```json
{
  "matchId": "qualquer-string",
  "bookmaker": "Pinnacle",
  "teamHome": "Real Madrid",
  "teamAway": "Barcelona",
  "timestamp": "2026-04-23T18:00:00Z",
  "odds": {
    "homeWin": 2.40,
    "draw": 3.10,
    "awayWin": 2.90
  }
}
```

> **Nota:** O scraper usa `snake_case` para os campos (ex: `match_id`, `team_home`). O Jackson com `@JsonProperty` faz o mapeamento para o `RawOddDTO.java` do backend.

### Observações Importantes

- Partidas são criadas **dinamicamente** a partir dos nomes normalizados — sem cadastro prévio.
- Redis requer `JavaTimeModule` + `activateDefaultTyping` para serializar `Instant` e records Java.
- `TelegramNotificationSender` **nunca propaga exceção** — falha silenciosa para não interromper o fluxo.
- `UserSeedConfig` cria o usuário admin no primeiro boot se não existir (idempotente).
- O endpoint `POST /api/v1/alerts` foi **removido** — alertas são 100% automáticos via Kafka.

---

## 🐍 Módulo Scraper (Python)

### Estados do Bot Telegram

```
Usuário entra / reinicia
          │
          ▼
     ┌─────────┐
     │  IDLE   │ ◄─────────────────────────────┐
     └────┬────┘                               │
          │ /start                             │
          ▼                                    │
  ┌────────────────┐                           │
  │ WAITING_MATCH  │                           │
  └───────┬────────┘                           │
          │ Usuário envia "Flamengo x Vasco"   │
          ▼                                    │
  ┌────────────────┐                           │
  │    SCRAPING    │ → scraper_runner.run()    │
  └───────┬────────┘                           │
          │                                    │
   ┌──────┴──────┐                             │
   ▼             ▼                             │
SCRAPING_OK  SCRAPING_FAIL                     │
   │             │                             │
   └──────┬──────┘                             │
          │ /start ou /cancel                  │
          └────────────────────────────────────┘
```

**Comandos disponíveis:**
- `/start` — Inicia o fluxo de monitoramento (qualquer estado volta para `WAITING_MATCH`)
- `/cancel` — Cancela scraping em curso, volta para `IDLE`
- `/status` — Mostra estado atual e última partida consultada

### Geração de `match_id` Canônico

O scraper e o backend geram o mesmo `match_id` usando a mesma lógica de normalização:

```python
# utils/match_id.py
def normalize_team_name(name: str) -> str:
    """Remove acentos, lowercase, substitui espaços por underscore."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ASCII", "ignore").decode("ASCII")
    clean = re.sub(r"[^a-z0-9]", "_", ascii_str.lower())
    return re.sub(r"_+", "_", clean).strip("_")

def build_match_id(team_home: str, team_away: str) -> str:
    return f"{normalize_team_name(team_home)}_v_{normalize_team_name(team_away)}"

# Exemplo: "Flamengo x Vasco da Gama" → "flamengo_v_vasco_da_gama"
```

### Hierarquia de Tratamento de Erros

| Nível | Ação |
|---|---|
| Odd inválida | Loga warning, ignora odd, continua |
| Extractor falha | Loga error, retorna `[]`, continua |
| Kafka indisponível | Retry 20x com backoff 3s, RuntimeError |
| Playwright timeout | `TimeoutError` capturado, retorna `[]` |
| 0 odds publicadas | Bot informa usuário, sugere retry |
| Bot crash | Reinício automático (systemd) |

---

## 🌐 API REST

Todos os endpoints, exceto `/api/v1/auth/login`, **exigem autenticação JWT** via header `Authorization: Bearer <token>`.

| Método | Endpoint | Autenticação | Cache | Descrição |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | ❌ Pública | — | Login, retorna JWT |
| `POST` | `/api/v1/auth/users` | ✅ ADMIN | — | Cria novo usuário |
| `GET` | `/api/v1/auth/users` | ✅ ADMIN | — | Lista todos os usuários |
| `GET` | `/api/v1/opportunities` | ✅ JWT | 15s | Lista oportunidades detectadas |
| `GET` | `/api/v1/matches` | ✅ JWT | 30s | Lista partidas monitoradas |
| `GET` | `/api/v1/matches/{id}/timeline?hours=24` | ✅ JWT | 30s | Histórico de odds de uma partida |
| `POST` | `/api/v1/notifications/telegram/chats` | ✅ ADMIN | — | Registra chat Telegram |
| `GET` | `/api/v1/notifications/telegram/chats` | ✅ ADMIN | — | Lista chats registrados |
| `DELETE` | `/api/v1/notifications/telegram/chats/{id}` | ✅ ADMIN | — | Remove chat Telegram |

> 📖 Documentação interativa disponível em: `http://localhost:8080/swagger-ui.html`

---

## 🚀 Configuração e Instalação

### Pré-requisitos

- Docker e Docker Compose
- Java 21+
- Python 3.11+

### 1. Clonar o repositório

```bash
git clone https://github.com/Kau4dev/Bet-Radar.git
cd BetRadar
```

### 2. Configurar variáveis de ambiente

Crie os arquivos `.env` conforme as seções abaixo.

### 3. Subir a infraestrutura

```bash
docker-compose up -d
```

Isso iniciará: PostgreSQL (5435), Kafka (29092), Zookeeper (22181), Kafdrop (9000) e Redis (6379).

### 4. Iniciar o Backend

```bash
cd backend
.\mvnw.cmd spring-boot:run
```

O backend estará disponível em `http://localhost:8080`.

### 5. Configurar e iniciar o Scraper

```bash
cd scraper
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
python bot/telegram_bot.py
```

---

## 🔐 Variáveis de Ambiente

### Backend — `backend/.env`

```env
# Telegram
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_DEFAULT_CHAT_ID=seu_chat_id_aqui

# Banco de dados
DB_URL=jdbc:postgresql://localhost:5435/betradar
DB_USERNAME=postgres
DB_PASSWORD=postgres

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:29092

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=sua_chave_secreta_minimo_256_bits

# Seed do usuário admin
SEED_ENABLED=true
SEED_USERNAME=admin
SEED_PASSWORD=admin123
```

### Scraper — `scraper/.env`

```env
# Telegram (mesmo token — o scraper usa a API para o ConversationHandler)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# Kafka (mesmo do backend)
KAFKA_BOOTSTRAP_SERVERS=localhost:29092

# Opcional: proxy para Bet365 (IPs residenciais são bloqueados)
# PROXY_URL=http://user:pass@proxy-host:port
```

> ⚠️ **Nunca commite os arquivos `.env` no repositório.** Ambos já estão no `.gitignore`.

---

## 🧪 Testes

### Backend (52 testes unitários)

```bash
cd backend
.\mvnw.cmd test
```

### Scraper

```bash
cd scraper
pytest tests/
```

---

## 📬 Alertas Telegram

O sistema envia dois tipos de alertas diretamente para os chats Telegram registrados:

### EV+ (Expected Value Positivo)
```
🎯 Aposta Recomendada: Casa (1)
🏦 Casa de Aposta: Pinnacle
📈 Odd Encontrada: 2.40
📊 Média do Mercado: 2.00
```

### Surebet (Arbitragem Garantida)
```
🏠 Casa (1): Alocar 38.5% na Bet365 (Odd: 2.50)
🤝 Empate (X): Alocar 26.0% na Betano (Odd: 3.70)
✈️ Fora (2): Alocar 35.5% na Pinnacle (Odd: 4.30)
```

Para registrar um chat Telegram para receber alertas:

```bash
curl -X POST http://localhost:8080/api/v1/notifications/telegram/chats \
  -H "Authorization: Bearer <seu_token_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"chatId": "seu_chat_id"}'
```

---

## 🗺️ Roadmap

- [x] Backend Spring Boot com DDD
- [x] Consumer Kafka e processamento de odds
- [x] Detecção de EV+ e Surebet
- [x] Alertas via Telegram Bot API (sem SDK)
- [x] Autenticação JWT + Spring Security
- [x] Cache Redis
- [x] Documentação Swagger
- [x] 52 testes unitários
- [x] Scraper blueprint (Pinnacle, Betano, Bet365)
- [x] Extractor Sportingbet (Playwright + intercepção de API interna)
- [x] Extractor Superbet (Playwright + REST/GraphQL)
- [x] Validação end-to-end: scraper → Kafka → backend → alerta

### Validação End-to-End

Com o backend e o Kafka rodando, execute o script de validação:

```bash
cd scraper
python e2e_validate.py --match "Flamengo x Vasco" --timeout 30
```

O script publica duas odds sintéticas no Kafka (uma com EV+ intencional), aguarda o backend processar e confirma o alerta via `GET /api/v1/opportunities`. Retorna exit code `0` em sucesso e `1` em falha.

---

<div align="center">

Feito por [Kau4dev](https://github.com/Kau4dev)

</div>
