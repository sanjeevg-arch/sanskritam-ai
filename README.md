# Sanskritam AI v1.6 — Secure Private Beta + Interactive Learning

This release builds on v1.5 and retains Supabase invitation-only OTP sign-in, atomic daily quotas, translations, comparison languages, word explorer, grammar, sandhi, speech, and accessibility controls.

## New in this version

- **👤 Account menu** near the top right of the page. It shows the authenticated email and contains **Sign out**. The old sidebar Sign out control is removed.
- **📚 Learn This Sentence** below Sandhi, with sentence structure, grammar explanations, and 3–5 multiple-choice vocabulary questions.
- Instant feedback, session-only score/progress, and a retry button.
- Quiz generation uses existing AI word-analysis output, with **zero additional OpenAI requests** for quiz interaction.

The quiz appears for Sanskrit → English source text with at least three distinct Sanskrit words and meanings. It is not a scholar-verified grammar assessment; source AI analysis can be inaccurate. Quiz progress resets on a new translation, sign-out, or session expiration. Progress is not stored in Supabase.

## Deploy on Streamlit Cloud

1. Back up your current repository.
2. Replace your current `app.py` and `private_beta.py` with the versions here. **Add the new `learning_mode.py`** alongside them. Retain the other included files.
3. Ensure `requirements.txt` is at the deployed app root. Do not commit `.env` or Streamlit secrets.
4. Keep the existing Streamlit secrets: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
5. Keep the existing Supabase schema from v1.5. **No database migration is required** for this release.
6. Commit and push changes to GitHub; allow Streamlit Cloud to redeploy.
7. Sign in with an approved email, translate `रामः पुस्तकं पठति।`, scroll below Sandhi, and answer the practice questions. Test the 👤 menu's Sign out action.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Important notes

- Keep your Supabase service-role key server-side. Never expose it in HTML, JavaScript, or the repository.
- The new quiz does not call OpenAI. Only **Translate & Analyze** calls OpenAI after the v1.5 quota reservation succeeds.
- The app still requires a configured Supabase project, invitation list, and working email OTP/SMTP settings.
- Local syntax checks passed. Live Supabase, OpenAI, and browser behavior have not been verified in this environment.


## v1.7 — Image-to-Sanskrit Translation

The **📷 Image-to-Sanskrit Translation** expander appears above the Translation workspace.

1. Sign in with your invited email.
2. Upload a clear PNG, JPEG, or WebP (maximum 5 MB).
3. Click **Extract Sanskrit text**. This calls the OpenAI vision model and consumes **one daily quota request**. Merely uploading does not call AI.
4. Check the extracted text in the editable **Enter text** field. Correct any mistakes.
5. Click **Translate & Analyze**. This is a **second AI request** and consumes another quota request.
6. Review translations, comparison languages, grammar, Sandhi and the learning quiz.

Images are processed by OpenAI and should not contain private or sensitive material. This feature is AI-assisted transcription, not guaranteed accurate OCR. Poor scans, unusual scripts, handwriting and damaged manuscripts may be transcribed incorrectly. The first 1,000 extracted characters can be transferred into the existing translation input. Existing invitation checks and database-backed quotas remain active for **both** image transcription and translation.

No new Python dependencies or Supabase SQL changes are required. Use the existing `.env` / Streamlit secrets and deploy all files from this directory.
