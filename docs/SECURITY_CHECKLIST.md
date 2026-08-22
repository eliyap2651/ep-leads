# Security Checklist

| נושא | מצב | פירוט |
|---|---|---|
| Authentication | ✅ | JWT access+refresh, bcrypt password hashing (passlib) |
| Sessions | ✅ | Stateless JWT; access token קצר-מועד (30 דק׳ ברירת מחדל), refresh ל-14 יום |
| RBAC | ✅ | Admin / Sales Manager / Sales Agent / Viewer, נאכף ב-dependency injection בכל endpoint רגיש |
| Rate limiting | ✅ | slowapi על `/api/auth/login` (10/דקה כברירת מחדל); ניתן להרחיב לכלל ה-API |
| Input validation | ✅ | Pydantic v2 על כל קלט; FastAPI מחזיר 422 עם exception handler ייעודי |
| SQL Injection | ✅ | SQLAlchemy ORM עם parameterized queries בלבד - אין string concatenation לשאילתות |
| XSS | ✅ | React מבצע escaping אוטומטי; לא נעשה שימוש ב-`dangerouslySetInnerHTML`; security headers (`X-Content-Type-Options`, `X-Frame-Options`) |
| CSRF | ⚠️ ראו הערה | האפליקציה משתמשת ב-Bearer token ב-`Authorization` header (לא cookies) - סיכון CSRF קלאסי לא רלוונטי כל עוד הטוקן לא מאוחסן ב-cookie. אם בעתיד תעברו לאחסון ב-cookie, הוסיפו CSRF token מפורש. |
| Secrets | ✅ | כל מפתח (Anthropic/Serper/SMTP/SECRET_KEY) נקרא אך ורק מ-Environment Variables (`app/config.py`); `.env` ב-`.gitignore`; שום מפתח לא מוטבע בקוד |
| Frontend secrets | ✅ | ה-Frontend מדבר רק עם ה-Backend שלנו; אין שום API key בצד הלקוח |
| Password strength | ✅ | אורך מינימלי 8 תווים (`Pydantic Field(min_length=8)`) - ניתן להחמיר |
| HTTPS | ⚠️ תלוי בפריסה | ה-container לא מטפל ב-TLS; יש להציב reverse proxy עם HTTPS אמיתי (ראו `docs/DEPLOYMENT.md`) |
| Least privilege DB user | ⚠️ מומלץ | הגדירו למשתמש ה-Postgres של האפליקציה רק את ההרשאות הנדרשות (לא superuser) בסביבת Production |
| Dependency scanning | 📋 מומלץ | הוסיפו `pip-audit`/`npm audit` ל-CI לפני deploy |
| Logging | ✅ | structlog בפורמט JSON; פעולות רגישות (שינוי סטטוס, מחיקה) נרשמות ל-`activities` |
| Error handling | ✅ | מקור סריקה שנכשל לא מפיל מקורות אחרים (`try/except` סביב כל source ב-worker) |
| Data provenance | ✅ | כל שדה עובדתי מקושר ל-Source URL; שדה שלא נמצא מוצג "לא נמצא" ולעולם לא מומצא |
| Robots.txt / legality | ✅ | כל אדפטר סריקה בודק `robots.txt` לפני גישה; אין עקיפת CAPTCHA/login/paywall בקוד |

## המלצות לפני עלייה ל-Production אמיתי

1. הריצו `openssl rand -hex 32` וקבעו כ-`SECRET_KEY` ייחודי (לא זה שבדוגמה).
2. ודאו ש-`DEBUG=false` וש-`FRONTEND_ORIGIN` מוגדר לדומיין האמיתי בלבד (לא `*`).
3. הפעילו גיבוי אוטומטי (`docs/BACKUP.md`) לפני שיש נתונים אמיתיים במערכת.
4. הגבילו גישת רשת ל-Postgres/Redis כך שלא ייחשפו לאינטרנט (ברירת המחדל
   ב-docker-compose חושפת את פורט 5432 להקלת דיבוג מקומי - הסירו את מיפוי
   הפורט הזה בפרודקשן אמיתי).
5. סיווגו את כל המשתמשים לתפקיד המתאים (Admin רק למי שבאמת צריך).
