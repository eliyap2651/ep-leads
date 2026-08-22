# גיבוי ושחזור

## גיבוי ידני מהיר

```bash
docker compose exec postgres pg_dump -U ep_leads -Fc ep_leads > backup_$(date +%Y%m%d_%H%M%S).dump
```

## שחזור

```bash
docker compose exec -T postgres pg_restore -U ep_leads -d ep_leads --clean --if-exists < backup_FILE.dump
```

## גיבוי אוטומטי יומי (מומלץ ל-Production)

הוסיפו לשרת (מחוץ ל-Docker) cron יומי:

```cron
0 3 * * * cd /path/to/ep-leads && docker compose exec -T postgres pg_dump -U ep_leads -Fc ep_leads > /backups/ep_leads_$(date +\%Y\%m\%d).dump && find /backups -mtime +30 -delete
```

זה שומר גיבוי יומי ומוחק גיבויים ישנים מ-30 יום. מומלץ להעלות את הגיבויים
גם ליעד חיצוני (S3/Backblaze/Google Cloud Storage) ולא רק לדיסק המקומי של
השרת.

## מעקב סטטוס גיבוי במערכת

מסך "ניטור מערכת" (Admin) מיועד להציג "גיבוי אחרון" ו"סטטוס גיבוי" (סעיף 54
במפרט). כרגע אין עדיין job ייעודי שכותב את הסטטוס הזה ל-DB - ניתן להוסיף
משימת Celery `run_backup` שמריצה את `pg_dump` ורושמת שורה לטבלת `settings`
(`last_backup_at`, `last_backup_status`), ואז מסך הניטור יקרא אותה. זהו
הרחבה ישירה של התשתית הקיימת (ראה `app/workers/tasks.py`).

## שחזור מלא לשרת חדש

1. התקינו Docker + שבטו את הקוד כרגיל.
2. הריצו `docker compose up -d postgres` בלבד תחילה.
3. שחזרו את הגיבוי לתוך ה-container (פקודת restore למעלה).
4. הריצו `docker compose up -d` להשלמת שאר השירותים - Alembic יזהה שהסכימה
   כבר קיימת ולא ינסה ליצור מחדש.
