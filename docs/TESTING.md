# הרצת בדיקות

## דרישות מוקדמות

- Python 3.11+, Docker (לבסיס נתונים ייעודי לבדיקות)

## הרצה

```bash
cd backend
pip install -r requirements.txt

# בסיס נתונים נקי ומבודד לבדיקות בלבד (פורט 5433, לא מתנגש עם ה-DB הראשי):
docker compose -f ../docker-compose.yml -f ../docker-compose.test.yml up -d postgres-test

export TEST_DATABASE_URL=postgresql+asyncpg://ep_leads:ep_leads@localhost:5433/ep_leads_test
pytest -v
```

## מה מכוסה

| קובץ | מכסה |
|---|---|
| `test_scoring.py` | מנוע ניקוד הלידים (0-100), חלוקה ל-HOT/HIGH/MEDIUM/LOW, גבולות |
| `test_dedup.py` | זיהוי כפילויות: מספר מכרז, דומיין, טלפון, מייל, שם מטושטש |
| `test_contact_extraction.py` | חילוץ טלפון/מייל דטרמיניסטי מטקסט חופשי |
| `test_auth.py` | Login, טוקנים, הגנה על endpoints |
| `test_leads_crud.py` | CRUD לידים, סינון, הערות, activity log |
| `test_permissions.py` | RBAC - Admin/Sales Agent/Viewer, ראיית לידים לפי הקצאה |
| `test_export.py` | ייצוא CSV/Excel |
| `test_tender_date_extraction.py` | חישוב ימים למועד אחרון; טיפול תקין בהיעדר מפתח AI |

## בדיקות שדורשות מפתח AI אמיתי (לא רצות כברירת מחדל)

ניתוח מסמכי מכרז (`AIEngine.analyze_tender_document`) ו-AI Sales Assistant
קוראים ל-Anthropic API בפועל. אלה **לא** נבדקים אוטומטית ב-CI הרגיל (כדי לא
לחייב מפתח תשלום/רשת בכל הרצת בדיקות) - `test_tender_date_extraction.py`
מוודא רק שהמערכת נכשלת בצורה ברורה (`AIUnavailableError`) כשאין מפתח, ולא
בצורה שקטה/מומצאת. אם תרצו בדיקת אינטגרציה מלאה מול AI אמיתי, הוסיפו קובץ
`test_ai_integration.py` עם `@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"))`.

## CI (מומלץ)

הוסיפו GitHub Actions workflow עם `services: postgres:` (ראו תיעוד GitHub
Actions) שמריץ את אותה פקודת `pytest` בכל push - כך תקבלו גם ריצת Docker
build אמיתית שלא זמינה בסביבה בה נכתב קוד זה.
