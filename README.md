# Django POS Backend

Versioned API backend for the POS project.

## API Docs

- Full reference: docs/API_V1_REFERENCE.md
- Runnable examples: docs/api_examples.ps1

## Environment Configuration

- Copy values from .env.example into your environment manager of choice.
- Minimum required variables for local run are the PostgreSQL variables.
- For frontend integration, set CORS and CSRF origins explicitly.

Important security variables:

- DJANGO_SECRET_KEY
- DJANGO_DEBUG
- DJANGO_ALLOWED_HOSTS
- DJANGO_CORS_ALLOWED_ORIGINS
- DJANGO_CSRF_TRUSTED_ORIGINS
- JWT_ACCESS_MINUTES
- JWT_REFRESH_DAYS

Email variables:

- EMAIL_BACKEND
- EMAIL_HOST
- EMAIL_PORT
- EMAIL_USE_TLS
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- DEFAULT_FROM_EMAIL
- SUPPORT_EMAIL
- APP_NAME
- FRONTEND_URL
- PASSWORD_RESET_URL_TEMPLATE

## Password Reset Email Deliverability

To avoid password reset emails landing in spam, use a verified sender domain and authenticated SMTP account.

1. Set DEFAULT_FROM_EMAIL to the same domain/account used by your SMTP provider.
2. Add DNS records for your sending domain: SPF, DKIM, and DMARC.
3. Use a production email service (SES, SendGrid, Mailgun, Postmark, etc.) or properly configured business SMTP.
4. Avoid free mailbox aliases in production (for example mismatching Gmail SMTP with an unrelated from-domain).
5. Keep APP_NAME and SUPPORT_EMAIL set so recipients see recognizable sender details.

Reset-link reachability:

1. Set FRONTEND_URL to the actual frontend host users can open (not localhost in production).
2. Optionally set PASSWORD_RESET_URL_TEMPLATE for full control, for example:
   PASSWORD_RESET_URL_TEMPLATE=https://pos.example.com/reset-password.html?token={token}
3. If PASSWORD_RESET_URL_TEMPLATE is empty, backend uses request Origin first, then FRONTEND_URL.

## Quick Start

1. Set database environment variables in PowerShell:

```powershell
$env:DB_NAME='Django_Project'
$env:DB_USER='postgres'
$env:DB_PASSWORD='1234'
$env:DB_HOST='localhost'
$env:DB_PORT='5432'
```

2. Run migrations:

```powershell
pipenv run python manage.py migrate
```

3. Start server:

```powershell
pipenv run python manage.py runserver
```

4. Obtain token:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/auth/token/" -ContentType "application/json" -Body (@{ username = "admin"; password = "Admin@12345" } | ConvertTo-Json)
```

## Hosting

- Render blueprint file: [render.yaml](../render.yaml)
- Backend process file: [Procfile](Procfile)
- Step-by-step guide: [docs/HOSTING_GUIDE.md](docs/HOSTING_GUIDE.md)
