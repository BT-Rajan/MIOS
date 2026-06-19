# MIOS - Manufacturing Intelligence Operating System

Enterprise manufacturing platform with strict auditability, traceability, and workflow governance.

## Core Principles

- **Traceable**: Every action creates immutable audit records
- **Auditable**: Complete history of all state changes
- **Conversational**: Command-style interaction support
- **API-First**: All functionality accessible via API
- **Deterministic**: Rules-based logic over AI
- **Privacy-Safe**: No business data leaves system boundary
- **Workflow Governed**: Explicit state machines only
- **Reusable**: Maximum code reuse through shared engines

## Architecture

```
backend/
├── core/              # Core configuration, exceptions, constants
├── shared/            # Reusable engines (audit, workflow, validation, etc.)
│   ├── audit/         # Immutable event logging
│   ├── workflow/      # State machine engine
│   ├── validation/    # Reusable validators
│   ├── permissions/   # RBAC engine
│   ├── notifications/ # Communication engine
│   ├── events/        # Event bus for module communication
│   └── repositories/  # Base repository layer
├── api/               # Domain modules
│   ├── customers/
│   ├── vendors/
│   ├── products/
│   ├── inventory/
│   ├── orders/
│   ├── procurement/
│   ├── production/
│   ├── workers/
│   ├── finance/
│   └── reports/
└── tests/             # Comprehensive test suite
```

## Shared Engines

### Audit Engine
Records all state changes as immutable events.

```python
audit.record_event(
    entity="order",
    entity_id=441,
    action="approved",
    old_state={"status": "pending"},
    new_state={"status": "approved"}
)
```

### Workflow Engine
Enforces explicit state transitions.

```python
workflow.transition(
    entity_type="order",
    current_state="draft",
    target_state="submitted",
    actor_id=user_id
)
```

### Validation Engine
Centralized validators used across all modules.

```python
ValidationEngine.validate_positive_number(amount, "amount")
ValidationEngine.validate_required_field(value, "field")
```

### Permission Engine
RBAC authorization checks.

```python
permission.can(user_id, action="approve_order")
permission.must(user_id, action="delete_inventory")
```

### Event Bus
Inter-module communication through events.

```python
event_bus.publish("order.approved", {"order_id": 441})
event_bus.subscribe("order.approved", handler_function)
```

## Development Setup

```bash
# Clone repository
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run application
uvicorn main:app --reload
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_shared_engines.py -v
```

## Docker

```bash
# Build production image
docker build -t mios-backend --target production .

# Run development container
docker-compose up --build
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Engineering Rules

1. **No business logic in frontend** - Frontend only renders UI
2. **No duplicate logic** - All logic in reusable services
3. **Service classes only** - Business logic in service layer
4. **Audit all state changes** - Every API call creates audit record
5. **Repository pattern** - No direct DB access from services
6. **No external AI** - Company secrets never leave system
7. **Explicit workflows** - State machines only, no implicit transitions
8. **Modular design** - Independent reusable modules
9. **Composition over inheritance** - Prefer composition
10. **File size limit** - Maximum 500 lines per file

## License

Proprietary - All rights reserved
