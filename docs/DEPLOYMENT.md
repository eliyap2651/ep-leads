# פריסה לסביבת Production

## אפשרות מומלצת למתחילים: VPS + Docker Compose

מתאים ל-DigitalOcean / Hetzner / AWS Lightsail / Linode וכל ספק VPS אחר.

1. **הקמת שרת**: Ubuntu 22.04+, לפחות 2 vCPU / 4GB RAM (יעד ראשוני; ראו סעיף
   Performance במפרט לצמיחה עתידית ל-100K+ לידים).
2. **התקנת Docker**:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```
3. **שיבוט הקוד לשרת** (git clone / scp את תיקיית `ep-leads`).
4. **הגדרת `.env`**: `cp .env.example .env` ומלאו ערכים אמיתיים - **לעולם אל
   תשתמשו בסיסמאות/מפתחות לדוגמה בפרודקשן**.
5. **דומיין + HTTPS**: הציבו reverse proxy (Nginx / Caddy / Traefik) מול
   `backend` (פורט 8000) ו-`frontend` (פורט 5173/80), עם תעודת TLS חינמית
   דרך Let's Encrypt (Caddy עושה זאת אוטומטית). דוגמת Caddyfile מינימלית:
   ```
   app.your-domain.co.il {
       reverse_proxy /api/* backend:8000
       reverse_proxy frontend:80
   }
   ```
6. **הרצה**:
   ```bash
   docker compose up --build -d
   ```
7. **בדיקת בריאות**: `curl https://app.your-domain.co.il/api/../health` דרך
   הפרוקסי, ומסך "ניטור מערכת" (Admin) בתוך האפליקציה.

לאחר שהדומיין פעיל עם HTTPS - האפליקציה נגישה מכל מחשב/אייפון בעולם, ואפשר
"להוסיף למסך הבית" באייפון להתקנה כמו אפליקציה (PWA).

## אפשרויות נוספות

- **Railway / Render**: תומכים ב-Docker Compose-like שירותים (Postgres,
  Redis, Web Service, Background Worker, Cron Job) - כל שירות ב-docker-compose.yml
  ממופה לשירות מקביל בפלטפורמה. הגדירו את משתני הסביבה מ-`.env.example` בממשק שלהם.
- **AWS/GCP/Azure**: ECS/Cloud Run/Container Apps + RDS/Cloud SQL (Postgres
  מנוהל) + ElastiCache/Memorystore (Redis מנוהל). מומלץ לארגונים גדולים יותר.

## Cron / סריקות מתוזמנות

שירות `beat` ב-docker-compose.yml מריץ את Celery Beat שמפעיל אוטומטית
`run_scheduled_scans` כל שעה (וכל מקור מכבד את תדירות הסריקה שהוגדרה לו
ב"מקורות מידע" - שעתי/כל 3 שעות/יומי וכו'), `check_closing_tenders` כל 3
שעות, ו-`check_changes_all` פעם ביום. אין צורך בהגדרת Cron חיצוני - ה-container
`beat` הוא ה-Cron.

## Health Check

`GET /health` (ללא אימות) מחזיר `{"status": "ok"}` - מתאים ל-Load
Balancer/Uptime monitor. `GET /api/admin/health` (Admin בלבד) מחזיר סטטוס
מפורט: DB, האם AI/חיפוש/Email מוגדרים, מספר מקורות פעילים/עם שגיאה, עבודות
שהצליחו/נכשלו.

## Scaling

- `worker`: הגדילו `--concurrency` או הריצו כמה instances של השירות מאחורי
  אותו broker (Redis) לביצוע מקבילי מבוקר של סריקות.
- `postgres`: לצמיחה מעבר למאות אלפי רשומות, שקלו מעבר ל-Postgres מנוהל עם
  replicas לקריאה.
- הוסיפו Index נוספים לפי דפוסי שאילתה בפועל (כל השדות הנפוצים לסינון כבר
  מאונדקסים ב-migration הראשונית).
