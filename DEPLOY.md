# Railway'ga Deploy qilish (qadam-baqadam)

AgroSmart backendni Railway'ga joylash. Doimiy URL beradi (ngrok kerak emas).

## Kerakli narsalar
- GitHub akkaunt (repo: `Toshmirzayev-Inomjon/Agrocrm`)
- Railway akkaunt: https://railway.app (GitHub bilan kiring)

---

## 1-qadam: Loyiha yaratish
1. https://railway.app → **New Project**
2. **Deploy from GitHub repo** → `Toshmirzayev-Inomjon/Agrocrm` ni tanlang
3. Railway avtomatik `railway.json`ni o'qib, `uvicorn`ni ishga tushiradi.

## 2-qadam: PostgreSQL qo'shish
1. Loyiha ichida **+ New** → **Database** → **Add PostgreSQL**
2. Railway avtomatik `DATABASE_URL` o'zgaruvchisini yaratadi.

## 3-qadam: Redis qo'shish
1. **+ New** → **Database** → **Add Redis**
2. Avtomatik `REDIS_URL` yaratiladi.

## 4-qadam: Backend xizmatiga o'zgaruvchilarni ulash
Backend (web) xizmatini oching → **Variables** → quyidagilarni qo'shing:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
JWT_SECRET_KEY=<64-belgili-tasodifiy-maxfiy-kalit>
DEFAULT_CURRENCY=UZS
DEBUG=false
OPENAI_API_KEY=<ixtiyoriy: AI uchun sk-... kaliti>
```

> `${{Postgres.DATABASE_URL}}` — Railway'ning reference sintaksisi; Postgres URL'ini avtomatik ulaydi.
> `JWT_SECRET_KEY` uchun: `openssl rand -hex 32` buyrug'i bilan kalit yarating.
> Kod `postgresql://` ni avtomatik `postgresql+asyncpg://` ga o'giradi — qo'shimcha sozlash shart emas.

## 5-qadam: Domen olish (bepul)
1. Web xizmat → **Settings** → **Networking** → **Generate Domain**
2. `https://agrocrm-production-xxxx.up.railway.app` kabi **doimiy** URL beriladi.

## 6-qadam: Tekshirish
Brauzerda oching:
- `https://<sizning-domeningiz>/health` → `{"status":"healthy",...}`
- `https://<sizning-domeningiz>/docs` → Swagger
- `https://<sizning-domeningiz>/openapi.json` → spec

Jadvallar startda avtomatik yaratiladi (`init_db`), migratsiya shart emas.

---

## (Ixtiyoriy) Celery — fon vazifalari uchun
Avtomatik hisob-kitob va alertlar (kunlik metrika 02:00, alertlar 06:00) ishlashi uchun **2 ta qo'shimcha xizmat** yarating (xuddi shu repodan):

1. **Worker xizmati:** Settings → Start Command:
   `celery -A app.core.celery_app worker --loglevel=info`
2. **Beat xizmati:** Settings → Start Command:
   `celery -A app.core.celery_app beat --loglevel=info`

Ikkalasiga ham 4-qadamdagi o'zgaruvchilarni ulang.

> Faqat API kerak bo'lsa (frontend test uchun), Celery'siz ham backend to'liq ishlaydi.

---

## Frontendchiga beriladigan (deploy'dan keyin)
- **Base URL:** `https://<sizning-railway-domeningiz>`  ← doimiy, o'zgarmaydi
- **Spec:** `https://<domen>/openapi.json`
- **Auth:** `/api/v1/auth/register` → `/api/v1/auth/login` → `Authorization: Bearer <token>`
- ngrok header **kerak emas** (bu ngrok emas, haqiqiy domen)
