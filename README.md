# Pastebin Lite

A simple Pastebin-like application built with Flask and PostgreSQL.

## Features
- Create text pastes
- Shareable URLs
- Optional TTL and max view limits
- HTML view and JSON API

## Tech Stack
- Python (Flask)
- PostgreSQL
- HTML/CSS

## Persistence
PostgreSQL database hosted on Render.

## Run Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@host/db
flask run
