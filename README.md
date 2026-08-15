# Fieldnotes — a minimal blog CMS

A small content-management system for a developer's blog, built with Flask
and SQLite. Write posts in Markdown, publish or save as a draft, and manage
everything from a lightweight admin dashboard — no external CMS, no build
step.

**Live demo:** _add your deployed link here_

## Features

- Public blog with post list, individual post pages, and tag filtering
- Markdown authoring with fenced code block support and syntax-friendly styling
- Admin dashboard: create, edit, publish/unpublish, and delete posts
- Session-based authentication (Flask-Login) protecting all admin routes
- Reading-time estimate and a scroll-based reading progress indicator
- Copy-to-clipboard buttons on code blocks
- Fully responsive, hand-styled UI (no CSS framework)

## Tech stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login
- **Database:** SQLite
- **Templating:** Jinja2
- **Content:** Markdown (`python-markdown`)
- **Frontend:** hand-written HTML/CSS/JS, no framework

## Getting started

```bash
git clone https://github.com/<your-username>/fieldnotes-cms.git
cd fieldnotes-cms

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`. The app seeds an admin account and three demo
posts on first run.

**Demo admin login:** `admin` / `changeme123`
(change this before deploying anywhere public — see below)

## Project structure

```
fieldnotes-cms/
├── app.py                 # routes, models, auth, seed data
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── post_detail.html
│   ├── login.html
│   ├── dashboard.html
│   └── post_form.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Deploying

This app has no external service dependencies beyond Python, so it deploys
cleanly to Render, Railway, PythonAnywhere, or Fly.io free tiers. Before
deploying:

1. Set a real `SECRET_KEY` environment variable.
2. Change the seeded admin password, or delete the seed and create your own
   admin user via a one-off script.
3. SQLite is fine for a personal blog's traffic; if you outgrow it, swap the
   `SQLALCHEMY_DATABASE_URI` for Postgres.

## What I'd improve next

- Image uploads for post covers
- Full-text search across posts
- RSS feed
- Comment system (or a link out to a discussion thread)
