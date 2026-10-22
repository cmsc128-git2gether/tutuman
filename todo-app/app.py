# app.py is the main Python file and runs Flask
import os
import re
import secrets
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import IntegrityError
from mailer import send_reset_email

from database import (
    get_db_connection,
    add_task,
    get_task,
    get_valid_reset,
    update_task,
    delete_task,
    restore_task,
    toggle_task,
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_display_name,
    update_password_hash,
    delete_user,
    get_task_stats,
    create_reset_token,
    get_valid_reset,
    delete_reset_token,
    get_lists_for_user,
    create_shared_list,
    is_member,
    get_list_details,
    get_members,
)

load_dotenv()
print("SMTP_HOST =", os.getenv("SMTP_HOST"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=7)


# prevents cached copy of pages from being displayed after logout
@app.after_request
def no_cache(response):
    if request.endpoint != 'static':
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# checks if user is logged in 
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

# format dates
@app.template_filter('format_date')
def format_date(date_value):
    if not date_value:
        return None

    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()

    return date_value.strftime("%A, %b %d")

# Time formatter
@app.template_filter('format_time')
def format_time(time_value):
    if not time_value:
        return None

    if isinstance(time_value, str):
        time_obj = datetime.strptime(time_value, "%H:%M").time()
    elif isinstance(time_value, timedelta):
        # MySQL TIME values are returned as timedelta
        total_seconds = int(time_value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        time_obj = datetime.strptime(
            f"{hours:02d}:{minutes:02d}",
            "%H:%M"
        ).time()
    else:
        time_obj = time_value

    return time_obj.strftime("%I:%M %p")

# For the home interface

@app.route('/tasks')
@login_required
def index():
    tab = request.args.get('tab', 'all')
    view_mode = request.args.get('view', 'list')
    priority_filter = request.args.get('priority', '')
    tag_filter = request.args.get('tag', '')
    user = get_user_by_id(session["user_id"])
    user_id = session["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tasks WHERE user_id = %s AND deleted = 0",
        (user_id,)
    )
    
    all_tasks = cursor.fetchall()
    total_count = len(all_tasks)
    open_count = sum(1 for t in all_tasks if t['completed'] == 0)
    done_count = sum(1 for t in all_tasks if t['completed'] == 1)

    query = 'SELECT * FROM tasks WHERE user_id = %s AND deleted = 0'
    params = [user_id]
    
    if tab == 'ongoing':
        query += ' AND completed = 0'
    elif tab == 'completed':
        query += ' AND completed = 1'
    
    if priority_filter:
        query += ' AND priority = %s'
        params.append(priority_filter)

    if tag_filter:
        query += ' AND tag = %s'
        params.append(tag_filter)
        
    # Displays tasks in a specific order
    query += ''' 
        ORDER BY
            due_date ASC,
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Med' THEN 2
                WHEN 'Low' THEN 3
            END ASC,
            due_date ASC,
            due_time ASC
    '''
    cursor.execute(query, params)
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    today = datetime.now().date()
    
    # For pedning and completed tasks
    open_tasks = [t for t in tasks if t['completed'] == 0]
    done_tasks = [t for t in tasks if t['completed'] == 1]

    today_tasks = []
    upcoming_tasks = []
    no_due_date_tasks = []

    for t in open_tasks:
        if not t['due_date']:
            no_due_date_tasks.append(t)
            continue

        due = t['due_date']

        if isinstance(due, str):
            due = datetime.strptime(due, "%Y-%m-%d").date()
            
        if due <= today:
            # overdue tasks are folded into "Today" so nothing open silently disappears
            today_tasks.append(t)
        else:
            upcoming_tasks.append(t)

    # Only include non-empty groups, keeps template logic simple
    grouped_open = []
    if today_tasks:
        grouped_open.append(("Today", today_tasks))
    if no_due_date_tasks:
        grouped_open.append(("No Due Date", no_due_date_tasks))
    if upcoming_tasks:
        grouped_open.append(("Upcoming", upcoming_tasks))

    # Week-Date Range
    def fmt(d):
        return d.strftime("%b %d").replace(" 0", " ")

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    date_range = f"{fmt(start_of_week)} - {end_of_week.day}, {end_of_week.year}"

    # Direct to index.html
    return render_template(
        'index.html',
        grouped_open=grouped_open,
        done_tasks=done_tasks,
        today_tasks=today_tasks,
        tab=tab,
        view_mode=view_mode,
        priority_filter=priority_filter,
        tag_filter=tag_filter,
        total_count=total_count,
        open_count=open_count,
        done_count=done_count,
        date_range=date_range,
        user=user,
    )

# For adding tasks
@app.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form['title']
    due_date = request.form.get('due_date') or None
    due_time = request.form.get('due_time') or None
    priority = request.form.get('priority') or None
    tag = request.form.get('tag') or None

    
    add_task(
        session["user_id"],
        title,
        due_date,
        due_time, 
        priority,
        tag
    )
    
    return redirect(url_for('index'))
   
# For completing tasks
@app.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def toggle(task_id):
    toggle_task(task_id, session["user_id"],) 
    
    return redirect(url_for('index'))

# For deleting tasks
@app.route('/delete/<int:task_id>', methods=['DELETE'])
@login_required
def delete(task_id):
    delete_task(task_id, session["user_id"],)
    return '', 204

# For deleting tasks
@app.route('/restore/<int:task_id>', methods=['POST'])
@login_required
def restore(task_id):
    restore_task(task_id, session["user_id"],)
    return '', 204

# For editing task and updating values of edited tasks
@app.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def update(task_id):
    title = request.form['title']
    due_date = request.form.get('due_date') or None
    due_time = request.form.get('due_time') or None
    priority = request.form.get('priority') or None
    tag = request.form.get('tag') or None
    
    update_task(
        task_id,
        session["user_id"],
        title,
        due_date,
        due_time,
        priority,
        tag
    )
    
    return redirect(url_for('index'))

# --------- LAB 2 FUNCTIONS --------- #

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8

@app.route('/')
def home():
    if "user_id" in session:
        return redirect(url_for("profile"))
    return redirect(url_for("login"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    # show form on GET method
    if request.method == 'GET':
        return render_template('register.html')
    
    # read form on POST method
    # TODO: implement added requirements for password (e.g must include sysmbols, etc)
    email = request.form.get('email', '').strip().lower()
    display_name = request.form.get('display_name', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # form validation
    error = None 
    if not email or not display_name or not password or not confirm_password:
        error = "All fields are required."
    elif not EMAIL_PATTERN.match(email):
        error = "Please enter a valid email address."
    elif len(password) < MIN_PASSWORD_LENGTH:
        error = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    elif password != confirm_password:
        error = "Passwords do not match."
    elif get_user_by_email(email):
        error = "An account with that email already exists."
        
    if error:
        flash(error, "error")
        return render_template('register.html', email=email, display_name=display_name)
    
    # hash password and save user
    password_hash = generate_password_hash(password)
    try:
        create_user(email, display_name, password_hash)
    except IntegrityError:
        # registering using same email causes errors
        flash("An account with that email already exists.", "error")
        return render_template('register.html', email=email, display_name=display_name)
    
    # redirect to login on successful register
    flash("Account created. Please log in.", "success")
    return redirect(url_for('login'))

# Display the login form or authenticate the submitted credentials.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if "user_id" in session:
        return redirect(url_for("profile"))

    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    error = None
    user = None
    
    if not email or not password:
        error = "Email and password are required."
    elif not EMAIL_PATTERN.match(email):
        error = "Please enter a valid email address."
    elif len(password) < MIN_PASSWORD_LENGTH:
        error = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    else:
        user = get_user_by_email(email)
        if user is None:
            error = "No account found with that email."
        elif not check_password_hash(user["password_hash"], password):
            error = "Incorrect password."

    if error:
        flash(error, "error")
        return render_template('login.html', email=email)
    
    session.clear() 
    session.permanent = True
    session["user_id"] = user["id"]
    return redirect(url_for("index"))

# Profile page shows the current user's account details
@app.route('/profile')
@login_required
def profile():
    user = get_user_by_id(session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login"))
    stats = get_task_stats(user["id"])
    return render_template('profile.html', user=user, stats=stats)

# Edit profile updates the display name submitted from the profile form.
@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    display_name = request.form.get('display_name', '').strip()

    if not display_name:
        flash("Display name can't be empty.", "error")
    elif len(display_name) > 100:
        flash("Display name must be 100 characters or fewer.", "error")
    else:
        update_display_name(session["user_id"], display_name)
        flash("Display name updated.", "success")

    return redirect(url_for('profile'))

# Verify the current password before saving a new one.
@app.route('/profile/password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_new_password = request.form.get('confirm_new_password', '')
    
    # Load the user's stored password hash for verification.
    user = get_user_by_id(session["user_id"])

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    # Validate the current password, new password length, and confirmation
    if not check_password_hash(user["password_hash"], current_password):
        flash("Current password is incorrect.", "error")
    elif len(new_password) < MIN_PASSWORD_LENGTH:
        flash(f"New password must be at least {MIN_PASSWORD_LENGTH} characters.", "error")
    elif new_password != confirm_new_password:
        flash("New passwords do not match.", "error")
    elif new_password == current_password:
        flash("New password must be different from the current one.", "error")
    else:
        update_password_hash(user["id"], generate_password_hash(new_password))
        flash("Password updated.", "success")

    return redirect(url_for('profile'))

# Remove the user's account and end their session.
@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('delete_password', '')
    user = get_user_by_id(session["user_id"])

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    if not check_password_hash(user["password_hash"], password):
        flash("Incorrect password. Your account was not deleted.", "error")
        return redirect(url_for('profile'))
    
    delete_user(session["user_id"])
    session.clear()
    flash("Your account has been deleted.", "success")
    return redirect(url_for('login'))

# End the current session and return the user to the login page
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

# This route currently clears the session and behaves like a logout endpoint
@app.route('/edit_profile', methods=['POST'])
def login_required():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

# Accept an email and send a reset link if an account exists
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_pass.html')

    email = request.form.get('email', '').strip().lower()
    user = get_user_by_email(email)

    if user: 
        token = secrets.token_urlsafe(32)
        create_reset_token(user["id"], token)
        link = url_for('reset_password', token=token, _external=True)
        send_reset_email(email, link)
        
    flash("A password reset link has been sent to your email.", "success")
    return redirect(url_for('login'))

# Validate the token, then allow the user to choose a new password.
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = get_valid_reset(token)
    if reset is None: 
        flash("Invalid or expired password reset link.", "error")
        return redirect(url_for('forgot_pass'))
    
    if request.method == 'GET':
        return render_template('reset_pass.html', token=token)
    
    new_password = request.form.get('new_password', '')
    confirm_new_password = request.form.get('confirm_new_password', '')
    
    if len(new_password) < MIN_PASSWORD_LENGTH:
        flash(f"New password must be at least {MIN_PASSWORD_LENGTH} characters.", "error")
        return render_template('reset_pass.html', token=token)
    
    if new_password != confirm_new_password:
        flash("New passwords do not match.", "error")
        return render_template('reset_pass.html', token=token)
    
    # Save the hashed password, then delete the used token so it cannot be reused.
    update_password_hash(reset["user_id"], generate_password_hash(new_password))
    delete_reset_token(reset["id"])
    flash("Your password has been reset successfully.", "success")
    return redirect(url_for('login'))


# --------------- LAB 3 FUNCTIONS --------------- # 

# calls function in database.py to return lists user belongs to
@app.route("/lists")
@login_required
def lists():
    personal, _ = get_lists_for_user(session["user_id"])
    return redirect(url_for("view_list", list_id=personal[0]["id"]))

@app.route("/lists", methods=["POST"])
@login_required
def create_list_route():
    name = request.form.get("name", "").strip()

    if not name or len(name) > 100:
        abort(400)

    list_id = create_shared_list(session["user_id"], name)
    return redirect(url_for("show_list", list_id=list_id))

@app.route("/lists/<int:list_id>")
@login_required
def show_list(list_id):
    uid = session["user_id"]

    if not is_member(list_id, uid):
        abort(404)

    current_list = get_list_details(list_id)
    personal, shared = get_lists_for_user(uid)
    tasks = get_all_tasks(uid, list_id)
    members = get_members(list_id)
    stats = get_task_stats(uid, list_id)

    return render_template(
        "index.html",
        current_list=current_list,
        personal=personal,
        shared=shared,
        tasks=tasks,
        members=members,
        stats=stats,
        is_owner=(current_list["owner_id"] == uid),
    )
if __name__ == '__main__':
    app.run(debug=True)   