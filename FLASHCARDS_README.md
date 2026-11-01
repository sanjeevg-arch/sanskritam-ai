# Sanskritam AI v2.2 — Smart Vocabulary Flashcards

1. Back up your existing repository and Supabase project.
2. Run `flashcards_setup.sql` in Supabase SQL Editor. Keep existing migrations and tables.
3. Deploy the complete files from this ZIP to your existing Streamlit Cloud repository.
4. Retain your existing Streamlit Secrets (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`). Never commit secrets.
5. Sign in, translate a Sanskrit sentence, expand the flashcards section below Sandhi, and click **Save these words as flashcards**.
6. Open the flashcards section near the top to review cards. Reveal a meaning, then choose Again, Hard, or Easy.
7. Sign out and sign back in to verify saved cards and schedules persist.

No extra AI calls are made for creating or reviewing flashcards. The Supabase service-role key is server-only. Flashcards are fetched by authenticated user ID; no browser-facing access to service credentials. The study schedule uses a simplified spaced-repetition algorithm, not SM-2.

Note: Existing quiz history and all other features remain in place. Live Supabase, Streamlit Cloud and OpenAI integrations have not been tested here.
