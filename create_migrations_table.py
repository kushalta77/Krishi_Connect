import MySQLdb

conn = MySQLdb.connect(host='localhost', user='root', password='', db='krishi_connect')
cursor = conn.cursor()

# Create the django_migrations table if it doesn't exist
sql = """
CREATE TABLE IF NOT EXISTS django_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied DATETIME NOT NULL,
    UNIQUE KEY (app, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

try:
    cursor.execute(sql)
    conn.commit()
    print("django_migrations table is ready")
except Exception as e:
    print(f"Error: {e}")

cursor.close()
conn.close()
