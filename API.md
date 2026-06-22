# AgroSmart AI — API Reference (Frontend uchun)

Bu hujjat frontend dasturchilar uchun. Barcha endpointlar, request/response namunalari shu yerda.

## Asosiy ma'lumotlar

- **Base URL:** `http://localhost:8000` (lokal) yoki productionda sizning domeningiz
- **API prefiks:** barcha endpointlar `/api/v1` bilan boshlanadi (auth ham)
- **Format:** barcha request/response — `application/json`
- **Interaktiv hujjat:** server ishlaganda `GET /docs` (Swagger) va `GET /openapi.json` (mashina o'qiydigan spec — Postman/typed-client generatsiya uchun)
- **Sana/vaqt:** ISO 8601 (masalan `2026-06-19T10:00:00Z`)
- **ID:** barcha id'lar UUID (string)
- **Pul:** `Numeric` — JSON'da string sifatida keladi (masalan `"2520000.00"`), aniqlik yo'qolmasligi uchun

## Autentifikatsiya (JWT)

1. `POST /api/v1/auth/register` → foydalanuvchi yaratasiz
2. `POST /api/v1/auth/login` → `access_token` (60 daqiqa) + `refresh_token` (7 kun) olasiz
3. Himoyalangan endpointlarga har bir so'rovda header qo'shasiz:

```
Authorization: Bearer <access_token>
```

4. Token eskirganda `POST /api/v1/auth/refresh` orqali yangilaysiz.

## Xato formati

Barcha xatolar shu ko'rinishda:

```json
{ "detail": "Xato haqida xabar" }
```

Kutilmagan server xatosi (500):

```json
{ "detail": "Kutilmagan xatolik yuz berdi...", "error_type": "..." }
```

Asosiy status kodlar: `200` OK, `201` yaratildi, `204` o'chirildi (body yo'q), `400` noto'g'ri so'rov, `401` autentifikatsiya yo'q/noto'g'ri, `403` ruxsat yo'q, `404` topilmadi, `409` allaqachon mavjud, `422` validatsiya xatosi, `429` so'rovlar chegarasi.

---

# 1. Auth — `/api/v1/auth`

### POST `/register`
Auth talab qilinmaydi.
```json
// request
{ "phone": "+998901234567", "full_name": "Ism Familiya", "password": "Parol123", "role": "owner" }
// role: owner | worker | admin  (default: owner)
// parol: kamida 8 belgi, katta + kichik harf + raqam
// response 201
{ "id": "uuid", "phone": "+998901234567", "full_name": "Ism Familiya", "role": "owner", "is_active": true }
```

### POST `/login`
```json
// request
{ "phone": "+998901234567", "password": "Parol123" }
// response 200
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

### POST `/refresh`
```json
// request
{ "refresh_token": "eyJ..." }
// response 200 — yangi access + refresh token
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

### POST `/change-password` 🔒
```json
// request
{ "old_password": "Eski123", "new_password": "Yangi123" }
// response 200
{ "message": "Parol muvaffaqiyatli o'zgartirildi." }
```

🔒 = `Authorization: Bearer` header kerak (quyidagilarning hammasi).

---

# 2. Farms — `/api/v1/farms` 🔒

### POST `` (ferma yaratish)
```json
// request
{ "name": "Mening Fermam", "region": "Toshkent", "district": "Zangiota" }
// response 201
{ "id": "uuid", "owner_id": "uuid", "name": "Mening Fermam", "region": "Toshkent",
  "district": "Zangiota", "is_active": true, "created_at": "...", "updated_at": null }
```

### GET `` (fermalar ro'yxati)
Query: `skip` (default 0), `limit` (default 100, max 500)
```json
// response 200
{ "total": 1, "items": [ { /* FarmResponse */ } ] }
```

### GET `/{farm_id}` (ferma tafsiloti)
```json
// response 200
{ "id": "uuid", "owner_id": "uuid", "name": "...", "region": "...", "district": "...",
  "is_active": true, "created_at": "...", "updated_at": null,
  "members": [ { "id": "uuid", "farm_id": "uuid", "user_id": "uuid", "role": "worker",
                 "permissions": {}, "created_at": "..." } ],
  "animal_count": 0, "group_count": 0, "inventory_count": 0 }
```

### PUT `/{farm_id}` (faqat owner/admin)
```json
{ "name": "Yangi nom", "region": "...", "district": "..." }   // barchasi ixtiyoriy
```

### DELETE `/{farm_id}` (faqat owner/admin) → `204`

### POST `/{farm_id}/members` (a'zo qo'shish, owner/admin)
```json
// request
{ "user_id": "uuid", "role": "worker", "permissions": {} }
// role: owner | manager | worker
// response 201 — FarmMemberResponse
```

### GET `/{farm_id}/members` → `[FarmMemberResponse]`

### DELETE `/{farm_id}/members/{member_user_id}` → `204`

---

# 3. Animals — `/api/v1/farms/{farm_id}/animals` 🔒

Yakka hayvonlar (sigir, buqa, ot va h.k.).

### POST `` (hayvon qo'shish)
```json
// request
{ "type": "cow", "name": "3-sigir", "tag_number": "UZ-001", "gender": "female",
  "breed": "Golshtin", "birth_date": "2022-04-01", "purchase_price": "8000000",
  "current_weight": "450" }
// gender: male | female  (majburiy)
// type, name majburiy; qolganlari ixtiyoriy
// response 201 — AnimalResponse (status: "active" default)
```

### GET `` (ro'yxat)
Query: `status` (active|sold|dead|slaughtered), `skip`, `limit`
```json
// response 200 — [AnimalResponse]
```

### GET `/{animal_id}` → `AnimalResponse`

### PUT `/{animal_id}`
```json
{ "name": "...", "tag_number": "...", "breed": "...", "current_weight": "460",
  "status": "sold" }   // barchasi ixtiyoriy; status: active|sold|dead|slaughtered
```

### DELETE `/{animal_id}` → `204`

**AnimalResponse:**
```json
{ "id": "uuid", "farm_id": "uuid", "type": "cow", "name": "3-sigir", "tag_number": "UZ-001",
  "gender": "female", "breed": "Golshtin", "birth_date": "2022-04-01",
  "purchase_price": "8000000.00", "current_weight": "450.00", "status": "active",
  "created_at": "...", "updated_at": null }
```

---

# 4. Animal Groups — `/api/v1/farms/{farm_id}/groups` 🔒

Guruhli hayvonlar (parranda, qo'y guruhi, broyler).

### POST ``
```json
{ "type": "broiler", "name": "1-partiya broyler", "initial_count": 500,
  "current_count": 495, "average_weight": "1.8" }
```

### GET `` (query: `status`, `skip`, `limit`) → `[AnimalGroupResponse]`
### GET `/{group_id}` → `AnimalGroupResponse`
### PUT `/{group_id}` → `{ name?, current_count?, average_weight?, status? }`
### DELETE `/{group_id}` → `204`

---

# 5. Inventory — `/api/v1/farms/{farm_id}/inventory` 🔒

Yem, dori, vaksina, mahsulot zaxirasi.

### POST `` (element qo'shish)
```json
// request
{ "name": "Kombikorm", "category": "feed", "unit": "kg", "current_quantity": "1000",
  "average_cost": "3500", "expiry_date": "2026-12-31" }
// category: feed | medicine | vaccine | product  (majburiy)
// average_cost, expiry_date ixtiyoriy
// response 201 — InventoryItemResponse
```

### GET `` (query: `category`, `skip`, `limit`) → `[InventoryItemResponse]`
### GET `/{item_id}` → `InventoryItemResponse`
### PUT `/{item_id}` → barcha maydonlar ixtiyoriy
### DELETE `/{item_id}` → `204`

### POST `/consume` (zaxiradan chiqim)
```json
// request
{ "item_id": "uuid", "quantity": "50", "notes": "kunlik yemlash" }
// response 200 — yangilangan InventoryItemResponse
// quantity zaxiradan ko'p bo'lsa → 400 xato
```

---

# 6. Production — `/api/v1/farms/{farm_id}/production` 🔒

Sut, tuxum, vazn o'sishi, go'sht yozuvlari.

### POST ``
```json
// request
{ "animal_id": "uuid", "group_id": null, "type": "milk", "quantity": "18",
  "unit": "liter", "notes": null, "recorded_at": "2026-06-19T08:00:00Z" }
// type: milk | egg | weight_gain | meat
// unit: liter | kg | piece | gram
// animal_id YOKI group_id (ikkalasi ham ixtiyoriy)
// response 201 — ProductionRecordResponse
```

### GET `` (query: `type`, `animal_id`, `group_id`, `skip`, `limit`) → `[ProductionRecordResponse]`
### GET `/{record_id}` → `ProductionRecordResponse`
### DELETE `/{record_id}` → `204`

---

# 7. Finance — `/api/v1/farms/{farm_id}/finance` 🔒

Daromad va xarajatlar.

### POST `/transactions`
```json
// request
{ "type": "income", "category": "milk_sale", "amount": "2520000",
  "currency": "UZS", "description": "Sut sotildi", "animal_id": null,
  "group_id": null, "recorded_at": "2026-06-19T10:00:00Z" }
// type: income | expense  (majburiy)
// income kategoriyalari: milk_sale, egg_sale, meat_sale, animal_sale, other_income
// expense kategoriyalari: feed, medicine, vaccine, salary, transport, utilities, equipment, other_expense
// currency ixtiyoriy (default: UZS)
// response 201 — FinanceTransactionResponse
```

### GET `/transactions`
Query: `type` (income|expense), `category`, `date_from`, `date_to`, `skip`, `limit`
```json
// response 200 — [FinanceTransactionResponse]
```

### GET `/transactions/{transaction_id}` → `FinanceTransactionResponse`
### DELETE `/transactions/{transaction_id}` → `204`

### GET `/summary` (daromad-xarajat hisoboti)
Query: `time_period` (today|this_week|this_month|this_year, default this_month) **yoki** aniq `date_from` + `date_to`
```json
// response 200
{ "farm_id": "uuid", "period": "this_month", "date_from": "...", "date_to": "...",
  "total_income": 2520000.0, "total_expense": 1740000.0, "net_profit": 780000.0,
  "currency": "UZS",
  "income_by_category": [ { "category": "milk_sale", "total": 2520000.0, "count": 1 } ],
  "expense_by_category": [ { "category": "feed", "total": 1740000.0, "count": 1 } ] }
```

---

# 8. AI Parser — `/api/v1/ai/entries` 🔒

Tabiiy matnni strukturalangan operatsiyalarga ajratadi. **Ikki bosqich: parse → commit** (avval preview, keyin tasdiqlash).
> Rate limit: foydalanuvchiga daqiqasiga 30 so'rov (oshsa `429`).

### POST `/parse`
```json
// request
{ "text": "Bugun 3-sigir 18 litr sut berdi, 2 qop yem ketdi", "farm_id": "uuid" }
// farm_id ixtiyoriy (AI'ga ferma konteksti beradi)
// response 200
{ "entry_id": "uuid",
  "operations": [ { "operation_type": "production", "record_type": "milk",
                    "quantity": 18, "unit": "liter", "animal_id": null, "notes": null } ],
  "warnings": [ "..." ] }
// operation_type: production | consumption | purchase | expense
```

### POST `/{entry_id}/commit` (tasdiqlash va DBga yozish)
```json
// request — foydalanuvchi tasdiqlagan/tahrirlagan operatsiyalar
{ "operations": [
  { "operation_type": "production", "record_type": "milk", "quantity": 18, "unit": "liter" }
] }
// response 200
{ "success": true, "committed_count": 1, "errors": [] }
```

> ⚠️ AI to'g'ridan-to'g'ri DBga yozmaydi. Avval `/parse`, foydalanuvchi ko'rib tasdiqlaydi, keyin `/commit`.
> OpenAI kaliti o'rnatilmagan bo'lsa, `/parse` bo'sh operations + ogohlantirish qaytaradi (xato bermaydi).

---

# 9. AI Assistant — `/api/v1/ai/assistant` 🔒

Fermer savol beradi, AI o'z bazasidagi data asosida javob beradi.
> Rate limit: daqiqasiga 30 so'rov.

### POST `/ask`
```json
// request
{ "question": "Bu oy qaysi sigirim eng foydali?", "farm_id": "uuid" }
// response 200
{ "intent": "profit_by_animal",
  "answer": "Bu oy eng foydali sigir... (o'zbek tilida tushuntirish)",
  "data": { /* hisoblangan raqamli ma'lumot */ } }
// intent variantlari: profit_by_animal, milk_cost_per_liter, egg_cost_per_unit,
//   feed_remaining_days, production_trend, total_expenses, total_revenue,
//   animal_performance, inventory_summary, general_question
```

---

# 10. Analytics — `/api/v1/farms/{farm_id}/analytics` 🔒

Hammasi `GET`. Hisoblangan raqamlarni qaytaradi (frontendda grafik/dashboard uchun).

| Endpoint | Query | Tavsif |
|----------|-------|--------|
| `/profit-by-animal` | `animal_type` | Hayvon bo'yicha foyda → `{ "data": [...] }` |
| `/milk-cost-per-liter` | — | 1 litr sut tannarxi |
| `/egg-cost-per-unit` | — | 1 dona tuxum tannarxi |
| `/feed-remaining-days` | — | Yem necha kunga yetadi |
| `/production-trend` | `animal_type`, `time_period` | Ishlab chiqarish dinamikasi |
| `/revenue` | `time_period` | Daromad (real finance data'dan) |
| `/expenses` | `time_period` | Xarajat |
| `/animal-performance` | `animal_type` | Hayvonlar samaradorligi → `{ "data": [...] }` |
| `/inventory-summary` | — | Zaxira holati (kam qolgan, muddati tugayotgan) |
| `/daily-metrics` | — | Kunlik umumiy ko'rsatkichlar |

`time_period` qiymatlari: `today`, `yesterday`, `this_week`, `this_month` (default), `this_year`.

---

# 11. Alerts — `/api/v1/farms/{farm_id}/alerts` 🔒

Ogohlantirishlar (sut kamayishi, yem tugashi, muddati tugashi). Celery backgroundda yaratadi.

### GET ``
Query: `is_read` (bool), `severity`, `type`, `skip`, `limit`
```json
// response 200
{ "total": 2, "items": [
  { "id": "uuid", "farm_id": "uuid", "type": "milk_drop", "severity": "warning",
    "title": "...", "message": "...", "details": "...", "is_read": false,
    "created_at": "...", "resolved_at": null } ] }
```

### GET `/{alert_id}` → `AlertResponse`
### PUT `/{alert_id}` → `{ "is_read": true }`
### POST `/{alert_id}/read` (o'qilgan deb belgilash) → `AlertResponse`
### POST `/read-all` → `{ "updated": <son> }`
### DELETE `/{alert_id}` → `204`

---

# Health check (auth shart emas)

### GET `/health`
```json
{ "status": "healthy", "version": "1.0.0", "project": "AgroSmart AI Backend" }
```

---

## Frontend uchun maslahatlar

- **Typed client:** `GET /openapi.json` ni oling → `openapi-typescript` yoki `orval` bilan TypeScript turlarini avtomatik generatsiya qiling. Qo'lda yozish shart emas.
- **Postman/Insomnia:** `openapi.json` ni import qiling — barcha endpointlar tayyor bo'ladi.
- **Token saqlash:** `access_token` ni memory/secure storage'da saqlang; `refresh_token` bilan jim yangilab turing.
- **Pul maydonlari** string keladi — `parseFloat` yoki `Decimal` kutubxonasi bilan ishlang.
- **Ko'p endpoint `farm_id` ga bog'liq** — foydalanuvchi tanlagan fermani global state'da saqlang.
