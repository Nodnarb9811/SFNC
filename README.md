# SSFNC — Daily TryBooking ticket-sales report

A small automation that runs **once a day**, asks the TryBooking API how many
tickets each event has sold, works out **how many more were sold since
yesterday**, and **emails the summary to `shop@ssfnc.com.au`**.

> **Just want it working with no fuss?** Follow [`SETUP.md`](SETUP.md) — it runs
> free in the cloud (GitHub Actions), no computer required. The rest of this
> file is the technical detail / how to run it on your own server instead.

```
Event                                       Sold (12mo)   +/- day
-----------------------------------------------------------------
2025 Sorrento Sharks Presentation Night             143        +6
Ladies Day 2026                                      77        +4
Red & White Night                                    15        +1
-----------------------------------------------------------------
TOTAL                                               235       +11
```

## How it works

Each run (`run_daily.py`):

1. Calls the TryBooking **Reporting API** Event Sales Report
   (`GET /reporting/v1/sales/event`, HTTP Basic auth: **Key** = username,
   **Secret Key** = password), with `datePeriod=1` (daily breakdown).
2. Because the API caps a single request at ~3 months, it fetches the last 12
   months in ~80-day chunks and concatenates them.
3. For each event it computes tickets sold over the last 12 months
   (`totalSold`) and the tickets sold on the previous day — that day's figure
   *is* the day-over-day increase.
4. Emails a plain-text + HTML table to the recipient over SMTP.

The increase comes straight from the API's per-day figures, so no local state
is needed between runs.

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

### Email (Microsoft 365)

`.env.example` is preconfigured for Microsoft 365:

```
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_SECURITY=tls
SMTP_USER=<a real, licensed M365 mailbox>
SMTP_PASSWORD=<that mailbox's password or App Password>
REPORT_FROM=<the same mailbox, or a shared mailbox it can "Send As">
```

Two M365 requirements to be aware of (both set by an IT/tenant admin):

1. **SMTP AUTH must be enabled** for the sending mailbox. Microsoft disables
   it by default on many tenants. Enable it in the Microsoft 365 admin centre:
   *Users → the mailbox → Mail → Manage email apps → tick "Authenticated SMTP"*,
   or via PowerShell:
   `Set-CASMailbox -Identity reports@ssfnc.com.au -SmtpClientAuthenticationDisabled $false`
2. **If the mailbox uses MFA**, a normal password won't work for SMTP — create
   an **App Password** for it and use that as `SMTP_PASSWORD`.

If your tenant blocks Authenticated SMTP entirely, the alternative is sending
via Microsoft Graph (OAuth) — tell me and I'll add a Graph sender.

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

## TryBooking API — verified

The client is wired against the live TryBooking Reporting API
(`https://api.trybooking.com`, spec at `/swagger/v1/swagger.json`) and has been
confirmed working end-to-end against the real account: `--dry-run` returns the
event sales table with live figures. Endpoint constants live at the top of
[`trybooking/client.py`](trybooking/client.py).

## Security note

The Key/Secret shown in a Generate-API-key dialog are sensitive. Keep them in
`.env` only. If that pair was shared anywhere public, regenerate it in
TryBooking and update `.env`.
