# database.py communicates with MySQL
import mysql.connector
import os
import hashlib
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".env"
    )
)

# MySQL configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": "todo_app"
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)

        if conn.is_connected():
            return conn

    except Error as e:
        print(f"Database connection error: {e}")

    return None


# Initialize database
def init_db():
    with open("schema.sql", "r") as f:
        schema = f.read()

    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    # schema.sql contains multiple statements
    for statement in schema.split(";"):
        statement = statement.strip()

        if statement:
            cursor.execute(statement)

    conn.commit()

    cursor.close()
    conn.close()


# Adding a task
def add_task(user_id, title, due_date, due_time, priority, tag):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks
        (user_id, title, due_date, due_time, priority, tag)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, title, due_date, due_time, priority, tag)
    )

    conn.commit()

    cursor.close()
    conn.close()


# Returns one single task based on task_id
def get_task(task_id, user_id):
    conn = get_db_connection()

    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM tasks WHERE id = %s and user_id = %s",
        (task_id, user_id)
    )

    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return task


# Returns all tasks
def get_all_tasks(user_id):
    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE user_id = %s
        ORDER BY completed ASC, due_date ASC, due_time ASC, created_at DESC
        """,
        (user_id,)
    )

    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return tasks


# Update edited tasks
def update_task(task_id, user_id, title, due_date, due_time, priority, tag):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title = %s,
            due_date = %s,
            due_time = %s,
            priority = %s,
            tag = %s
        WHERE id = %s AND user_id = %s
        """,
        (title, due_date, due_time, priority, tag, task_id, user_id)
    )

    conn.commit()

    cursor.close()
    conn.close()


# Delete task
def delete_task(task_id, user_id):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET deleted = 1 WHERE id = %s AND user_id = %s",
        (task_id, user_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

def restore_task(task_id, user_id):
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET deleted = 0 WHERE id = %s AND user_id = %s",
        (task_id, user_id)
    )
    conn.commit()
    
    cursor.close()
    conn.close()
    
# Mark task as complete / incomplete
def toggle_task(task_id, user_id):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET completed = CASE
            WHEN completed = 0 THEN 1
            ELSE 0
        END
        WHERE id = %s AND user_id = %s
        """,
        (task_id, user_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

# ------------- LAB 2 FUNCTIONS ------------- #

# create user function
def create_user (email, display_name, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, display_name, password_hash) VALUES (%s, %s, %s)",
        (email, display_name, password_hash)
    )
    conn.commit()
    
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return user_id

# find user and get info in db using email
def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# find user and get info in db using id
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# for edit profile function
def update_display_name(user_id, display_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET display_name = %s WHERE id = %s",
        (display_name, user_id)
    )
    conn.commit()
    
    cursor.close()
    conn.close()

# update password hash for reset password function
def update_password_hash(user_id, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (password_hash, user_id)
    )
    conn.commit()
    
    cursor.close()
    conn.close()

# permanently delete user account
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    
    cursor.close()
    conn.close()

# get statustics for a user
def get_task_stats(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(completed = 1), 0) AS done,
            COALESCE(SUM(completed = 0), 0) AS open,
            COALESCE(SUM(completed = 0 AND due_date < CURDATE()), 0) AS overdue
        FROM tasks
        WHERE user_id = %s
        """,
        (user_id,)
    )
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    return stats

# convert a reset token into a hash
def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

# create a password reset token for user
def create_reset_token(user_id, token, minutes=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    #one active link per user, delete any existing tokens for the user
    cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (user_id,))
    cursor.execute(
        """
        INSERT INTO password_resets (user_id, reset_token, expires_at)
        VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL %s MINUTE))
        """,
        (user_id, _hash_token(token), minutes)
    )
    conn.commit()
    
    cursor.close()
    conn.close()

# check for validity if the token exists 
def get_valid_reset(token):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT * FROM password_resets
        WHERE reset_token = %s AND expires_at > NOW()
        """,
        (_hash_token(token),)
    )
    reset_entry = cursor.fetchone()
    cursor.close()
    conn.close()
    return reset_entry

# delete a reset token after it has been used
def delete_reset_token(reset_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM password_resets WHERE id = %s", (reset_id,))
    conn.commit()
    
    cursor.close()
    conn.close()