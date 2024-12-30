import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "n8n",
    "user": "root",
    "password": "password"
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("Database connection successful!")
    conn.close()
except Exception as e:
    print("Error connecting to the database:", e)

