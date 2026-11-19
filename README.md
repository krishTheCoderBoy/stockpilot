# StockPilot

### Smart Inventory & Procurement Operating System

StockPilot is a full-stack inventory and procurement management platform designed to help businesses manage products, warehouses, inventory levels, suppliers, purchase orders, stock movements, and procurement workflows from a single system.

The project is being built with a **modular monolith architecture** initially, with a roadmap toward event-driven architecture, microservices, search, machine-learning-based forecasting, and operational automation.

---

## 🚀 Project Vision

StockPilot aims to provide a reliable operational system for answering questions such as:

- How much stock do we have?
- Where is the stock located?
- How much stock is reserved?
- Which products are running low?
- What inventory is incoming?
- Which suppliers are being used?
- What has been purchased?
- What stock movements occurred?
- Why did the inventory change?
- Which purchase orders are pending?
- What should procurement order next?

The goal is to build the system incrementally while applying real-world software engineering practices.

---

## 🏗️ Architecture

### Phase 1 — Modular Monolith

```text
                    ┌──────────────────────┐
                    │      React Web       │
                    │  TypeScript + Vite   │
                    └──────────┬───────────┘
                               │
                              HTTPS
                               │
                    ┌──────────▼───────────┐
                    │      FastAPI API     │
                    │    REST Endpoints     │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
      ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
      │  Inventory   │   │ Procurement │   │   Products   │
      │   Module     │   │   Module    │   │   Module     │
      └──────────────┘   └─────────────┘   └──────────────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │      PostgreSQL      │
                    └──────────────────────┘
## 💻 Running locally without Docker

Each service is a plain uvicorn app. Copy each service's `.env.example` to `.env` (the same `SECRET_KEY` everywhere; the same `INTERNAL_SERVICE_TOKEN` in auth, inventory and procurement), point `DATABASE_URL` at your own PostgreSQL databases (`auth_db`, `inventory_db`, `procurement_db`), then from each service directory:

```bash
alembic upgrade head                       # auth-service, inventory-service, procurement-service
uvicorn main:app --port 8001               # auth-service
uvicorn app.main:app --port 8002           # inventory-service
uvicorn app.main:app --port 8003           # procurement-service
uvicorn app.main:app --port 8004           # chatbot-service
uvicorn app.main:app --port 8000           # gateway
```

Background processes (inventory-service directory): `python -m app.consumers.purchase_order_receive_consumer`, `python -m app.consumers.notification_consumer`, `python worker.py`, `python scheduler.py`. Auth's email worker (login codes): `python worker.py` from `auth-service`. Frontend: `cd frontend && npm run dev` (set `VITE_API_GATEWAY_BASE_URL=http://localhost:8000` to route everything through the gateway).

**Forecasting needs history.** Planning is only useful with months of daily `ISSUE` movements. For a development database, `python scripts/seed_demand_history.py --confirm` (inventory-service) backfills about six months; it rewrites on-hand quantities, so never run it against real data.

**The assistant needs a model key.** In `services/chatbot-service/.env` set `GROK_API_KEY` (a Groq `gsk_...` or xAI `xai-...` key, recognised by its prefix) or `ANTHROPIC_API_KEY` for Claude; `LLM_PROVIDER` and `LLM_MODEL` override the choice. Without a key the chat window answers that the assistant is not configured; everything else works. Free tiers cap tokens per minute, so a multi-step question can take a while: the service waits and retries when it is rate limited.

## 🐳 Running with Docker (development)

StockPilot is now a set of services behind a gateway (see [docs/architecture.md](docs/architecture.md)). The compose file starts everything for local development: Postgres (three databases), Redis, RabbitMQ, auth / inventory / procurement services, the inventory event consumers, worker and scheduler, the auth email worker, the gateway and the frontend.

```bash
cp .env.example .env        # optional: every value has a development default
docker compose up --build
```

| What | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API gateway | http://localhost:8000 |
| Auth / Inventory / Procurement | http://localhost:8001 / 8002 / 8003 (`/docs` for Swagger) |
| RabbitMQ management | http://localhost:15672 (guest / guest) |

Notes:

- Each service runs `alembic upgrade head` on start, so databases are migrated automatically. The three databases (`auth_db`, `inventory_db`, `procurement_db`) are created by [docker/postgres/init.sql](docker/postgres/init.sql) on the first start of an empty volume. To start from scratch: `docker compose down -v`.
- All three services receive the same `SECRET_KEY` (they verify each other's JWTs locally). Inventory and auth also share `INTERNAL_SERVICE_TOKEN`, used for the internal recipients lookup.
- Source directories are bind-mounted and the Python services run with `--reload`, so edits apply without a rebuild. Rebuild after changing `requirements.txt` or `package.json`.
- Seed data: `docker compose exec auth-service python scripts/seed.py` (likewise for `inventory-service` and `procurement-service`).
- Email (OTP codes, notifications) needs `SMTP_USER` / `SMTP_PASSWORD` in `.env`. Without them the stack runs, but sends fail.
- This setup is for development only. Production images, secrets handling and TLS are Phase 5.


🛠️ Tech Stack
Frontend
React
TypeScript
Vite
Tailwind CSS
React Router
TanStack Query
React Hook Form
Zod
Lucide React
Backend
Python
FastAPI
SQLAlchemy
Alembic
Pydantic
JWT Authentication
Password Hashing
Database
PostgreSQL
Development & DevOps
Git
GitHub
Docker
Docker Compose
GitHub Actions
Planned Technologies
Redis
Background Workers
Kafka / RabbitMQ
OpenSearch / Elasticsearch
Prometheus
Grafana
OpenTelemetry
Kubernetes
Cloud Deployment
Machine Learning
Operational AI
📦 Core Modules
Authentication & Authorization
User authentication
JWT-based authentication
Password hashing
Role-based access control
Roles
Role	Responsibilities
ADMIN	Full system access
INVENTORY_MANAGER	Products, warehouses, inventory and transfers
PROCUREMENT_MANAGER	Suppliers, purchase orders and receiving
Products

Manage:

Product name
SKU
Description
Category
Unit
Reorder point
Safety stock
Active/inactive status
Warehouses

Manage:

Warehouse code
Warehouse name
Address
City
Capacity
Active/inactive status
Inventory

Inventory is maintained per product and warehouse.

Product
   │
   ├── Warehouse A → 120 units
   │
   ├── Warehouse B → 75 units
   │
   └── Warehouse C → 40 units

Inventory tracks:

Quantity
Reserved quantity
Available quantity
Reorder point
Stock status
Available Stock = Quantity - Reserved Quantity
📜 Inventory Movement Ledger

Inventory changes are recorded through an immutable movement ledger.

Supported movement types include:

PURCHASE_RECEIVED
CONSUMED
TRANSFER_IN
TRANSFER_OUT
ADJUSTMENT_IN
ADJUSTMENT_OUT
DAMAGED
RETURNED

Example:

Purchase Received     +100
Transfer Out           -20
Damaged                 -5
                       ----
Current Stock           75

The system should never silently modify inventory without recording the corresponding movement.

This provides:

Auditability
Traceability
Historical inventory information
Easier debugging
Better reporting
🧾 Procurement

StockPilot manages the complete purchase order lifecycle.

DRAFT
  ↓
SUBMITTED
  ↓
APPROVED
  ↓
ORDERED
  ↓
PARTIALLY_RECEIVED
  ↓
RECEIVED
  ↓
CLOSED

Purchase orders contain:

Supplier
Products
Ordered quantity
Received quantity
Unit price
Expected delivery date
Current status
Created by

Business actions are used for state transitions instead of allowing arbitrary status changes.

Example:

POST /purchase-orders/{id}/submit
POST /purchase-orders/{id}/approve
POST /purchase-orders/{id}/receive
🔄 Receiving Workflow

Receiving inventory is handled as a single database transaction.

Purchase Order
      │
      ▼
Receive Goods
      │
      ├───────────────┐
      ▼               ▼
Update Inventory   Create Movement
      │               │
      └───────┬───────┘
              ▼
      Update PO Quantity
              │
              ▼
          COMMIT

If any operation fails, the transaction is rolled back.

This ensures inventory and procurement data remain consistent.

🗄️ Database Model

Initial entities:

users
roles
products
warehouses
inventory
inventory_movements
suppliers
purchase_orders
purchase_order_items

High-level relationships:

Roles
  │
  ▼
Users
  │
  └───────────────┐
                  ▼
          Inventory Movements
                  ▲
                  │
Products ───── Inventory ───── Warehouses
   │
   │
   ▼
Purchase Order Items
   ▲
   │
Purchase Orders
   │
   ▼
Suppliers
📊 Dashboard

The dashboard will provide operational visibility through:

Key Metrics
Total Products
Total Stock
Low Stock Items
Pending Purchase Orders
Additional Information
Inventory by warehouse
Low-stock products
Recent inventory movements
Procurement status
Overdue purchase orders
🖥️ Application Structure
StockPilot
│
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── products/
│   │   │   ├── warehouses/
│   │   │   ├── inventory/
│   │   │   ├── movements/
│   │   │   ├── suppliers/
│   │   │   └── purchase-orders/
│   │   │
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── routes/
│   │   └── lib/
│   │
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── dependencies/
│   │   └── workers/
│   │
│   ├── alembic/
│   └── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── database.md
│   ├── roadmap.md
│   ├── HLD.md
│   ├── LLD.md
│   └── API.md
│
├── tests/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
🐳 Local Development
Prerequisites

Install:

Git
Docker Desktop
Node.js
Python 3.12+
PostgreSQL client (optional)
Clone Repository
git clone https://github.com/krishTheCoderBoy/stockpilot.git
cd stockpilot
Environment Variables

Create a .env file based on:

.env.example

Never commit secrets to Git.

Start the Application
docker compose up --build

The application will start the required services.

🧪 Testing

Backend tests:

pytest

Frontend tests:

npm test

Important business rules to test:

Authentication
RBAC
Product validation
Inventory constraints
No negative inventory
Inventory movement creation
Purchase order state transitions
Receiving workflow
Role restrictions
🔀 Git Workflow

StockPilot follows a simple feature-branch workflow.

main
 │
 ├── feature/project-foundation
 ├── feature/auth
 ├── feature/products
 ├── feature/inventory
 └── feature/procurement

Development workflow:

Issue
  ↓
Todo
  ↓
In Progress
  ↓
Review
  ↓
Testing
  ↓
Done

Typical Git workflow:

Issue
  ↓
Feature Branch
  ↓
Development
  ↓
Testing
  ↓
Commit
  ↓
Push
  ↓
Pull Request
  ↓
Review
  ↓
Merge
📈 Development Roadmap
Phase 1 — Core Platform
 Repository setup
 GitHub Project setup
 Docker + PostgreSQL
 SQLAlchemy configuration
 Alembic migrations
 Authentication
 RBAC
 Products
 Warehouses
 Inventory
 Inventory movement ledger
 Suppliers
 Purchase orders
 Receiving workflow
 Dashboard
 Testing
 Production hardening
Phase 2 — Production Foundation

Planned:

Redis
Background workers
Caching
Rate limiting
Scheduled jobs
Notifications
Phase 3 — Event-Driven Architecture

Introduce domain events such as:

PurchaseOrderCreated
PurchaseOrderApproved
PurchaseOrderReceived
InventoryUpdated
InventoryTransferred
StockLow

Potential architecture:

                 ┌───────────────┐
                 │ Procurement   │
                 └───────┬───────┘
                         │
                         ▼
                  Message Broker
                 Kafka / RabbitMQ
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Inventory      Analytics      Notification
Phase 4 — Microservices

Potential services:

API Gateway
     │
     ├── Auth Service
     ├── Inventory Service
     ├── Procurement Service
     ├── Notification Service
     └── Analytics Service

Services will only be extracted when there is a clear operational or architectural reason.

Phase 5 — Search

Introduce a dedicated search engine for:

Products
Suppliers
Warehouses
Purchase Orders
Inventory movements

Potential technologies:

OpenSearch
Elasticsearch
Phase 6 — Procurement Intelligence

Use historical operational data for:

Demand forecasting
Stockout prediction
Reorder recommendations
Supplier lead-time analysis
Procurement planning

Example:

Available Stock       = 42
Incoming Stock        = 20
Safety Stock          = 30
Forecast Demand       = 160

Recommended Order ≈ 148

Recommendations will include an explanation of the factors used.

Phase 7 — Operational AI

A future conversational interface may allow users to ask questions such as:

"Which products may stock out next week?"

"Why is PO-1042 still pending?"

"Show me low-stock products across all warehouses."

"Which supplier has the longest lead time?"

The chatbot will interact with existing application APIs and business services rather than directly modifying the database.

🔐 Security

Security considerations include:

JWT authentication
Password hashing
Role-based authorization
Input validation
Database constraints
Protected API endpoints
Environment-based secrets
CORS configuration
Rate limiting
Audit logging

Secrets must never be committed to the repository.

🎯 Engineering Goals

StockPilot is being developed to demonstrate practical knowledge of:

Full-stack development
REST API design
Database design
Transaction management
Authentication & authorization
Business workflows
Modular architecture
Testing
Git/GitHub workflows
Docker
CI/CD
System design
Event-driven architecture
Search systems
Machine learning integration
Cloud deployment

The focus is on building the system incrementally rather than introducing complex infrastructure before it is necessary.

📚 Documentation

Project documentation will be maintained in:

docs/
├── architecture.md
├── database.md
├── roadmap.md
├── HLD.md
├── LLD.md
└── API.md
📌 Current Status

Current phase: Phase 1 — Foundation

Current focus: Development infrastructure

Repository
    ↓
GitHub Project
    ↓
Issue Tracking
    ↓
Docker + PostgreSQL
    ↓
Backend Foundation
    ↓
Authentication
    ↓
Core Inventory
    ↓
Procurement
👨‍💻 Development

StockPilot is being developed as a solo engineering project with an emphasis on clean architecture, maintainability, testing, and progressive system evolution.