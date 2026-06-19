# MIOS - Manufacturing Intelligence Operating System

Enterprise-grade factory operating system for complete manufacturing operations management.

## 🏭 System Overview

MIOS is a mission-critical production platform designed to survive 15+ years in manufacturing environments. It enforces strict auditability, traceability, workflow governance, API-first architecture, conversational interaction, privacy-first intelligence, and maximum code reuse.

**This is NOT an ERP** - This is a factory operating system.

## ✨ Core Principles

1. **Traceable** - Every action tracked
2. **Auditable** - Immutable event ledger
3. **Conversational** - Natural language interface
4. **API-First** - Backend services exposed via REST
5. **Deterministic** - Rules over AI
6. **Privacy-Safe** - No business data leaves system
7. **Workflow Governed** - Explicit state machines
8. **Reusable** - Composition over inheritance
9. **Modular** - Independent, swappable components
10. **Secure** - Enterprise-grade security

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                  │
│  Dashboard | Orders | Inventory | Production       │
│  Conversation Panel | Reports                      │
└─────────────────────┬───────────────────────────────┘
                      │ REST API / WebSocket
┌─────────────────────▼───────────────────────────────┐
│                Backend (FastAPI)                    │
│  ┌─────────────────────────────────────────────┐   │
│  │          Shared Engines (Core)              │   │
│  │  Audit | Workflow | Validation | Events     │   │
│  │  Permissions | Rules | Notifications        │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │           Business Modules                  │   │
│  │  Orders | Inventory | Production | Workers  │   │
│  │  Procurement | Finance | Customers | Vendors│   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              Data Layer (MySQL + Redis)             │
│  ACID Transactions | Event Ledger | Cache          │
└─────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
mios/
├── backend/                 # Python FastAPI backend
│   ├── api/                # API routers by module
│   │   ├── orders/
│   │   ├── inventory/
│   │   ├── production/
│   │   ├── customers/
│   │   ├── vendors/
│   │   ├── workers/
│   │   ├── finance/
│   │   └── conversation/
│   ├── core/               # Core configuration
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── constants.py
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic schemas
│   ├── repositories/       # Data access layer
│   ├── services/           # Business logic layer
│   ├── shared/             # Shared engines
│   │   ├── audit/
│   │   ├── workflow/
│   │   ├── validation/
│   │   ├── events/
│   │   ├── permissions/
│   │   └── notifications/
│   └── tests/              # Test suite
│       └── seed_sample_data.py
│
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── api/           # API clients
│   │   ├── components/    # UI components
│   │   ├── features/      # Feature modules
│   │   ├── hooks/         # Custom hooks
│   │   ├── layouts/       # Page layouts
│   │   ├── stores/        # Zustand state
│   │   └── lib/           # Utilities
│   └── public/
│
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container definition
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OR: Python 3.13+, Node.js 18+, MySQL 8+, Redis 7+

### Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Seed sample data
docker-compose exec api python -m tests.seed_sample_data
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/mios
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key-here

# Run migrations (when available)
# alembic upgrade head

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

#### Seed Sample Data

```bash
cd backend
python -m tests.seed_sample_data
```

## 🔧 Technology Stack

### Backend
- **Python 3.13+** - Runtime
- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - ORM
- **MySQL 8** - Database
- **Redis** - Cache & message broker
- **Celery** - Task queue
- **Pytest** - Testing

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Charts

## 📦 Implemented Modules

### Phase 1: Shared Engines ✅
- Audit Engine - Immutable event logging
- Workflow Engine - State machine transitions
- Validation Engine - Reusable validators
- Events Engine - Event bus propagation
- Permissions Engine - RBAC
- Notifications Engine - Communication

### Phase 2: Authentication ✅
- JWT authentication
- User management
- Role-based access control

### Phase 3: Master Data ✅
- Customer management
- Vendor management
- Product catalog
- Bill of Materials (versioned)

### Phase 4: Inventory ✅
- Warehouse management
- Stock levels tracking
- Stock movements
- Reservations

### Phase 5: Orders ✅
- Sales order management
- Workflow states (Draft → Shipped)
- Order items
- Approval workflows

### Phase 6: Procurement ✅
- Purchase requisitions
- Purchase orders
- Vendor management integration

### Phase 7: Production ✅
- Work orders
- Routings
- Resource management
- Production transactions

### Phase 8: Workers ✅
- Worker profiles
- Skills matrix
- Time attendance
- Labor tracking

### Phase 9: Finance ✅
- Costing engine
- General ledger abstraction
- Journal entries
- Financial reporting

### Phase 10: Reporting ✅
- Standard reports
- Ad-hoc queries
- Analytics engine

### Phase 11: Conversation ✅
- Natural language parser
- Command execution
- Context management

## 🔐 Security Features

- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- SQL injection prevention (parameterized queries)
- XSS protection
- CORS configuration
- Rate limiting
- Audit logging of all auth events
- No sensitive data in logs

## 📊 Audit System

Every action creates an immutable record:

```sql
event_ledger:
- id
- correlation_id
- entity_type
- entity_id
- action
- actor_id
- old_state_json
- new_state_json
- reason
- timestamp (immutable)
```

## 💬 Conversational Interface

Natural language commands:

```
"Show delayed orders"
"Show inventory risk"
"Why was order 441 rejected?"
"Show profitability report"
"Approve purchase request 21"
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📈 Monitoring

Health check endpoint:
```bash
curl http://localhost:8000/api/health
```

## 🚢 Deployment

See `DEPLOYMENT.md` for production deployment guide.

### Environment Variables

**Backend:**
```env
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/mios
REDIS_URL=redis://host:6379/0
SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CELERY_BROKER_URL=redis://host:6379/0
```

**Frontend:**
```env
VITE_API_BASE_URL=/api
```

## 📝 API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Follow the standard module template
2. All business logic in service layer
3. Repository pattern for data access
4. No file > 500 lines
5. Functions < 40 lines when practical
6. Type hints everywhere
7. Tests required for new features
8. Document all public methods

## 📄 License

Proprietary - All rights reserved

## 🏢 Support

For enterprise support, contact: support@mios.example.com

---

**Built to last 15+ years in production** 🏭
