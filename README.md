# AgroSmart AI Backend

Production-ready FastAPI backend for smart farm management with AI-powered features.

## Stack
- **FastAPI** (async, APIRouter)
- **SQLAlchemy 2.0** (async, DeclarativeBase, Mapped)
- **Pydantic v2** (BaseModel, Field, model_validator)
- **PostgreSQL** (JSONB support)
- **Redis + Celery + Celery Beat** (background tasks, scheduled jobs)
- **PyJWT + Passlib (bcrypt)** (auth, password hashing)
- **OpenAI** (LLM integration)

## Modules
1. **AI Parser** - Natural language → structured farm operations (parse + commit)
2. **AI Assistant** - Intent classification → backend analytics → LLM response (Uzbek)
3. **Analytics** - Cost/profit calculations, trends, inventory summary
4. **Alerts** - Milk drop detection, feed shortage, expiry warnings (Celery Beat 06:00)
5. **Finance** - Income/expense transactions, category breakdown, period-based summary. Analytics revenue/expense now prefer real recorded transactions and fall back to estimates only when none exist.

## Quick Start

```bash
git clone https://github.com/mardonsodikov1-commits/Agrocrm.git
cd Agrocrm

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env faylini yarating
cp .env.example .env  # sozlang: DATABASE_URL, JWT_SECRET_KEY, OPENAI_API_KEY

# PostgreSQL da baza yarating
createdb agrosmart

# Migratsiya (jadval yarash)
uvicorn app.main:app --reload &
# POST /api/v1/auth/register -> user yaratish

# Celery worker va beat (alohida terminal)
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info
```

## API Docs
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| Auth | `POST /api/v1/auth/register` | Ro'yxatdan o'tish |
| Auth | `POST /api/v1/auth/login` | Kirish (JWT) |
| Farms | `POST /api/v1/farms/` | Ferma yaratish |
| Animals | `POST /api/v1/farms/{id}/animals` | Hayvon qo'shish |
| Inventory | `POST /api/v1/farms/{id}/inventory` | Inventar qo'shish |
| Production | `POST /api/v1/farms/{id}/production` | Ishlab chiqarish yozuvi |
| Finance | `POST /api/v1/farms/{id}/finance/transactions` | Daromad/xarajat qo'shish |
| Finance | `GET /api/v1/farms/{id}/finance/summary` | Daromad-xarajat hisoboti |
| AI Parser | `POST /api/v1/ai/entries/parse` | Matnni tahlil qilish |
| AI Parser | `POST /api/v1/ai/entries/{id}/commit` | Tasdiqlash va yozish |
| AI Assistant | `POST /api/v1/ai/assistant/ask` | Savol berish |
| Analytics | `GET /api/v1/farms/{id}/analytics/*` | Analitika ma'lumotlari |
| Alerts | `GET /api/v1/farms/{id}/alerts` | Ogohlantirishlar |

## Environment Variables (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agrosmart
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-64-char-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
OPENAI_API_KEY=sk-...
DEFAULT_CURRENCY=UZS
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
DEBUG=true
```

## Tests
```bash
pip install -r requirements.txt
pytest -q
```

## Project Structure
```
app/
├── core/           # config, security, database, redis, celery
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
├── repositories/   # Data access layer
├── services/       # Business logic
├── ai/             # LLM provider
├── tasks/          # Celery tasks
├── api/v1/         # REST endpoints
└── main.py         # FastAPI app entry
```
