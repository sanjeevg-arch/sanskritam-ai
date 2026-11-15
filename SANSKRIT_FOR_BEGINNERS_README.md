# Sanskritam AI v2.8 — Sanskrit for Beginners

This release adds a new expandable **Sanskrit for Beginners** section to the existing Streamlit application, retaining v2.7.1 features.

## Included
- 18 curated beginner lessons; lessons 1–6 cover Devanagari and lessons 7–18 cover basic Sanskrit.
- Optional starting point for learners who can already read Devanagari.
- 3 multiple-choice questions per lesson, progress stored per authenticated user.
- Uses existing IAST preference; mobile-friendly native Streamlit controls.
- No new Python packages, no OpenAI API calls for these lessons.

## Deployment
1. Back up the working v2.7.1 GitHub repository.
2. Run `sanskrit_beginners_setup.sql` in the **Supabase SQL Editor**. Review it before executing. This creates one new table and one new RPC; it does not modify existing tables.
3. Upload the ZIP contents into the **GitHub repository root** (same folder as `app.py`). Ensure `sanskrit_beginners.py` and `sanskrit_beginners_content.py` are present.
4. Keep your existing Streamlit secrets and **Python 3.12** setting.
5. Redeploy. Test with two separate invited accounts; verify that their progress is separate.

## Security model
- Progress SELECT uses the signed-in user's Supabase access token, not the service-role key.
- RLS permits authenticated users to read only their own progress.
- Writes use a tightly scoped SECURITY DEFINER RPC; it derives the user ID from `auth.uid()` and never accepts a user ID parameter.
- The RPC accepts a lesson ID and a score; it does **not** independently validate individual answers. This is appropriate for casual learning but **not** for exams, credentials, or prizes.
- The lesson-selection preference is session-local. Progress persists in Supabase.

## Limitations and future improvements
- Curated text-only lessons; no recorded pronunciation audio or handwriting assessment in this version.
- Review the Sanskrit educational content with a qualified teacher before a public curriculum launch.
- This release has syntax/unit validation, but not live integration testing against your Supabase instance.
- Do not upload secrets, `.env`, or service-role keys to GitHub.
