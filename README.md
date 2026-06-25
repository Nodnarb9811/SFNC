# SSFNC — Daily TryBooking ticket-sales report

A small automation that runs **once a day**, asks the TryBooking API how many
tickets each event has sold, works out **how many more were sold since
yesterday**, and **emails the summary to `shop@ssfnc.com.au`**.

```
Event                     Sold   +/- day
-------------------------------------------
Season Launch              240       +18
Annual Gala Dinner         184       +12
Quiz & Trivia Night         92        +5
Junior Coaching Clinic      56        +0
-------------------------------------------
TOTAL                      572       +35
```

## How it works

Each run (`run_daily.py`):

1. Calls the TryBooking API (HTTP Basic auth: **Key** = username,
   **Secret Key** = password) and totals tickets sold per event.
2. Loads yesterday's saved snapshot from `state/latest.json`.
3. Builds the report — per-event sold count and the increase vs yesterday.
4. Emails it (plain-text + HTML table) to the recipient over SMTP.
5. Saves today's snapshot so tomorrow can compute the next increase.

The "increase" is derived from saved daily snapshots, so it's correct even if
the API doesn't expose per-day figures.

## Setup

```bash
cd SFNC
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
# edit .env: paste your TryBooking Key + Secret Key, and your SMTP details
```

Your credentials from the **Generate API key** dialog go in `.env`:

| Dialog field | `.env` variable        |
|--------------|------------------------|
| Key          | `TRYBOOKING_API_KEY`   |
| Secret Key   | `TRYBOOKING_SECRET`    |

`.env` is gitignored — credentials are never committed.

### Email (SMTP)

The report is sent via whatever SMTP server you configure in `.env`
(`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_SECURITY`).
For Gmail / Google Workspace use an **App Password**, not your normal password.

## Try it before going live

```bash
# Render a report from built-in sample data — no network, no email:
.venv/bin/python run_daily.py --mock

# Hit the real API and print the report, but don't email or save state:
.venv/bin/python run_daily.py --dry-run
```

## Schedule it daily (cron)

```bash
bash scripts/install_cron.sh          # runs every day at 08:00 local time
REPORT_HOUR=9 bash scripts/install_cron.sh   # or pick another hour
```

This adds a crontab entry like:

```
0 8 * * * cd /path/to/SFNC && /path/to/.venv/bin/python run_daily.py >> report.log 2>&1
```

## Tests

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

## ⚠️ One thing to confirm against the TryBooking docs

The environment this was built in couldn't reach `developer.trybooking.com`
(network policy), so the **endpoint paths and JSON field names** are based on
TryBooking's documented Basic-auth REST API and are all collected at the top of
[`trybooking/client.py`](trybooking/client.py) under `>>> VERIFY-AGAINST-DOCS`.
If a path or field name differs in your account's docs, change it there — it's
the only TryBooking-specific code. Everything else (diff, email, scheduling) is
generic and covered by tests. Run `--dry-run` once after setup to confirm the
events come back as expected.

## Security note

The Key/Secret shown in a Generate-API-key dialog are sensitive. Keep them in
`.env` only. If that pair was shared anywhere public, regenerate it in
TryBooking and update `.env`.
