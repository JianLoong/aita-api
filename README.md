# AITA API

This repository is a complete rewrite of reddit-store using FastAPI and SQLModel

```sql
SELECT *, strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS MONTH, strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS YEAR FROM submission;
```

```sql
--SELECT * FROM submission ORDER BY id DESC;

SELECT s.id, title, strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_month, 
strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_year,
MAX(yta) AS yta,
FROM submission s
INNER JOIN breakdown ON s.id = breakdown.id
GROUP BY sub_month, sub_year
ORDER BY sub_month, sub_year;
```