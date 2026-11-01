# Sanskritam AI v2.7.1 — Security & Stability Patch

## Changes
- Sign-out now requests Supabase Auth `/auth/v1/logout` for the active token (best effort), then clears **all** Streamlit session state. This avoids carrying results, transcripts, widgets or learning state into a different account.
- When a token becomes invalid or an invitation is revoked, account state is cleared before returning to the login gate.
- Admin cost report data fetching requires an administrator user argument, rather than relying only on the rendering function to check permissions.
- Supabase HTTP calls use separate connect/read timeouts.
- Added unit tests for account-state clearing, sign-out failure handling and admin usage authorization.

## Important limitations and follow-up
- **Service-role database operations remain privileged.** Existing modules still use service-role calls and application-level user-ID filtering. Do not consider this an RLS security audit. Review every RPC's `SECURITY DEFINER` grants and every table policy in Supabase, and test cross-user access before public launch.
- Supabase sign-out invalidates refresh tokens, but already-issued JWT access tokens may remain valid until expiration. Do not treat logout as instant JWT revocation.
- This patch does not add a new admin-role schema, database-side cost aggregation, or guaranteed token accounting when an AI response fails to parse. Those require more extensive code/database changes.
- No live Supabase or OpenAI integration tests were performed. Test in staging with separate accounts and a non-production API quota.
- Keep `.streamlit/secrets.toml`, `.env`, API keys, and service-role keys out of Git.

## Deployment
1. Back up the current GitHub repo and Supabase database.
2. Replace project files with this package, preserving your existing Streamlit secrets.
3. Run `python -m unittest discover -s tests -v` and `python -m compileall -q .`.
4. In staging, verify OTP, sign-out/sign-in as a different user, invite revocation, user-owned history, flashcards, grammar attempts, corrections and admin-only dashboard.
5. Deploy to private beta first. No database migration is required by the changes in this patch.
