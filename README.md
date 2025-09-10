AI Tinder-like Swipe Demo (one profile at a time + AI chat)

How to run:
1. Unzip the package and cd into the folder.
2. (Optional) create a virtualenv: python3 -m venv venv && source venv/bin/activate
3. Install requirements: pip install flask requests
4. (Optional) To enable Groq integration, set environment variable GROQ_API_KEY before running:
   export GROQ_API_KEY="your_key_here"
5. Run: python app.py
6. Open http://127.0.0.1:7860

Notes:
- If GROQ_API_KEY isn't set or the Groq call fails, the server falls back to canned replies.
- This is a demo. Do NOT deploy as-is to production. It uses in-memory storage and minimal moderation.
- Profiles are AI-generated labels for demo; images use picsum.photos placeholders.
