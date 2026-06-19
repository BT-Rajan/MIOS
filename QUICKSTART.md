# MIOS Quick Start Guide

## 🚀 Deploy in 3 Commands

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Access the application
# Frontend: http://localhost
# API Docs: http://localhost/api/docs
```

## 📋 Default Credentials

After first startup, login with:
- **Username:** `admin`
- **Password:** `Admin@MIOS2024!`

⚠️ **Change this password immediately in production!**

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌──────────────┐
│   Nginx     │────▶│   React      │
│   (Port 80) │     │   Frontend   │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   FastAPI   │────▶│   MySQL 8    │
│   Backend   │     │   Database   │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Celery    │────▶│   Redis 7    │
│   Workers   │     │   Cache/Broker│
└─────────────┘     └──────────────┘
```

## 📦 What's Included

### Backend (FastAPI + Python 3.13)
- ✅ Authentication & Authorization (JWT + RBAC)
- ✅ Customer Management
- ✅ Vendor Management
- ✅ Product & BOM Management
- ✅ Inventory Control (Multi-warehouse)
- ✅ Sales Orders with Workflow
- ✅ Procurement & Purchase Orders
- ✅ Production Planning (Work Orders, Routings)
- ✅ Worker Management & Time Tracking
- ✅ Finance & Costing Engine
- ✅ Reporting Engine
- ✅ Conversation Interface (Natural Language)
- ✅ Audit Trail (Immutable Ledger)
- ✅ Event Bus (Domain Events)

### Frontend (React + TypeScript + Tailwind)
- ✅ Modern SPA with Vite
- ✅ Dashboard with KPIs
- ✅ Order Management UI
- ✅ Conversation Panel
- ✅ Responsive Design
- ✅ Type-safe API Integration

### Infrastructure
- ✅ Docker Compose Orchestration
- ✅ MySQL 8.0 with Persistence
- ✅ Redis 7.0 for Caching & Queue
- ✅ Nginx Reverse Proxy
- ✅ Celery Workers (Async Tasks)
- ✅ Health Checks
- ✅ Security Headers
- ✅ Rate Limiting

## 🔧 Configuration

Edit `.env` file to customize:

```bash
# Database
MYSQL_PASSWORD=your_secure_password

# Security
SECRET_KEY=your-32-char-secret-key

# Feature Flags
FEATURE_CONVERSATION_UI=True
FEATURE_ADVANCED_REPORTING=True
```

## 📊 Sample Data

To load demo data for testing:

```bash
# In docker-compose.yml, add environment variable:
# SEED_DATA=true

# Or run manually:
docker-compose exec backend python -m tests.seed_sample_data
```

This creates:
- 3 Warehouses
- 5 Customers
- 4 Vendors
- 18 Products (3 finished goods + 15 components)
- Sample Orders (Completed, In Progress, Delayed)
- Production Work Orders
- Employee Records

## 🔍 Testing the System

### 1. Health Check
```bash
curl http://localhost/api/health
```

### 2. API Documentation
Open: http://localhost/api/docs

### 3. Try Conversation Interface
In the frontend, type:
- "Show delayed orders"
- "What is our inventory value?"
- "List pending purchase orders"
- "Show profitability report"

### 4. Test Workflow
1. Create a new Sales Order (Draft)
2. Submit for approval
3. Approve the order
4. Check inventory reservation
5. Create Production Work Order
6. Complete production
7. Ship the order

## 🛠️ Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
cd backend
pytest -v
```

## 📁 Project Structure

```
/workspace
├── backend/
│   ├── api/              # Business modules
│   │   ├── auth/
│   │   ├── customers/
│   │   ├── vendors/
│   │   ├── products/
│   │   ├── inventory/
│   │   ├── orders/
│   │   ├── procurement/
│   │   ├── production/
│   │   ├── workers/
│   │   ├── finance/
│   │   └── reports/
│   ├── core/             # Core framework
│   ├── shared/           # Shared engines
│   │   ├── audit/
│   │   ├── workflow/
│   │   ├── validation/
│   │   ├── permissions/
│   │   └── events/
│   └── tests/            # Tests & seed data
├── frontend/
│   ├── src/
│   │   ├── api/          # API clients
│   │   ├── components/   # Reusable UI
│   │   ├── features/     # Feature modules
│   │   ├── layouts/      # Page layouts
│   │   ├── lib/          # Utilities
│   │   └── stores/       # State management
│   └── public/
├── docker-compose.yml
├── nginx.conf
├── .env.example
└── README.md
```

## 🔐 Security Features

- ✅ JWT Authentication with refresh tokens
- ✅ Role-Based Access Control (RBAC)
- ✅ Password hashing (bcrypt)
- ✅ SQL Injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (Security headers)
- ✅ CSRF protection
- ✅ Rate limiting (60 req/min)
- ✅ Input validation (Pydantic)
- ✅ Audit logging (all actions)
- ✅ No sensitive data to external AI

## 📈 Monitoring

### Logs
```bash
# View all logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Database Access
```bash
docker-compose exec db mysql -u mios_user -p mios
```

### Redis CLI
```bash
docker-compose exec redis redis-cli
```

## 🚨 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs backend

# Restart services
docker-compose down
docker-compose up --build
```

### Database connection failed
```bash
# Wait for health checks (30-60 seconds)
# Check database status
docker-compose ps
```

### Port already in use
Edit `docker-compose.yml` and change port mappings:
```yaml
ports:
  - "8080:80"  # Change 80 to 8080
```

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review API docs: http://localhost/api/docs
3. Verify environment: `docker-compose config`

---

**Built with enterprise principles for 15+ year maintainability**

✓ Traceable ✓ Auditable ✓ Conversational ✓ API-first
✓ Deterministic ✓ Privacy-safe ✓ Workflow governed
✓ Modular ✓ Secure ✓ Maintainable
