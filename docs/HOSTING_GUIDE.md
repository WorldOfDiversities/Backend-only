# POS Hosting Guide

Use this guide to deploy the current project with minimal changes.

## Stage 1. Deploy backend API

1. Push your code to GitHub.
2. On Render, create a new Blueprint using the repository root.
3. Render will use [render.yaml](../render.yaml) and deploy the `pos-backend` service from [BACKEND](../).
4. In Render dashboard, set real values for these env vars on backend:
   - `DJANGO_SECRET_KEY`
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
   - `DJANGO_ALLOWED_HOSTS` to your backend domain
   - `DJANGO_CORS_ALLOWED_ORIGINS` to your frontend domain
   - `DJANGO_CSRF_TRUSTED_ORIGINS` to your frontend domain
   - `FRONTEND_URL` to your frontend domain
   - `PASSWORD_RESET_URL_TEMPLATE` to `https://your-frontend/reset-password.html?token={token}`
5. Open backend shell and run migrations:
   - `python manage.py migrate`

## Stage 2. Deploy frontend

1. Deploy [FRONTEND](../../FRONTEND/) as static site (Render static service from blueprint is already included).
2. If frontend and backend are on different domains, set API override in [FRONTEND/app-config.js](../../FRONTEND/app-config.js):
   - `window.POS_API_BASE_URL = "https://your-backend-domain/api/v1";`
3. Ensure pages load over HTTPS.

## Stage 3. Connect email and reset links

1. Configure SMTP env vars on backend.
2. Keep `DEFAULT_FROM_EMAIL` and `SUPPORT_EMAIL` as valid mailbox addresses.
3. Trigger forgot-password flow and confirm links open `reset-password.html` on frontend.

## Stage 4. Production hardening

1. Set `DJANGO_DEBUG=False`.
2. Set `DJANGO_CORS_ALLOW_ALL=False`.
3. Restrict `DJANGO_ALLOWED_HOSTS`, CORS, and CSRF to your real domains only.
4. Add SPF, DKIM, DMARC for your sender domain to improve inbox delivery.
