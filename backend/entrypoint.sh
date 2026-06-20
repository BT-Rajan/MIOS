#!/bin/sh
set -e

echo "🚀 MIOS Container Startup Script"
echo "================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
while ! nc -z db 3306; do
    echo "   Database is unavailable - sleeping..."
    sleep 2
done
echo "✅ Database is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
    echo "   Redis is unavailable - sleeping..."
    sleep 2
done
echo "✅ Redis is ready!"

# Run database migrations
echo "🔧 Running database migrations..."
python -m alembic upgrade head || {
    echo "⚠️  Migration failed or Alembic not configured yet"
    echo "   Continuing with existing schema..."
}

# Seed sample data if database is empty (optional)
if [ "$SEED_DATA" = "true" ]; then
    echo "🌱 Seeding sample data..."
    python -m tests.seed_sample_data || {
        echo "⚠️  Data seeding failed"
        echo "   Continuing without sample data..."
    }
fi

# Create initial admin user if not exists
echo "👤 Ensuring admin user exists..."
python -c "
from core.database import get_db
from api.auth.service import AuthService
from shared.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session

try:
    db = next(get_db())
    repo = UserRepository(db)
    user = repo.get_by_username('admin')
    if not user:
        auth_service = AuthService()
        auth_service.create_admin_user(db, 'admin', 'Admin@MIOS2024!', 'admin@mios.local')
        print('✅ Admin user created (username: admin, password: Admin@MIOS2024!)')
    else:
        print('ℹ️  Admin user already exists')
    db.close()
except Exception as e:
    print(f'⚠️  Could not create admin user: {e}')
" || true

echo ""
echo "✅ MIOS Backend is ready to start!"
echo "=================================="
echo ""

# Start the application based on command
exec "$@"
