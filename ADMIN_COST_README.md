# AI Cost & Admin Dashboard (v2.6)

1. Run `admin_cost_setup.sql` in Supabase SQL Editor **before** deploying updated Python code. Keep all prior tables.
2. Keep `CORRECTIONS_ADMIN_EMAILS` configured with your administrator's verified Supabase email; this same allowlist gates the dashboard. Example: `CORRECTIONS_ADMIN_EMAILS = "admin@example.com"`.
3. Deploy `app.py`, `private_beta.py`, and `admin_cost_dashboard.py` together with the existing project.
4. Sign in as an administrator and open **AI Cost & Admin Dashboard** near My Learning Dashboard. Select 7, 30, or 90 days.
5. Perform a translation and refresh. Confirm the operation appears and its input/output tokens are recorded. Test that non-admin users cannot see the dashboard.

## Important limitations
- Cost estimates use configured per-million-token prices (default $0.40 input and $1.60 output for gpt-4.1-mini). These are illustrative; check current prices. OpenAI billing is authoritative.
- Voice transcription costs are **not** priced; old rows have no input/output token breakdown. Both are excluded from estimated USD and counted as unknown.
- A request can incur OpenAI cost even when parsing fails or the application marks it failed; these costs cannot always be recovered from the existing API flow.
- Images may have special billing/token accounting; image costs are approximate when usage tokens are returned.
- Metrics come from the `beta_requests` table, not from OpenAI's billing API. 20,000-row retrieval cap, with an on-screen warning if reached.
- UTC dates; report filters use request creation time, whereas usage_day is the UTC quota day.
- The service role key stays server-side. Never commit secrets to Git or expose usage data to non-admin users.
- Dashboard is **read-only**. It does not alter quota rules or enforce a monetary budget.
