from flask import Flask, jsonify, request, send_from_directory, render_template
import requests
import os
from groq import Groq

app = Flask(__name__, static_url_path="", static_folder="static")


# client = Groq(api_key=GROQ_API_KEY)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Serve index.html
@app.route("/")
def index():
     return render_template("index.html")  # ✅ use templates
#    return send_from_directory("static", "index.html")

# ✅ RandomUser API for profiles
@app.route("/api/profiles")
def get_profiles():
    try:
        response = requests.get("https://randomuser.me/api/")  # fetch 1 profile
        user = response.json()["results"][0]

        profile = {
            "name": f"{user['name']['first']} {user['name']['last']}",
            "age": user["dob"]["age"],
            "bio": f"{user['location']['city']}, {user['location']['country']}",
            "pic": user["picture"]["large"],  # 👈 renamed to match app.js
        }

        return jsonify(profile)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ AI chat via Groq
@app.route("/api/send_message", methods=["POST"])
def send_message():
    try:
        user_message = request.json.get("message", "")

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are simulating a fun, flirty dating app conversation."},
                {"role": "user", "content": user_message},
            ],
            max_tokens=100,
        )

 # ✅ Defensive: check response structure
        if (
            completion 
            and hasattr(completion, "choices") 
            and len(completion.choices) > 0 
            and hasattr(completion.choices[0].message, "content")
        ):
            reply = completion.choices[0].message.content.strip()
        else:
            reply = "(No reply generated)"

        

        ai_response = completion.choices[0].message.content.strip()
        return jsonify({"ok": True, "reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=True)
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host="0.0.0.0", port=port)
    app.run(host="0.0.0.0", port=5000, debug=True)
