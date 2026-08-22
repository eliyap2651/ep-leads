# EP LEADS

מערכת מודיעין עסקי, מכרזים ולידים ארצית לתחום הריהוט בישראל.

"מצא לי את העסקה הבאה שלי."

## מה זה

EP LEADS סורקת מקורות מידע אמיתיים (אתרי מכרזים, עיריות, חברות ממשלתיות, RSS,
Sitemap, חיפוש חיצוני, מסמכי PDF) כדי לאתר הזדמנויות עסקיות לרכש ריהוט - לפני
או בזמן שבו מתקבלת החלטת הרכש - מדרגת אותן אוטומטית (0-100), מנהלת אותן ב-CRM
מובנה, ומתריעה על שינויים ומועדים קריטיים. שום מידע לא מומצא: כל שדה מקושר
למקור, ושדה שלא נמצא מוצג כ"לא נמצא".

## ארכיטקטורה

```
ep-leads/
├── backend/           FastAPI + SQLAlchemy 2.0 + Alembic + Celery
│   ├── app/
│   │   ├── api/        REST endpoints
│   │   ├── core/        אבטחה, RBAC, rate limiting
│   │   ├── models/       טבלאות SQLAlchemy
│   │   ├── schemas/      Pydantic
│   │   ├── services/     מנועי ליבה (ניקוד, דה-דופ, AI, PDF, אדפטרים)
│   │   └── workers/      Celery tasks + beat schedule
│   ├── alembic/          מיגרציות DB
│   └── tests/            pytest
├── frontend/          React + TypeScript + Vite + Tailwind (Mobile-First, RTL, PWA)
├── docker-compose.yml
├── docker-compose.test.yml
└── .env.example
```

ראו את מסמך הארכיטקטורה המלא שנשלח בתחילת הפרויקט לפירוט מלא של כל החלטה טכנולוגית.

## הרצה מקומית (Docker)

דרישות: Docker + Docker Compose, וגישה רגילה לאינטרנט (להורדת חבילות/images).

```bash
cp .env.example .env
# ערכו את .env: מלאו SECRET_KEY, POSTGRES_PASSWORD, ADMIN_EMAIL/ADMIN_PASSWORD
# לפחות. ANTHROPIC_API_KEY ו-SERPER_API_KEY נדרשים כדי להפעיל AI/חיפוש חיצוני,
# אך המערכת עולה ורצה גם בלעדיהם (עם הודעת "לא מוגדר" ברורה בפיצ'רים התלויים בהם).

docker compose up --build -d

# לוגים:
docker compose logs -f backend worker beat

# המערכת זמינה ב:
#   Backend API:  http://localhost:8000/api   (תיעוד אינטראקטיבי: http://localhost:8000/docs)
#   Frontend:     http://localhost:5173
```

בעליית `backend` המכולה מריצה אוטומטית `alembic upgrade head` ואז `python -m
app.seed` שיוצר בדיוק משתמש Admin אחד (מתוך ADMIN_EMAIL/ADMIN_PASSWORD ב-.env)
- ללא שום ליד/חברה/מכרז מזויפים (ראה סעיף 49-50 במפרט המקורי).

התחברו ל-Frontend עם פרטי ה-Admin, ואז דרך מסך **מקורות מידע** הוסיפו את
המקורות האמיתיים הרלוונטיים לכם (אתרי עיריות, michrazim.gov.il וכו') ודרך
מסך **שאילתות חיפוש** הגדירו שאילתות (המערכת מגיעה ריקה מהן בכוונה - ראו
"מקורות זמינים להוספה" למטה).

## גישה מהאייפון

זהו PWA (Progressive Web App): פתחו את כתובת ה-Frontend ב-Safari באייפון,
לחצו "שתף" ← "הוסף למסך הבית" - האפליקציה תתנהג כמו אפליקציה מותקנת, מסך
מלא, כולל אייקון. אין צורך ב-App Store.

**חשוב:** כדי שהאייפון יוכל להתחבר, ה-Backend וה-Frontend צריכים להיות
נגישים דרך כתובת אמיתית (דומיין+HTTPS) ולא localhost - ראו `docs/DEPLOYMENT.md`.

## מקורות זמינים להוספה (דוגמאות אמיתיות להתחלה)

המערכת מגיעה נקייה ממקורות (ללא Mock), אך מסך "מקורות מידע" מאפשר להוסיף
כל מקור. דוגמאות טובות להתחלה בישראל (בדקו את תנאי השימוש/robots.txt של כל
אתר לפני הוספה - המערכת מכבדת robots.txt אוטומטית):

- אתרי "מכרזים"/"רכש"/"מאגר ספקים" של עיריות ומועצות (Adapter: HTML)
- gov.il - מכרזים ממשלתיים (בדקו האם יש API/RSS רשמי; אחרת HTML)
- אתרי חברות ממשלתיות (רכבת ישראל, רשות מקרקעי ישראל וכו')
- פידי RSS של אתרי חדשות עסקיים/נדל"ן (Adapter: RSS)
- Sitemap.xml של אתרי מוסדות גדולים (Adapter: Sitemap, עם מילות מפתח)

## בדיקות (Tests)

```bash
cd backend
docker compose -f ../docker-compose.yml -f ../docker-compose.test.yml up -d postgres-test
export TEST_DATABASE_URL=postgresql+asyncpg://ep_leads:ep_leads@localhost:5433/ep_leads_test
pytest -v
```

ראו `docs/TESTING.md` לפירוט מלא.

## תיעוד נוסף

- `docs/DEPLOYMENT.md` - פריסה לסביבת Production אמיתית (VPS/ענן, HTTPS, דומיין)
- `docs/BACKUP.md` - גיבוי ושחזור מסד הנתונים
- `docs/SECURITY_CHECKLIST.md` - רשימת אבטחה
- `docs/API.md` - סקירת ה-REST API (התיעוד המלא והאינטראקטיבי תמיד ב-`/docs`)
- `docs/TESTING.md` - הרצת בדיקות

## הערה על מגבלת סביבת הפיתוח

הקוד בריפו זה נכתב ונבדק (syntax + לוגיקת ליבה דטרמיניסטית) בסביבת Sandbox
ללא גישה לאינטרנט להתקנת חבילות (`pip`/`npm`) ובלי Docker daemon פעיל - לכן
לא בוצעה כאן הרצה מלאה של `docker compose up` או `pytest` מול Postgres אמיתי.
בהרצה במחשב/שרת עם גישה רגילה לאינטרנט, `docker compose up --build` אמור
לעלות בהצלחה מהקופסה. אם תיתקלו בשגיאה - שלחו לי אותה ואני אתקן.
