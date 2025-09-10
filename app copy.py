from flask import Flask, render_template, request, jsonify, session
import random, os, requests, time
from uuid import uuid4

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

# Simple profile generator (one profile at a time)
NAMES = ["Aisha","Liam","Sophia","Ethan","Maya","Ravi","Leena","Noah","Zara","Kiran"]
BIRTH_YEAR_MIN = 1990
BIRTH_YEAR_MAX = 2004

SAMPLE_BIOS = [
    "Loves painting and long walks.",
    "Fitness enthusiast and foodie.",
    "Tech geek who enjoys sci-fi movies.",
    "Traveler and amateur photographer.",
    "Bookworm who drinks way too much coffee.",
    "Weekend hiker and plant parent.",
    "Sketchbook in hand, head full of dreams.",
    "Guitar player and chai lover."
]

SAMPLE_PICS = [
    "https://picsum.photos/seed/{s}/300/400".format(s=i) for i in range(10,90,8)
]

# Small moderation blacklist demo (not production-ready)
BLACKLIST = {"sex","nude","kill","suicide","child","porn","drugs"}

# In-memory store of active matched profile and message history (per session)
# For demo only — will reset when server restarts.
# session['match_id'] stores current matched profile id
MESSAGES = {}  # match_id -> [ {from:'user'|'ai', text:...}, ... ]

def generate_profile():
    name = random.choice(NAMES)
    age = random.randint(22, 35)
    bio = random.choice(SAMPLE_BIOS)
    pic = random.choice(SAMPLE_PICS)
    pid = str(uuid4())[:8]
    personality = random.choice(["artsy","funny","calm","adventurous","thoughtful"])
    return { "id": pid, "name": name, "age": age, "bio": bio, "pic": pic, "personality": personality }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/profiles')
def profiles():
    # return a single random profile (demo behaves like 'one profile at a time')
    p = generate_profile()
    return jsonify(p)

@app.route('/api/swipe', methods=['POST'])
def swipe():
    data = request.json or {}
    direction = data.get('direction')
    profile = data.get('profile')  # frontend can send the profile object
    if direction == 'right' and profile:
        # mark as matched in session and create message history
        match_id = profile.get('id') or str(uuid4())[:8]
        session['match_id'] = match_id
        MESSAGES[match_id] = [
            {"from":"ai", "text": f"Hi — I'm {profile.get('name')}! Nice to meet you. (AI-generated demo)"} 
        ]
        return jsonify({"match": True, "match_id": match_id})
    return jsonify({"match": False})

def moderate_text(text):
    t = (text or "").lower()
    for w in BLACKLIST:
        if w in t:
            return False, f"Message blocked by moderation (word: {w})"
    if len(text or "") > 1200:
        return False, "Message too long."
    return True, ""

def groq_reply(user_text, profile):
    """Attempt to call Groq chat completion. If GROQ_API_KEY not set or call fails, raise Exception."""
    key = os.environ.get('GROQ_API_KEY')
    if not key:
        raise RuntimeError("No GROQ_API_KEY")
    url = "https://api.groq.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    # Build a gentle prompt that asks the model to role-play the profile
    system = f"You are role-playing an AI dating-app persona. Profile: name={profile.get('name')}, age={profile.get('age')}, personality={profile.get('personality')}, bio={profile.get('bio')}. Keep replies friendly, short (max 80 tokens), and in a conversational tone. Don't claim to be a real person. Always include a gentle reminder: (AI-generated)."
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role":"system","content": system},
            {"role":"user","content": user_text},
        ],
        "max_tokens": 150,
        "temperature": 0.9
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")
    j = resp.json()
    # attempt to read common fields (best-effort)
    choice = None
    if isinstance(j.get('choices'), list) and j['choices']:
        c = j['choices'][0]
        # Groq responses often follow OpenAI shape; try to extract
        if isinstance(c.get('message'), dict):
            choice = c['message'].get('content')
        elif isinstance(c.get('text'), str):
            choice = c.get('text')
    if not choice:
        # fallback to raw json string if shape unexpected
        choice = str(j)
    return choice

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json or {}
    text = data.get('message','').strip()
    match_id = session.get('match_id')
    profile = data.get('profile') or {}

    ok, reason = moderate_text(text)
    if not ok:
        return jsonify({"ok": False, "error": reason}), 400

    # store user message
    if match_id:
        MESSAGES.setdefault(match_id, []).append({"from":"user","text": text})

    # Try Groq if key present, otherwise fallback
    reply = None
    try:
        reply = groq_reply(text, profile)
    except Exception as e:
        # fallback canned reply set — personality-aware small variations
        pers = (profile.get('personality') or "").lower()
        canned = [
            "That sounds interesting — tell me more!",
            "Haha, nice — what's the story behind that?",
            "I can totally relate. How did that make you feel?",
            "Lovely — I wish I was there with you!",
            "Oh wow, I like that. Tell me another."
        ]
        if 'artsy' in pers:
            canned = ["I love that — art makes everything better.", "Tell me about the colors you use in your painting!"]
        if 'advent' in pers or 'adventurous' in pers:
            canned = ["That sounds like a blast — where to next?", "I love adventure! Tell me your best trip story."]
        if 'funny' in pers:
            canned = ["Haha, that's hilarious — you win!", "You have jokes, I like that. Tell me another."]
        # small random pick
        reply = random.choice(canned)

    # store AI message
    if match_id:
        MESSAGES.setdefault(match_id, []).append({"from":"ai","text": reply})

    return jsonify({"ok": True, "reply": reply})

@app.route('/api/history')
def history():
    match_id = session.get('match_id')
    if not match_id:
        return jsonify([])
    return jsonify(MESSAGES.get(match_id, []))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)
