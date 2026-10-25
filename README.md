# Sanskritam AI v1.8 — Translation History & Bookmarks

Builds on v1.7 (private beta, image extraction, learning quizzes, compare languages, accessibility).

## Setup
1. Back up your existing GitHub repository and Supabase project.
2. In **Supabase → SQL Editor**, run **`history_setup.sql`** once. Keep the earlier `supabase_setup.sql` tables/functions; this migration only adds history.
3. Upload **`app.py`** and new **`history.py`** along with the existing project files to GitHub.
4. Keep existing Streamlit secrets: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`. Never commit keys.
5. Redeploy Streamlit Cloud. No new Python dependencies are required.

## Usage
- Sign in with an invited account and translate a passage. A successful translation is automatically saved to Supabase.
- Scroll to **Translation History & Bookmarks** to browse the 50 most recent entries.
- Click **⭐ Bookmark** to mark an entry; **Show bookmarks only** filters the list.
- Click **📖 Open** to restore the saved result and learning content without another AI request or quota charge.
- Click **🗑️ Delete** to remove an entry. Deletion is immediate.
- History is private per verified Supabase Auth user ID, persisted across Streamlit restarts.

## Notes
- The existing OpenAI request quota remains enforced for NEW translations and image extraction. Reopening a saved translation does not call OpenAI.
- Supabase service-role credentials are used only in server-side Python; every history operation filters by the verified account's user ID.
- The app stores submitted source text and generated analyses in Supabase. Inform beta testers and obtain consent; do not submit sensitive material.
- History is limited to the latest 50 entries in the UI; no bulk export or pagination in this version.
- Existing translations from earlier versions are not backfilled.
- Python syntax and ZIP integrity were checked; live Supabase and Streamlit UI tests were not performed.


## v1.9 PDF Study Notes
After translating a passage (or opening an item in History), expand **Customize PDF study notes**, choose the sections to include, click **Prepare PDF study notes**, then **Download PDF Study Notes**. No additional OpenAI requests are made. The generated PDF includes source text, natural and literal translations, selected-language translations, and optionally word analysis, grammar, and Sandhi. Quiz questions and personal details are not exported.

### Deployment dependencies
`requirements.txt` adds `weasyprint`. `packages.txt` installs `fonts-noto-core` on Streamlit Community Cloud for Indic-script rendering. Streamlit Cloud must install both Python and OS dependencies; if installation fails, inspect build logs. Font coverage may vary for some scripts. No additional Supabase migration is required.

**Privacy:** PDF generation runs server-side using existing session results; PDFs are returned directly to the signed-in user, not uploaded to a third-party service. Avoid sharing PDFs containing sensitive text.
