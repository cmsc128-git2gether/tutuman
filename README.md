# Tutuman - Todo App

A multi-user todo web app for organizing, tracking, and categorizing tasks. Each person registers, logs in, and manages their own private task list.

**Authors:** Cambel (@ed-cambel), Gelvezon (@thoenii)

## Features

- **Account registration and login:** sign up with email, display name, and password. After login, the user goes straight to their To-Do List.
- **Task management:** create, edit, complete, delete, and restore tasks, organized by due date, priority, and tag, with list/calendar views and status filters. Deletes are soft deletes with an undo toast.
- **Private task list (UBAC):** every task belongs to one user, and the backend only lets that user read or change it.
- **Profile management:** profile page with account details and task stats; edit display name, change password, or delete the account.
- **Secure credentials:** passwords are stored as hashes, never as plain text.
- **Persistent sessions:** users stay logged in across refreshes, back navigation, and server restarts, and pages are protected when signed out.
- **Password recovery:** reset links are emailed to the registered address.

## Tech stack

| Layer          | Choice                                                                                                                              | Why                                                                                              |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Frontend       | Server-rendered Jinja2 templates, plain HTML, CSS, and vanilla JavaScript. Bootstrap Icons and the DM Sans font load from CDNs      | No build step; state is driven by URL/query params, and `fetch()` covers modals and delete/undo. |
| Backend        | Python 3 with Flask                                                                                                                 | Minimal boilerplate for a CRUD app, with Jinja built in.                                         |
| Database       | MySQL (XAMPP / MariaDB) via `mysql-connector-python` and parameterized queries                                                      | Needed for a multi-user app with foreign keys. Replaces the SQLite database used in Activity 1.  |
| Authentication | Session-based login. Passwords hashed with Werkzeug (`generate_password_hash` / `check_password_hash`). Sessions are signed cookies | Reused unchanged from Activity 2.                                                                |
| Testing        | pytest with Flask's test client                                                                                                     | Exercises routes, including cross-user access attempts.                                          |

## How Activity 1 and Activity 2 were merged

- **Branches:**
- **Strategy:**
- **Conflicts resolved:**
  -

## Project structure

```
todo-app/
├── app.py            # Flask app and all routes
├── database.py       # MySQL connection and every database operation
├── schema.sql        # Table definitions
├── .env              # Local secrets (not committed)
├── .env.example      # Names of the required variables
├── templates/        # index, login, register, profile
├── static/
│   ├── css/
│   └── js/
└── tests/            # pytest tests
```

## Installation and local run

**Requirements:** Python 3.10+, XAMPP (for MySQL), and a browser.

1. **Clone the repository**, check out the branch, and open the project folder:

```bash
   git clone <repo-url>
   cd <repo-folder>
   git checkout act3-ubac
```

2. **Create and activate a virtual environment** (recommended):

```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
```

3. **Install the dependencies:**

```bash
   python -m pip install flask mysql-connector-python python-dotenv
```

For the tests, also run `python -m pip install pytest`.

4. **Create a `.env` file** next to `app.py`:

```
   MYSQL_PASSWORD=
   SECRET_KEY=your-long-random-string
```

- Leave `MYSQL_PASSWORD` empty if your XAMPP MySQL has no password (the default).
- Generate a secret key with:

```bash
     python -c "import secrets; print(secrets.token_hex(32))"
```

- `.env` is listed in `.gitignore`. Never commit it.

5. **Set up the database** (see the next section).
6. **Start MySQL** in the XAMPP Control Panel.
7. **Run the app:**

```bash
   python app.py
```

Open **http://127.0.0.1:5000**. You'll be sent to the login page.

To run the tests (MySQL must be running):

```bash
python -m pytest -v
```

The tests create accounts with the email domain `@test.invalid` and delete them before and after each test.

## Database setup

1. Start **MySQL** (and Apache, if you want phpMyAdmin) in XAMPP.
2. Open `http://localhost/phpmyadmin` and create a database named **`todo_app`**.
3. Select `todo_app`, open the **Import** tab (or the **SQL** tab), and run `schema.sql`.
   > `schema.sql` starts with `DROP TABLE IF EXISTS`, so running it again deletes all existing accounts and tasks.

The connection settings (host `localhost`, user `root`, database `todo_app`) are in `DB_CONFIG` in `database.py`. The password comes from `.env`.

## Schema

Users and tasks are stored in separate tables. Each task references its owner through `user_id`, so no user data is duplicated inside task records.

```
users (1) ────< tasks (many)
  id  <──────── user_id (FK, ON DELETE CASCADE)
```

| Table   | Columns                                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `users` | `id` (PK), `email` (unique), `display_name`, `password_hash`, `created_at`                                                                             |
| `tasks` | `id` (PK), `user_id` (FK to `users.id`, `ON DELETE CASCADE`), `title`, `due_date`, `due_time`, `priority`, `tag`, `completed`, `deleted`, `created_at` |

`priority` is one of `Low`, `Med`, `High`; `tag` is one of `School`, `Personal`, `Others`. Deletes set the `deleted` flag instead of removing the row, so a task can be restored from the undo toast.

## Routes and ownership checks

**Authentication and account**

| Method    | Route               | Description                                                     | Auth |
| --------- | ------------------- | --------------------------------------------------------------- | ---- |
| GET       | `/`                 | Redirects to `/tasks` if logged in, otherwise `/login`          | No   |
| GET, POST | `/register`         | Show the form; validate, hash the password, and create the user | No   |
| GET, POST | `/login`            | Verify the password hash, start a session, go to the To-Do List | No   |
| POST      | `/logout`           | Clear the session                                               | Yes  |
| GET       | `/profile`          | Greeting, account details, and activity counts                  | Yes  |
| POST      | `/profile/edit`     | Update the display name                                         | Yes  |
| POST      | `/profile/password` | Change the password (needs the current password)                | Yes  |
| POST      | `/profile/delete`   | Delete the account and its tasks                                | Yes  |

**Tasks** (all require login and only touch the current user's tasks)

| Method | Route            | Description                                                    |
| ------ | ---------------- | -------------------------------------------------------------- |
| GET    | `/tasks`         | List tasks. Query parameters: `tab`, `view`, `priority`, `tag` |
| POST   | `/add`           | Create a task                                                  |
| POST   | `/edit/<id>`     | Update a task                                                  |
| POST   | `/complete/<id>` | Toggle completed                                               |
| POST   | `/delete/<id>`   | Soft delete a task                                             |
| POST   | `/restore/<id>`  | Restore a soft-deleted task                                    |

**How ownership is checked**

- The task owner always comes from `session["user_id"]`, never from the request body or URL. `/add` stores the session's user ID as `user_id`.
- Every task function in `database.py` takes a `user_id` and includes it in its `WHERE` clause, for example `WHERE id = %s AND user_id = %s`.
- Example: if User A sends `POST /delete/42` and task 42 belongs to User B, the query matches no row, nothing changes, and the server responds with `[404 / 403 - confirm]`. User B's data is never returned.
- Task lists are filtered with `WHERE user_id = <session user>`.
- All queries use `%s` placeholders to prevent SQL injection.

**Database operations** (`database.py`)

- Users: `create_user`, `get_user_by_email`, `get_user_by_id`, `update_display_name`, `update_password_hash`, `delete_user`
- Tasks: `add_task`, `get_task`, `get_all_tasks`, `update_task`, `delete_task`, `restore_task`, `toggle_task`, `get_task_stats`

## Session mechanism

- **Storage:** Flask's `session` is a cookie in the browser holding the user's ID. It is signed with `SECRET_KEY`, so it can't be changed without the key. The server stores no session data, which is why restarting the server doesn't log anyone out.
- **Login:** after the password hash is verified, the session is cleared (to discard any older session), the user's ID is stored, and `session.permanent = True` is set.
- **Persistence:** permanent sessions expire after **7 days** (`app.permanent_session_lifetime`), counted from the user's last request, so the login survives refreshes, back navigation, and browser restarts.
- **Route protection:** a `login_required` decorator redirects to `/login` when there is no user ID in the session. It is applied to the profile and all task routes, and `/login` and `/register` redirect logged-in users away.
- **Logout:** a POST request clears the session and returns to `/login`.
- **Expiry:** the session also ends if the user clears their cookies, if `SECRET_KEY` changes, or after 7 days without a visit.

## Password hashing

Passwords are hashed with Werkzeug's `generate_password_hash`, which adds a random salt (scrypt or pbkdf2, depending on the installed version). The plain password is never stored or logged. Login compares the entered password with the stored hash using `check_password_hash`. The failure message is the same for an unknown email and a wrong password.

## Password recovery

Reset tokens are stored in the database as SHA-256 hashes, not as the original tokens. The reset link containing the original token is sent to the user's registered email through SMTP and expires after 30 minutes. After verification, the user sets a new password, which is hashed with Werkzeug's `generate_password_hash`. The used token is deleted with `delete_reset_token` to prevent reuse. If SMTP is not configured or sending fails, the reset link is printed in the terminal for local testing.

## Screenshots

<img width="1917" height="927" alt="task-list" src="https://github.com/user-attachments/assets/73646e9d-b627-434b-86ba-63bc7ca988f1" />
<img width="1917" height="926" alt="undo-toast" src="https://github.com/user-attachments/assets/066239e3-2e13-47f3-a506-2d05ee686e7e" />
<img width="1917" height="930" alt="new-task-modal" src="https://github.com/user-attachments/assets/19007602-424b-4e4a-9618-8fdb7b240421" />
<img width="1917" height="923" alt="delete-confirm" src="https://github.com/user-attachments/assets/03eb2f5e-b4a2-4bff-b981-d9d9dfd59197" />
