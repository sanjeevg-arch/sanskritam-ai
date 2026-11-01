# Sanskritam AI v2.1 — Personalized Learning Dashboard

Based on v2.0 Voice Input Edition. All existing features remain in the project.

## Deploy
1. Back up your repository. Copy the updated project files into your GitHub repository.
2. In Supabase > SQL Editor, run **dashboard_setup.sql** once. Keep all previous database tables and setup scripts.
3. Retain existing Streamlit Secrets (OpenAI and Supabase keys). No new secrets or dependencies are required.
4. Commit and push to GitHub; allow Streamlit Community Cloud to redeploy.
5. Sign in as an invited user, translate a Sanskrit sentence with 3+ distinct words, and complete the Learn This Sentence quiz.
6. Open **📊 My Learning Dashboard** near the top of the app. It shows attempts, lessons, questions, accuracy, UTC-day practice streak, and recent attempts.

## Behavior and limits
- Quiz results are saved in Supabase, scoped by verified user UUID; no extra OpenAI requests.
- No quiz attempt is stored until all questions have been answered. Retry generates a new attempt.
- Dashboard displays the 500 latest attempts; this is not an all-time tally for users with more than 500 attempts.
- Database calls use the existing server-only service key. Keep it out of GitHub.
- A failed progress save shows a warning without preventing the quiz result from displaying.
- AI-generated vocabulary analysis may contain errors.
- Live Supabase/Streamlit testing has not been performed.


## Quiz progress hotfix (v2.1.1)

**Important:** Deploy `learning_mode.py`, `learning_dashboard.py`, and `app.py` together.
The older `learning_mode.py` displays “Progress is stored only in this browser session” and never saves a quiz. If that message appears, your deployed module is outdated.

1. Run `dashboard_setup.sql` in Supabase SQL Editor once.
2. Replace the three files above in the **same GitHub directory** that Streamlit Cloud uses for `app.py`. Commit and push.
3. In Streamlit Cloud, reboot the app if needed.
4. Complete a **new** quiz. You should see “Progress saved to Supabase”.
5. Expand My Learning Dashboard and click **Refresh dashboard**.
6. If saving fails, check Streamlit logs and verify `SUPABASE_SERVICE_ROLE_KEY` in Streamlit Secrets. Never share the key.

A previously completed quiz from the old session-only code cannot be recovered from Supabase because it was never saved.
