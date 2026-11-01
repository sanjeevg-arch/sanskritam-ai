# Sanskritam AI v2.5 — Accuracy & Correction Workflow

## Deploy
1. Back up the current GitHub repository.
2. Run `corrections_setup.sql` in the Supabase SQL Editor. Keep previous migrations and tables.
3. Copy all application files into your repo, including `corrections.py` and updated `app.py`.
4. In Streamlit Cloud Secrets, add the comma-separated email list of reviewers:
   `CORRECTIONS_ADMIN_EMAILS = "your-admin@example.com"`
   This email must be an approved, authenticated beta account.
5. Commit and redeploy.

## Workflow
- An authenticated learner translates or reopens a saved passage, then opens **Translation Accuracy & Corrections**.
- They choose a category, optionally choose a word, and submit a proposed correction.
- Their submissions are stored in Supabase and visible under **My recent reports**.
- Approved administrators see **Correction Review · Admin**, inspect pending reports, and approve, reject, or request information.
- Approval **does not** automatically replace AI output. Human-reviewed corrections can be incorporated into a curated dictionary or future prompt revision in a subsequent release.
- Submitting/reviewing corrections uses **zero OpenAI API requests**.

## Security / limitations
- `SUPABASE_SERVICE_ROLE_KEY` must remain in Streamlit server-side Secrets only.
- Admin access is determined from `CORRECTIONS_ADMIN_EMAILS` on the server, not from a user-editable widget.
- All user-specific reads are filtered by the verified Supabase user ID.
- The migration revokes direct table privileges for anonymous/authenticated API clients; app access is through server-side service role.
- This version does not include notifications, dispute resolution, or a curated-correction publishing engine.
- Avoid entering personal or sensitive information in correction reports.

## Smoke tests
1. Submit a correction from beta account A. Confirm it appears under A's reports.
2. Sign in as account B. Confirm A's report is not shown.
3. Sign in as the admin. Confirm pending report appears, then approve it.
4. Sign in as A. Confirm updated status and reviewer note.
5. Verify translation quotas do not change from these actions.
