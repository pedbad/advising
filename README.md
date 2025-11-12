# Advising Platform

![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![Tailwind](https://img.shields.io/badge/tailwind-4.1-blueviolet)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A multi-role advising portal that joins Django 5.2, Tailwind CSS 4, and the `django-tailwind`/ShadCN-inspired component kit. Students, advisors/teachers, and admins share one codebase while seeing role-aware dashboards, navigation, and tooling.

---

## Feature Highlights

- **Role-aware authentication & dashboards** – Central `users` app drives login, post-auth redirects, and landing pages per role (student/advisor/admin).
- **Availability & booking workflow** – Advisors publish availability slots, students book them, and everyone can review bookings or filter upcoming sessions.
- **Notes & threaded comments** – Advisors/admins and students collaborate on student-specific note threads with modal-driven create/edit/comment flows and role-specific theming.
- **Notifications with ICS attachments** – The `notifications` app emits personalized emails (student/advisor/admin) any time bookings, cancellations, notes, or comments occur. Booking confirmations attach downloadable `.ics` calendar files and also surface download buttons in teacher dashboards.
- **Questionnaire + profile gating** – Optional student questionnaire flow, profile management, and controlled access to booking until onboarding steps complete.
- **Tailwind + ShadCN UI system** – Shared components, icons, and theme-aware palettes ensure consistent styling across marketing pages and dashboards (light/dark aware).
- **Navigation UX polish** – Role-sensitive nav links, responsive menus, and CTA “cards” keep important actions easy to reach (notes, booking, availability, etc.).
- **Developer-friendly email previews** – All outbound emails land in `tmp_emails/` via Django’s console backend for quick inspection.

---

## Quickstart for New Contributors

The steps below assume macOS/Linux. Windows commands are provided where they differ.

### 0. Prerequisites

- Python **3.13** (match the version in `.python-version`/Pyenv if you use it)
- Node.js **20+** and npm (ships with node)
- Git, Make (optional), and a working C compiler (for some pip wheels)

### 1. Clone the repository

```bash
git clone https://github.com/pedbad/advising.git
cd advising
```

### 2. Create & activate a virtual environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# or on Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

Keep the venv active for all subsequent Python commands.

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

> `requirements.txt` is the minimal runtime set. `requirements-dev.txt` includes pytest, Ruff, etc.

### 4. Configure environment variables

```bash
cp .env.example .env
python check_env.py
```

Update `.env` with database credentials, email settings, etc., as needed. `check_env.py` warns if required keys are missing.

### 5. Sanity-check Django

```bash
python src/manage.py check
```

### 6. Apply migrations

```bash
python src/manage.py makemigrations
python src/manage.py migrate
```

### 7. Create an admin user

```bash
python src/manage.py createsuperuser
```

### 8. Install frontend dependencies

```bash
npm install
npm run tw:build          # one-off Tailwind build (minified)
```

For active development you can run:

```bash
npm run tw:watch          # watches Tailwind input.css → output.css
# or run everything together
npm run dev               # tailwind watch + Django runserver concurrently
```

### 9. Run the development server

```bash
python src/manage.py runserver
# …or, with Tailwind watcher included:
npm run dev
```

Visit http://127.0.0.1:8000/ and sign in with your superuser or seed data.

### 10. Inspect outgoing emails

- Django stores all messages in `tmp_emails/` (default EMAIL_BACKEND). Open the most recent `.eml` to review booking confirmations, note alerts, etc.
- ICS attachments are generated via `notifications/ics.py` and attached to booking-confirmation emails.

### 11. Run tests & linters

```bash
pytest -q
python src/manage.py test        # optional: Django test runner
ruff check                       # lint/format validation
```

---

## Repository Layout

```
.
├── README.md
├── package.json                # Tailwind CLI + dev scripts (watch/build/dev)
├── pyproject.toml              # Ruff / tooling configuration
├── requirements*.txt           # Runtime vs dev dependency sets
├── templates/                  # Marketing pages + shared HTML fragments
├── tmp_emails/                 # Local email backend output for inspection
└── src/
    ├── config/                 # Django settings, ASGI/WSGI entrypoints
    ├── core/                   # Base templates, Tailwind input/css, icon tags
    ├── users/                  # Auth, role redirects, dashboards, navigation
    ├── profiles/               # StudentProfile and related profile models
    ├── availability/           # Advisor availability slots, filters, listings
    ├── booking/                # Booking flows, forms, teacher/student views, ICS download endpoint
    ├── notes/                  # Student notes, threaded comments, modal forms
    ├── notifications/          # Email helpers, ICS builder, signal handlers, templates
    ├── questionnaire/          # Student onboarding questionnaire + gating logic
    └── manage.py               # Django entrypoint (exposed via src/manage.py)
```

Supporting directories:

- `data/` – fixtures or import/export helpers (if present).
- `node_modules/` – populated via `npm install` (ignored by git).
- `tmp_emails/` – inspect `.eml` files when bookings/notes trigger notifications.

---

## Additional Tips

- **Static assets** – CSS is generated into `src/core/static/core/css/output.css`. If you add new components, edit `input.css` and rerun `npm run tw:build`.
- **Icons** – Material-symbol-inspired icons live under `core/templates/core/icons/`; use `{% icon 'name' %}` after loading the custom template tag library.
- **Calendar downloads** – Teachers can download `.ics` files from upcoming bookings, and the same attachments ship with booking emails for all roles.
- **Questionnaire gating** – Toggle behavior with `FORCE_QUESTIONNAIRE_COMPLETION` in settings or `.env`.

You now have everything needed to clone, configure, and extend the advising application. Happy building!
