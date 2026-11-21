# LOST: Never lose your way in learning

Student app (focus timer, calendar, notes, goals, and the **I AM LOST!** catch-up button).

```
hackathon/
  frontend/app.html        the whole front (HTML + JS), served by the backend
  backend/
    app/                   FastAPI code (main, models, routes/, security, ai)
    tests/                 automated tests (pytest)
    requirements.txt
    .env.example           copy to .env (never commit .env)
```

## Run it on your PC

Use a terminal in the repo root (VS Code: Terminal > New Terminal). Python 3.10+.

**Windows (PowerShell)**
```powershell
python -m venv venv            # skip if the venv folder already exists
venv\Scripts\activate          # if blocked: Set-ExecutionPolicy -Scope Process RemoteSigned
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
cd backend
uvicorn app.main:app --reload
```

**macOS / Linux**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cd backend && uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** (not the file directly, not Live Server: the page and API must share one address).
API documentation: http://127.0.0.1:8000/docs

Edit `backend/.env`, set `SECRET_KEY` to the output of
`python -c "import secrets; print(secrets.token_urlsafe(48))"`.

Run the tests (from `backend/`): `python -m pytest`

The database is the file `backend/lost.db`, created on first start. To reset it, stop the server and delete the file.
Each teammate has their own local database.

## How it works

- The front keeps data in memory. When something changes it sends the whole collection to the API
  (`PUT /api/notes` means "make the server match this list"). On login it loads everything with `GET /api/bootstrap`.
- Login uses a signed, `httpOnly` cookie. Passwords are hashed with PBKDF2 (200k iterations).
- Every table row carries `user_id`; every query filters on it, so students only see their own data.

| Endpoint | What |
|---|---|
| `POST /api/auth/signup` `login` `guest` `logout` | accounts and session |
| `GET /api/bootstrap` | all data of the signed-in student |
| `PUT /api/subjects` `notes` `events` `goals` `focus` | save a collection |
| `PATCH /api/me/prefs` | name, theme, default format, timer, meet link |
| `DELETE /api/me` | delete account and all data |
| `POST /api/lost` | the big button (sample content until audio capture exists) |
| `DELETE /api/summaries[/{id}]` | history |

## Not built yet
Google login, DOCX / Google Docs export, real audio capture (the Gemini path in `backend/app/ai.py` is written but untested),
database migrations (change a model => delete `lost.db`), email verification.

## Push to GitHub
See the commands in the chat answer / `git status`, `git add`, `git commit`, `git push`.
Never commit: `venv/`, `.env`, `*.db`.
