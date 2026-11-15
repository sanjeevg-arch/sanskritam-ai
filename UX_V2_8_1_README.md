# Sanskritam AI v2.8.1 — Personalized Home & Simplified Navigation

Built on the supplied v2.8 Sanskrit for Beginners project. The main navigation is **Home · Learn · Translate · Practice**.

## Changes
- `app.py`: groups the existing feature modules into four destinations; retains authentication, sign-out, accessibility controls, translation, image and voice transcription, history, corrections, and existing admin guard.
- `home_ux.py` (new): lightweight home page with Continue Learning, progress indicator, and Translate/Practice shortcuts.
- `tests/test_home_ux.py` (new): lesson-selection tests.

No new Python dependencies or Supabase migrations. Existing v2.8 `sanskrit_beginners_setup.sql` is still required if it hasn't been run.

## Deploy
1. Back up the working GitHub repository.
2. Extract the ZIP. Upload **root-level** `app.py` and new `home_ux.py` together. Keep all other existing files (or upload the complete package).
3. Keep Streamlit Cloud on **Python 3.12**. Do not upload secrets.
4. Redeploy and test OTP login, Home → Learn → lesson completion, Translate (including image/voice), Practice, history, admin visibility, and sign-out.

## Known limitations
- The home page uses existing session-based starting-level preference. It does not persist the preferred starting level across devices.
- The Continue Learning button selects the next incomplete lesson, but the lesson content still uses the original v2.8 expander UI (v2.8.2 is intended for step-by-step lessons).
- The home page makes a read-only Supabase progress request. If the v2.8 table is unavailable, it shows a notice instead of blocking navigation.
- Source checks and local tests are not equivalent to live Streamlit/Supabase integration testing.
