sh ./migrate.sh
PYTHONUNBUFFERED=TRUE gunicorn -b 0.0.0.0:5000 app:app --capture-output