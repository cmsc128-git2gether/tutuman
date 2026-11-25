from database import get_db_connection

conn = get_db_connection()

if conn:
    print("MySQL connection successful!")

    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE();")

    result = cursor.fetchone()

    print("Current database:", result[0])

    cursor.close()
    conn.close()