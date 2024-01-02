# AITA API

This repository is a complete rewrite of reddit-store using FastAPI and SQLModel

```sql
SELECT *, strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS MONTH, strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS YEAR FROM submission;
```