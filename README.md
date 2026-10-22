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

- **Branches:** During Activity 2, branches `act-feat/crud-<lastname>` and `act-feat/auth-<lastname>` were already merged to form a working UBAC. Along with this merge, the minimum requirements were met.
- **Strategy:** Each partner was assigned specific features and coded them in their own branch for Activity 2. Once a feature was done, its branch was merged into `main`, so `main` always holds the working copy of the project.
- **Conflicts resolved:**
  1.  Function parameters (`database.py`, `app.py`): adding the `users`, `lists`, `list_members`, and `password_resets` tables, and the `user_id` and `list_id` columns on `tasks`, meant existing functions needed extra parameters. For example, task functions that took only a `task_id` now also take the logged-in user's ID, read from `session["user_id"]` in the route, so the backend can check ownership or list membership.
  2.  Routes (`app.py`): the task routes were updated to require login, pass the session user to the database functions.
  3.  SQLite to MySQL migration: Activity 1 used SQLite, so database functions and queries were rewritten for MySQL (`%s` placeholders, MySQL types). The seeder (`seed.py`) also had to be updated, because it was missing arguments for the new schema fields (`user_id`) and failed with incomplete inserts.

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

## Schema

Users, lists and tasks are stored in separate tables. A list belongs to one owner, users join lists through a membership table, and each task references the list it lives in and the user who created it, so no user data is duplicated inside list or task records.

```
users (1) ────< lists (many)          owner
  id  <──────── owner_id (FK, ON DELETE CASCADE)

users (many) >────< lists (many)      membership
  id  <──────── list_members.user_id (FK, ON DELETE CASCADE)
                list_members.list_id (FK, ON DELETE CASCADE) ────> lists.id

lists (1) ────< tasks (many)
  id  <──────── list_id (FK, ON DELETE CASCADE)

users (1) ────< tasks (many)          creator
  id  <──────── user_id (FK, ON DELETE CASCADE)
```

| Table        | Columns                                                                                                                                                                     |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| users        | id (PK), email (unique), display_name, password_hash, created_at                                                                                                            |
| lists        | id (PK), name, owner_id (FK to users.id, ON DELETE CASCADE), is_personal, created_at                                                                                        |
| list_members | list_id (PK, FK to lists.id, ON DELETE CASCADE), user_id (PK, FK to users.id, ON DELETE CASCADE), joined_at                                                                 |
| tasks        | id (PK), list_id (FK to lists.id, ON DELETE CASCADE), user_id (FK to users.id, ON DELETE CASCADE), title, due_date, due_time, priority, tag, completed, deleted, created_at |

### Relationships

- A user owns many lists (`lists.owner_id`). Registration creates one personal list (`is_personal = 1`) and adds the user to it.
- Users and lists are many-to-many through list_members. Every list has at least its owner as a member.
- A list has many tasks (`tasks.list_id`). `tasks.user_id` records who created the task. It does not control who can see it.

## Access control

Every query is scoped by the logged-in user's id from the session, never by an id sent from the client alone.

| Role    | Determined by                    | Can                                        |
| ------- | -------------------------------- | ------------------------------------------ |
| Member  | row in `list_members`            | view the list, add and complete tasks      |
| Owner   | `lists.owner_id` equals the user | invite and remove members, delete the list |
| Creator | `tasks.user_id` equals the user  | edit and delete that task                  |

| Operation                                          | Ownership check                                                                            | On failure            |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------- |
| `GET /lists/<id>`                                  | `is_member(list_id, uid)`                                                                  | 404                   |
| `POST /add`                                        | insert runs as `INSERT ... SELECT ... FROM list_members WHERE list_id = ? AND user_id = ?` | 404 (0 rows inserted) |
| `POST /toggle/<task_id>`                           | `UPDATE ... JOIN list_members` and `t.user_id = ?`                                         | no rows changed       |
| `POST /update/<task_id>`, `POST /delete/<task_id>` | same as toggle                                                                             | no rows changed       |
| `POST /lists/<id>/members`                         | member, then owner, then not personal                                                      | 404, 403, 400         |
| delete list                                        | `WHERE id = ? AND owner_id = ? AND is_personal = 0`                                        | 0 rows deleted        |
| remove member                                      | `l.owner_id = ? AND m.user_id <> l.owner_id`                                               | 0 rows deleted        |

Non-members receive 404 instead of 403 so list ids cannot be probed.

```python
@app.route("/lists/<int:list_id>/members", methods=["POST"])
@login_required
def add_list_member(list_id):
    uid = session["user_id"]
    lst = get_list_details(list_id)

    if lst is None or not is_member(list_id, uid):
        abort(404)   # hide the list from non-members
    if lst["owner_id"] != uid:
        abort(403)   # members can view, only the owner can invite
    if lst["is_personal"]:
        abort(400)   # personal lists can't be shared
    ...
```

## Routes and ownership checks

**Authentication and account**

| Method    | Route               | Description                                                                   | Auth |
| --------- | ------------------- | ----------------------------------------------------------------------------- | ---- |
| GET       | `/`                 | Redirects to the personal list if logged in, otherwise `/login`               | No   |
| GET, POST | `/register`         | Show the form; validate, hash the password, create the user and personal list | No   |
| GET, POST | `/login`            | Verify the password hash, start a session, go to the personal list            | No   |
| POST      | `/logout`           | Clear the session                                                             | Yes  |
| GET       | `/profile`          | Greeting, account details, and activity counts across all lists               | Yes  |
| POST      | `/profile/edit`     | Update the display name                                                       | Yes  |
| POST      | `/profile/password` | Change the password (needs the current password)                              | Yes  |
| POST      | `/profile/delete`   | Delete the account, its owned lists, and its tasks                            | Yes  |

**Lists** (all require login)

| Method | Route                 | Description                                                     | Who      |
| ------ | --------------------- | --------------------------------------------------------------- | -------- |
| GET    | `/lists/<id>`         | Show a list. Query parameters: `tab`, `view`, `priority`, `tag` | Member   |
| POST   | `/lists`              | Create a shared list; the creator becomes owner and member      | Any user |
| POST   | `/lists/<id>/members` | Invite a user by email                                          | Owner    |
| POST   | `[route]`             | Remove a member                                                 | Owner    |
| POST   | `[route]`             | Delete a shared list                                            | Owner    |

**Tasks** (all require login)

| Method | Route            | Description                                  | Who     |
| ------ | ---------------- | -------------------------------------------- | ------- |
| POST   | `/add`           | Create a task in the list given by `list_id` | Member  |
| POST   | `/edit/<id>`     | Update a task                                | Creator |
| POST   | `/complete/<id>` | Toggle completed                             | Creator |
| POST   | `/delete/<id>`   | Soft delete a task                           | Creator |
| POST   | `/restore/<id>`  | Restore a soft-deleted task                  | Creator |

**How ownership is checked**

- The acting user always comes from `session["user_id"]`, never from the request body or URL. `/add` stores the session's user ID as the task's `user_id` (creator).
- Access to a list is decided by `list_members`. `GET /lists/<id>` calls `is_member(list_id, uid)` and returns 404 for non-members, so list ids cannot be probed.
- `/add` inserts with `INSERT ... SELECT ... FROM list_members WHERE list_id = %s AND user_id = %s`, so a non-member inserts zero rows and receives 404.
- Owner-only actions compare `lists.owner_id` to the session user: inviting returns 403 for non-owners and 400 for personal lists; deleting a list and removing a member put `owner_id = %s` in the `WHERE` clause.
- Task functions in `database.py` join `list_members` and filter on the user, for example `WHERE t.id = %s AND t.user_id = %s`.
- Example: if User A sends `POST /delete/42` and task 42 was created by User B, the query matches no row, nothing changes, and the server responds with `[404 / 403 - confirm]`.
- Task lists are filtered with `WHERE t.list_id = %s AND m.user_id = <session user> AND t.deleted = 0`.
- All queries use `%s` placeholders to prevent SQL injection.

**Database operations** (`database.py`)

- Users: `create_user` (also creates the personal list and membership), `get_user_by_email`, `get_user_by_id`, `update_display_name`, `update_password_hash`, `delete_user`
- Lists: `create_shared_list`, `get_list_details`, `get_lists_for_user`, `delete_list`
- Members: `is_member`, `add_member`, `remove_member`, `get_members`, `find_user_for_invite`
- Tasks: `add_task`, `get_task`, `get_all_tasks`, `update_task`, `delete_task`, `restore_task`, `toggle_task`, `get_task_stats`, `get_profile_task_stats`

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
