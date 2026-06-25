# Setup guide (the simple, no-computer version)

This runs your daily ticket-sales email automatically in the cloud, for free.
You don't need to install anything or leave a computer on.

**Status so far:** the connection to TryBooking is set up and confirmed
working — a test run already pulled your real event sales. The only thing left
is letting it **send the email** (the two `SMTP_*` secrets below), then a test.

---

## Step 1 — ✅ Already done

The code is already on your repository's **default branch**, which is the
branch GitHub uses to run the daily schedule. So there's nothing to merge —
this step is taken care of.

*(Optional tidy-up, not required: if you'd prefer the branch to be called
`main`, you can rename it in GitHub under **Settings → General → Default
branch → the pencil/rename icon**. The automation works either way.)*

---

## Step 2 — Add your passwords as "Secrets"

Secrets are a safe place on GitHub to store passwords. They're hidden and never
shown in the code.

1. Go to your repository on **github.com**.
2. Click **Settings** (top menu).
3. In the left menu click **Secrets and variables → Actions**.
4. Click the green **New repository secret** button and add each of these four,
   one at a time (Name on top, Value below, then **Add secret**):

   | Name (type exactly)   | Value to paste                                        |
   |-----------------------|-------------------------------------------------------|
   | `TRYBOOKING_API_KEY`  | the **Key** from TryBooking — ✅ already added & working |
   | `TRYBOOKING_SECRET`   | the **Secret Key** — ✅ already added & working          |
   | `SMTP_USER`           | a Microsoft 365 email address that's allowed to send (e.g. reports@ssfnc.com.au) |
   | `SMTP_PASSWORD`       | that mailbox's password (or App Password — see below) |

So really you only need to add the bottom two (`SMTP_USER`, `SMTP_PASSWORD`).

---

## Step 3 — Test it with one click

1. On your repository, click the **Actions** tab (top menu).
2. Click **Daily TryBooking ticket-sales report** on the left.
3. Click the **Run workflow** button on the right, then **Run workflow** again.
4. Wait about a minute. A green tick means it ran; check shop@ssfnc.com.au for
   the email.

After this test, it will run **by itself every morning** — you don't touch it
again.

---

## About the Microsoft 365 email

For Microsoft 365 to let the report send email, two things usually need an
IT/admin to switch on (one-time):

1. **Authenticated SMTP** turned on for the sending mailbox.
2. If that mailbox uses multi-factor login (a code/app to sign in), create an
   **App Password** for it and use that as `SMTP_PASSWORD`.

If sending doesn't work, this is almost always why — send the error to Claude
and it'll tell you exactly what to flick on, or switch the email method to
Microsoft's newer system that avoids this.

---

## A quick safety note

Your TryBooking Key and Secret are like a password. They've been typed into
chat a few times, so once everything works it's worth clicking **regenerate**
in TryBooking and updating the two secrets above with the new values.
