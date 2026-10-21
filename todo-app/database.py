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
def add_task(user_id, list_id, title, due_date, due_time, priority, tag):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks
        (user_id, list_id, title, due_date, due_time, priority, tag)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        from list_members
        WHERE list_id = %s and user_id = %s
        """,
        (user_id, list_id, title, due_date, due_time, priority, tag, list_id, user_id)
    )

    conn.commit()
    task_id = cursor.lastrowid if cursor.rowcount == 1 else None   # None = not a member
    cursor.close()
    conn.close()
    return task_id


# Returns one single task based on task_id
def get_task(task_id, user_id):
    conn = get_db_connection()

    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """SELECT t.* 
        FROM tasks t 
        JOIN list_members m ON m.list_id = t.list_id
        WHERE t.id = %s and m.user_id = %s""",
        (task_id, user_id)
    )

    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return task


# Returns all tasks
def get_all_tasks(user_id, list_id):
    conn = get_db_connection()

    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT t.*
        FROM tasks t
        JOIN list_members m ON m.list_id = t.list_id
        WHERE t.user_id = %sAND m.user_id = %s AND t.deleted = 0
        ORDER BY t.due_date, t.due_time
        """,
        (list_id,user_id)
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
        UPDATE tasks t
        JOIN list_members m ON m.list_id = t.list_id
        SET t.title = %s,
            t.due_date = %s,
            t.due_time = %s,
            t.priority = %s,
            t.tag = %s
        WHERE t.id = %s AND t.user_id = %s
        """,
        (title, due_date, due_time, priority, tag, task_id, user_id)
    )

    conn.commit()
    changed = cursor.rowcount > 0
    cursor.close()
    conn.close()
    
    return changed


# Delete task
def delete_task(task_id, user_id):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        """UPDATE tasks t
        JOIN list_members m ON m.list_id = t.list_id
        SET t.deleted = 1 
        WHERE t.id = %s AND t.user_id = %s""",
        (task_id, user_id,)
    )

    conn.commit()
    changed = cursor.rowcount > 0
    
    cursor.close()
    conn.close()
    return changed

def restore_task(task_id, user_id):
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tasks t
        JOIN list_members m ON m.list_id = t.list_id
        SET t.deleted = 0 
        WHERE t.id = %s AND t.user_id = %s""",
        (task_id, user_id)
    )
    conn.commit()
    changed = cursor.rowcount > 0
    
    cursor.close()
    conn.close()
    return changed
    
# Mark task as complete / incomplete
def toggle_task(task_id, user_id):
    conn = get_db_connection()

    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks t
        JOIN list_members m ON m.list_id = t.list_id
        SET t.completed = CASE
            WHEN t.completed = 0 THEN 1
            ELSE 0
        END
        WHERE t.id = %s AND t.user_id = %s
        """,
        (task_id, user_id)
    )

    conn.commit()
    changed = cursor.rowcount > 0
    
    cursor.close()
    conn.close()
    return changed

# ------------- LAB 2 FUNCTIONS ------------- #

# create user function; automatically creates personal list on registration
def create_user (email, display_name, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try: 
        cursor.execute(
            "INSERT INTO users (email, display_name, password_hash) VALUES (%s, %s, %s)",
            (email, display_name, password_hash)
        )
        user_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO lists (name, owner_id, is_personal) VALUES (%s, %s, 1)",
            ("Personal", user_id)
        )
        list_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO list_members (list_id, user_id) VALUES (%s, %s)",
            (list_id, user_id)
        )
        conn.commit()
        return user_id
    
    except Exception:
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()

# fetches list details, mainly for finding out ownership
def get_list_details(list_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, owner_id, is_personal FROM lists WHERE id = %s",
        (list_id,)
    )
    lst = cursor.fetchone()
    cursor.close()
    conn.close()
    return lst

# owned of list allowed to removed member
def remove_member(list_id, owner_id, member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE m FROM list_members m
        JOIN lists l ON l.id = m.list_id
        WHERE m.list_id = %s
          AND m.user_id = %s
          AND l.owner_id = %s
          AND m.user_id <> l.owner_id
        """,
        (list_id, member_id, owner_id)
    )
    conn.commit()
    removed = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return removed

# deletes shared lists only, personal lists cant be deleted
def delete_list(list_id, owner_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM lists WHERE id = %s AND owner_id = %s AND is_personal = 0",
        (list_id, owner_id)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return deleted

# creates shared list 
def create_shared_list (owner_id, name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO lists (name, owner_id, is_personal) VALUES (%s, %s, 0)",
            (name, owner_id)
        )
        list_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO list_members (list_id, user_id) VALUES (%s, %s)",
            (list_id, owner_id)
        )

        conn.commit()
        return list_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        
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

# find user by username or email for shared list invites
def find_user_for_invite(value):
    value = value.strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, email, username, display_name FROM users WHERE email = %s OR username = %s",
        (value, value)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# fetches every list current user belongs to 
def get_lists_for_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT l.id, l.name, l.owner_id, l.is_personal,
                   (SELECT COUNT(*) FROM tasks t
                    WHERE t.list_id = l.id
                      AND t.deleted = 0
                      AND t.completed = 0) AS open_count
            FROM lists l
            JOIN list_members m ON m.list_id = l.id
            WHERE m.user_id = %s
            ORDER BY l.is_personal DESC, l.created_at
            """,
            (user_id,)
        )
        rows = cursor.fetchall()

        personal = [r for r in rows if r["is_personal"]]
        shared = [r for r in rows if not r["is_personal"]]
        return personal, shared
    finally:
        cursor.close()
        conn.close()

# checks if user is in this specific list, also prevents access by url
def is_member(list_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT 1 FROM list_members WHERE list_id = %s AND user_id = %s",
            (list_id, user_id)
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()
        
# adds member to list; ignores if already on list
def add_member(list_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT IGNORE INTO list_members (list_id, user_id) VALUES (%s, %s)",
            (list_id, user_id)
        )
        conn.commit()
        return cursor.rowcount == 1    # true = added, false = already a member
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# returns people part of list, for showing later who added which tasks and member count
def get_members(list_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT u.id, u.display_name, u.email,
                   (u.id = l.owner_id) AS is_owner
            FROM list_members m
            JOIN users u ON u.id = m.user_id
            JOIN lists l ON l.id = m.list_id
            WHERE m.list_id = %s
            ORDER BY is_owner DESC, m.joined_at
            """,
            (list_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

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
def get_task_stats(list_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(completed = 1), 0) AS done,
            COALESCE(SUM(completed = 0), 0) AS open,
            COALESCE(SUM(completed = 0 AND due_date < CURDATE()), 0) AS overdue
        FROM tasks t
        JOIN list_members m ON m.list_id = t.list_id
        WHERE t.list_id = %s AND m.user_id = %s AND t.deleted = 0
        """,
        (list_id, user_id)
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