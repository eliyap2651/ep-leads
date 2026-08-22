# REST API - סקירה

תיעוד אינטראקטיבי מלא (Swagger UI, נוצר אוטומטית מהקוד) זמין תמיד ב-
`http://<backend-host>/docs` כשהשרת רץ, ותיעוד ReDoc ב-`/redoc`.

כל ה-endpoints תחת `/api` ודורשים `Authorization: Bearer <access_token>`
אלא אם צוין אחרת.

## Auth
- `POST /api/auth/login` - התחברות, מחזיר access+refresh tokens
- `POST /api/auth/refresh` - חידוש access token
- `GET /api/auth/me` - פרטי המשתמש המחובר
- `POST /api/auth/change-password`
- `POST /api/auth/users` (Admin) - יצירת משתמש
- `GET /api/auth/users` (Admin)

## Leads
- `GET /api/leads` - רשימה + פילטרים (q, domain, region, record_type, status, tier, min_score, max_score, min_value, has_contact, deadline_before, assigned_to_id)
- `GET /api/leads/{id}`
- `PATCH /api/leads/{id}` - עדכון (סטטוס, הקצאה וכו')
- `DELETE /api/leads/{id}` (Manager/Admin)
- `POST /api/leads/{id}/notes` , `GET /api/leads/{id}/notes`
- `POST /api/leads/{id}/activities` , `GET /api/leads/{id}/activities`
- `POST /api/leads/{id}/ai-assistant` - "מה לעשות עכשיו?"

## Tenders / Projects / Companies / Contacts
- `GET /api/tenders?is_open=&closing_before=`
- `GET /api/projects?stage=`
- `GET /api/companies`
- `GET /api/contacts`, `GET /api/contacts/lead/{lead_id}`

## Sources & Search
- `GET/POST /api/sources`, `PATCH/DELETE /api/sources/{id}` (Manager/Admin)
- `GET/POST/DELETE /api/search-queries` (Manager/Admin)
- `POST /api/search/run` (Manager/Admin) - מפעיל סבב סריקה+חיפוש מיידי

## Alerts / Tasks
- `GET /api/alerts?unread_only=`, `POST /api/alerts/{id}/read`
- `GET /api/tasks`, `POST /api/tasks`, `POST /api/tasks/{id}/complete`

## Analytics
- `GET /api/analytics/dashboard`
- `GET /api/analytics/by-day|by-domain|by-region|by-score|by-status`
- `GET /api/analytics/tenders-closing`
- `GET /api/analytics/top-opportunities`
- `GET /api/analytics/daily-brief`

## Export / Import
- `GET /api/export/leads.csv|leads.xlsx?domain=&region=&tier=&min_score=`
- `POST /api/import/leads` (Manager/Admin, multipart file)

## Admin
- `GET /api/admin/health`, `GET /api/admin/scan-runs`

## Settings
- `GET/PUT /api/settings` (Admin)
