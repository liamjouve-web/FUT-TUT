import os
import json
import random
import hashlib
import hmac
import secrets
from datetime import date, datetime, timedelta

import streamlit as st

# ============================================================
# FUT TUT — Football Training App
# Single-file Streamlit build
# ============================================================

st.set_page_config(
    page_title="FUT TUT ⚽",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "futtut_data.json"
MAX_LEVEL = 20
XP_PER_LEVEL = 250

CATEGORIES = [
    "Finishing",
    "Dribbling",
    "First Touch",
    "Passing",
    "Speed",
    "Soccer IQ",
]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
POSITIONS = ["Winger", "Striker", "Midfielder", "Defender", "Fullback", "Goalkeeper"]
STYLES = ["Balanced", "Technical", "Match-like"]
GOALS = [
    "Become more complete",
    "Improve my biggest weakness",
    "Perform better in games",
    "Build confidence under pressure",
    "Improve my technique",
    "Get ready for a higher level",
]

POSITION_BIAS = {
    "Winger": ["Dribbling", "Speed", "Finishing", "First Touch", "Soccer IQ"],
    "Striker": ["Finishing", "First Touch", "Soccer IQ", "Speed", "Dribbling"],
    "Midfielder": ["Passing", "First Touch", "Soccer IQ", "Dribbling", "Speed"],
    "Defender": ["Soccer IQ", "Passing", "First Touch", "Speed", "Dribbling"],
    "Fullback": ["Speed", "Passing", "First Touch", "Soccer IQ", "Dribbling"],
    "Goalkeeper": ["First Touch", "Passing", "Soccer IQ", "Speed"],
}

STYLE_KEYWORDS = {
    "Balanced": ["control", "both", "side", "repeat"],
    "Technical": ["technique", "control", "touch", "quality"],
    "Match-like": ["pressure", "decision", "game", "speed"],
}

DRILLS = {
    "Finishing": [
        ("One-Touch Finishing", "Beginner", 10, "Finish quickly from a short setup.", "Ball, cones, goal or target"),
        ("Near-Post Finishing", "Beginner", 10, "Practice fast, accurate finishes toward the near side.", "Ball, cones, goal or target"),
        ("Far-Corner Placement", "Beginner", 10, "Prioritize accuracy into the far side of the target.", "Ball, cones, goal or target"),
        ("Moving Ball Finish", "Intermediate", 12, "Receive a moving ball and finish without taking unnecessary touches.", "Ball, cones, goal or target"),
        ("Cutback Finishing", "Intermediate", 12, "Attack a cutback and finish first time or with one setup touch.", "Ball, cones, goal or target"),
        ("Weak-Foot Finishing", "Intermediate", 12, "Build reliable finishing with your less comfortable foot.", "Ball, cones, goal or target"),
        ("First-Time Volley", "Advanced", 14, "Coordinate your body and timing for controlled volleys.", "Ball, goal or target"),
        ("Pressure Finishing", "Advanced", 14, "Finish after a quick movement or decision cue.", "Ball, cones, goal or target"),
        ("Three-Zone Finishing", "Advanced", 14, "Finish from three different starting zones.", "Ball, cones, goal or target"),
        ("Rebound Finishing", "Advanced", 14, "React quickly to a rebound and choose a controlled finish.", "Ball, cones, goal or target"),
    ],
    "Dribbling": [
        ("Cone Slalom", "Beginner", 10, "Carry the ball through cones with controlled changes of direction.", "Ball, 5–8 cones"),
        ("Inside-Outside", "Beginner", 10, "Alternate inside and outside touches while moving forward.", "Ball, cones"),
        ("Figure Eight", "Beginner", 10, "Dribble around two markers while keeping the ball close.", "Ball, 2 cones"),
        ("Change of Direction", "Beginner", 10, "Use controlled changes of direction at increasing speed.", "Ball, cones"),
        ("Elastico Reps", "Intermediate", 12, "Practice the elastico slowly, then add realistic speed.", "Ball, cones"),
        ("1v1 Attack", "Intermediate", 12, "Use a move to create space before accelerating away.", "Ball, cones, partner optional"),
        ("Tight-Space Dribbling", "Intermediate", 12, "Keep possession in a small area with frequent touches.", "Ball, cones"),
        ("Speed Dribble", "Advanced", 14, "Combine a controlled carry with a sharp acceleration.", "Ball, cones"),
        ("Move + Burst", "Advanced", 14, "Perform a move and immediately accelerate into space.", "Ball, cones"),
        ("Stop-Start Dribbling", "Advanced", 14, "Change tempo suddenly while keeping the ball under control.", "Ball, cones"),
    ],
    "First Touch": [
        ("Wall First Touch", "Beginner", 10, "Pass against a wall and control the return into useful space.", "Ball, wall"),
        ("Open-Body Receive", "Beginner", 10, "Receive side-on so your next action is easier.", "Ball, wall or partner"),
        ("First Touch Across Body", "Beginner", 10, "Take the first touch across your body and away from pressure.", "Ball, wall or partner"),
        ("Turn on First Touch", "Intermediate", 12, "Control and turn when the situation allows it.", "Ball, wall or partner"),
        ("High-Ball Control", "Intermediate", 12, "Bring a higher ball down with a calm first touch.", "Ball, partner optional"),
        ("Receive Under Pressure", "Intermediate", 12, "Control the ball while imagining or using a pressure cue.", "Ball, wall or partner"),
        ("Back-Foot Receiving", "Intermediate", 12, "Receive on the farther foot to open your next action.", "Ball, wall or partner"),
        ("First Touch Escape", "Advanced", 14, "Use the first touch to escape an imagined defender.", "Ball, cones, wall or partner"),
        ("Match-Speed Receiving", "Advanced", 14, "Receive while moving at realistic game speed.", "Ball, wall or partner"),
        ("Receive-and-Play", "Advanced", 14, "Control and play the next pass quickly and accurately.", "Ball, wall or partner"),
    ],
    "Passing": [
        ("Two-Touch Wall Passing", "Beginner", 10, "Receive and pass with a clean two-touch rhythm.", "Ball, wall"),
        ("One-Touch Wall Passing", "Beginner", 10, "Use one-touch passing while maintaining a controlled rhythm.", "Ball, wall"),
        ("Passing Gates", "Beginner", 10, "Pass through small gates with consistent accuracy.", "Ball, 2–6 cones"),
        ("Third-Man Passing", "Intermediate", 12, "Combine with a wall or partner to simulate a third-player action.", "Ball, wall or 2 partners"),
        ("Split Passes", "Intermediate", 12, "Pass through a gap between markers with the right pace.", "Ball, cones"),
        ("Long-Passing Technique", "Intermediate", 12, "Practice clean contact and controlled longer passes.", "Ball, open space"),
        ("Weak-Foot Passing", "Intermediate", 12, "Build accuracy and confidence on your less comfortable foot.", "Ball, wall or partner"),
        ("Pressure Passing", "Advanced", 14, "Make accurate passes after a quick scan or movement cue.", "Ball, cones, partner optional"),
        ("Switch of Play", "Advanced", 14, "Move the ball accurately across a larger area.", "Ball, cones, partner optional"),
        ("Third-Line Combination", "Advanced", 14, "Combine movement and passing to break a line.", "Ball, cones, 1–2 partners"),
    ],
    "Speed": [
        ("Acceleration Starts", "Beginner", 10, "Practice explosive first steps from different starting positions.", "Cones, open space"),
        ("Cone Sprints", "Beginner", 10, "Sprint between markers while staying controlled through turns.", "Cones, open space"),
        ("Reaction Sprint", "Beginner", 10, "React to a visual or verbal cue before accelerating.", "Cones, partner optional"),
        ("Sprint + Ball", "Intermediate", 12, "Accelerate while keeping the ball under control.", "Ball, cones"),
        ("Change-of-Direction Sprint", "Intermediate", 12, "Sprint, brake under control, and accelerate in a new direction.", "Cones"),
        ("Curved Sprint Runs", "Intermediate", 12, "Use curved runs to mirror realistic football movement.", "Cones, open space"),
        ("Repeated Sprint", "Advanced", 14, "Repeat short quality sprints with sensible recovery.", "Cones, open space"),
        ("Explosive First Step", "Advanced", 14, "Focus on the first few steps after a change of direction.", "Cones"),
        ("Game-Speed Running", "Advanced", 14, "Combine changes of pace with football movements.", "Cones, ball optional"),
        ("Burst + Recover", "Advanced", 14, "Alternate short bursts with controlled recovery movement.", "Cones, open space"),
    ],
    "Soccer IQ": [
        ("Scanning Drill", "Beginner", 10, "Check your surroundings before receiving or moving.", "Ball, wall or partner"),
        ("Shoulder Check", "Beginner", 10, "Build the habit of checking both sides before the ball arrives.", "Ball, wall or partner"),
        ("Find the Space", "Beginner", 10, "Identify useful open space before moving into it.", "Cones, ball optional"),
        ("Third-Man Run", "Intermediate", 12, "Recognize when a third player can create an advantage.", "Ball, 2 partners optional"),
        ("Winger Decision-Making", "Intermediate", 12, "Choose between carrying, passing, or moving into space.", "Ball, cones, partner optional"),
        ("When to Carry", "Intermediate", 12, "Recognize moments where carrying the ball is useful.", "Ball, cones"),
        ("Defensive Scanning", "Intermediate", 12, "Check space, teammates, and opponents before defending.", "Cones, partner optional"),
        ("Final-Third Choices", "Advanced", 14, "Practice choosing between a pass, carry, cross, or shot.", "Ball, cones, goal/target"),
        ("Match Reading", "Advanced", 14, "Pause and identify the highest-value next action.", "Ball, cones, partner optional"),
        ("Space + Timing", "Advanced", 14, "Coordinate movement timing with available space.", "Cones, ball, partner optional"),
    ],
}

DRILL_INDEX = {}
for cat, items in DRILLS.items():
    for name, level, mins, short, equipment in items:
        DRILL_INDEX[name] = {
            "name": name, "category": cat, "level": level, "minutes": mins,
            "short": short, "equipment": equipment,
        }

DEFAULT_DATA = {
    "users": {},
    "current_user": "",
}

# ---------- Styling ----------
st.markdown("""
<style>
:root { color-scheme: dark; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
    background: #080b12 !important;
    color: #f4f7fb !important;
}
[data-testid="stHeader"] { background: rgba(8,11,18,.92) !important; }
[data-testid="stSidebar"] { background: #0b0f18 !important; }
* { box-sizing: border-box; }
h1,h2,h3,h4,h5,p,span,label,div { color: #f4f7fb; }
.stMarkdown, .stText, .stCaption { color: #dce3ee !important; }
.small-muted { color:#9ca9ba !important; font-size:.9rem; }
.card {
    background: linear-gradient(145deg,#111827,#0c111b);
    border:1px solid #253047;
    border-radius:20px;
    padding:20px;
    margin:8px 0 16px;
    box-shadow:0 8px 30px rgba(0,0,0,.18);
}
.hero {
    padding:28px 24px;
    border-radius:24px;
    background: radial-gradient(circle at 15% 10%,#17233a 0%,#0e1420 38%,#090d15 100%);
    border:1px solid #2a3954;
    margin-bottom:18px;
}
.logo {
    font-size:3.2rem; font-weight:900; letter-spacing:-3px; line-height:1;
}
.pill {
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:#182237; border:1px solid #30405c; color:#dfe8f5 !important;
    margin:2px 4px 2px 0; font-size:.8rem;
}
.big-number { font-size:2rem; font-weight:850; }
.locked { opacity:.5; }
div.stButton > button {
    width:100%; border-radius:13px; min-height:44px;
    font-weight:750; border:1px solid #2b3951;
    background:#151d2b; color:#f7f9fc !important;
}
div.stButton > button:hover { border-color:#6e82a6; transform:translateY(-1px); }
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color:#f4f7fb !important; }
input, textarea, select, [data-baseweb="select"] > div {
    color:#f4f7fb !important;
}
</style>

<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
    background: #070a10 !important;
    color: #f8fbff !important;
}
[data-testid="stHeader"] { background: rgba(7,10,16,.92) !important; }
[data-testid="stSidebar"] { background: #090d15 !important; }
h1,h2,h3,h4,h5,h6,p,span,label,div { color: #f8fbff; }
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #0b111b !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #30415b !important;
    border-radius: 12px !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #718096 !important;
    -webkit-text-fill-color: #718096 !important;
}
[data-baseweb="select"] > div {
    background-color: #0b111b !important;
    color: #ffffff !important;
    border-color: #30415b !important;
}
[data-baseweb="select"] span { color: #ffffff !important; }
[data-baseweb="popover"] * { color: #ffffff !important; }
div.stButton > button {
    color: #ffffff !important;
    background: #151f2e !important;
    border: 1px solid #30415b !important;
    border-radius: 13px !important;
    font-weight: 800 !important;
}
div.stButton > button:hover {
    border-color: #62ff9a !important;
    background: #1b293b !important;
}
div.stButton > button[kind="primary"] {
    color: #06100a !important;
    background: #62ff9a !important;
    border-color: #62ff9a !important;
}
div.stButton > button[kind="primary"]:hover {
    background: #7dffac !important;
}
div[data-testid="stForm"] {
    background: linear-gradient(145deg,#111a29,#0a1019) !important;
    border: 1px solid #2a3b55 !important;
    border-radius: 24px !important;
    padding: 24px !important;
}
.stCaption, [data-testid="stCaptionContainer"] { color: #9aa8ba !important; }
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #ffffff !important; }
.brand-green { color: #62ff9a !important; }
</style>
""", unsafe_allow_html=True)

# ---------- Persistence ----------
def blank_user():
    return {
        "password_hash": "",
        "created": datetime.now().isoformat(timespec="seconds"),
        "profile": {
            "name": "",
            "position": "Winger",
            "style": "Balanced",
            "email": "",
        },
        "assessment": {
            "completed": False,
            "strengths": [],
            "weaknesses": [],
            "pressure": 3,
            "confidence": 3,
            "goal": GOALS[0],
            "training_days": 3,
        },
        "xp": 0,
        "sessions": 0,
        "completed": [],
        "completion_counts": {},
        "challenge_claimed": [],
        "weekly_goal": 5,
        "weekly_sessions": 0,
        "week_key": "",
        "training_dates": [],
        "recent_sessions": [],
    }

def load_db():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "current_user": ""}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        if not isinstance(db, dict):
            raise ValueError
        db.setdefault("users", {})
        db.setdefault("current_user", "")
        return db
    except Exception:
        return {"users": {}, "current_user": ""}

def save_db(db):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    os.replace(tmp, DATA_FILE)

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000)
    return salt + "$" + digest.hex()

def verify_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000).hex()
        return hmac.compare_digest(check, digest)
    except Exception:
        return False

def normalize_user(u):
    base = blank_user()
    if isinstance(u, dict):
        for key, value in u.items():
            if key in base:
                base[key] = value
    base["profile"] = {**blank_user()["profile"], **(u.get("profile", {}) if isinstance(u, dict) else {})}
    base["assessment"] = {**blank_user()["assessment"], **(u.get("assessment", {}) if isinstance(u, dict) else {})}
    if not isinstance(base["completed"], list):
        base["completed"] = []
    base["completed"] = list(dict.fromkeys(str(x) for x in base["completed"]))
    if not isinstance(base["completion_counts"], dict):
        base["completion_counts"] = {}
    if not isinstance(base["challenge_claimed"], list):
        base["challenge_claimed"] = []
    if not isinstance(base["training_dates"], list):
        base["training_dates"] = []
    if not isinstance(base["recent_sessions"], list):
        base["recent_sessions"] = []
    return base

db = load_db()
if db.get("current_user") and db["current_user"] in db["users"]:
    st.session_state.setdefault("logged_in_user", db["current_user"])

def current_user():
    username = st.session_state.get("logged_in_user", "")
    if username and username in db["users"]:
        db["users"][username] = normalize_user(db["users"][username])
        return db["users"][username]
    return None

def update_user(user):
    username = st.session_state.get("logged_in_user", "")
    if username:
        db["users"][username] = user
        db["current_user"] = username
        save_db(db)

# ---------- Helpers ----------
def week_key():
    d = date.today()
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()

def ensure_week(user):
    if user.get("week_key") != week_key():
        user["week_key"] = week_key()
        user["weekly_sessions"] = 0
        update_user(user)

def level_from_xp(xp):
    return min(MAX_LEVEL, int(xp // XP_PER_LEVEL) + 1)

def level_progress(xp):
    level = level_from_xp(xp)
    if level >= MAX_LEVEL:
        return XP_PER_LEVEL, XP_PER_LEVEL
    current = xp % XP_PER_LEVEL
    return current, XP_PER_LEVEL

def complete_drill(user, drill_name):
    if drill_name in user["completed"]:
        return False, 0, False
    drill = DRILL_INDEX[drill_name]
    xp = {"Beginner": 25, "Intermediate": 30, "Advanced": 35}[drill["level"]]
    old_level = level_from_xp(user["xp"])
    user["xp"] += xp
    user["sessions"] += 1
    user["completed"].append(drill_name)
    user["completion_counts"][drill_name] = user["completion_counts"].get(drill_name, 0) + 1
    user["weekly_sessions"] += 1
    user["training_dates"].append(date.today().isoformat())
    user["training_dates"] = user["training_dates"][-90:]
    user["recent_sessions"].insert(0, {
        "date": datetime.now().isoformat(timespec="seconds"),
        "drill": drill_name,
        "category": drill["category"],
        "xp": xp,
    })
    user["recent_sessions"] = user["recent_sessions"][:30]
    update_user(user)
    new_level = level_from_xp(user["xp"])
    return True, xp, new_level > old_level

def drill_instructions(drill):
    cat = drill["category"]
    name = drill["name"]
    level = drill["level"]
    return [
        f"Set up: {drill['equipment']}. Give yourself enough room to move safely.",
        f"Start controlled: work at a pace where you can keep the ball under control.",
        f"Main work: perform 3–5 rounds of 30–60 seconds, or 8–12 quality repetitions.",
        f"Focus for {name}: {drill['short']}",
        "Reset between rounds. Quality beats rushing.",
        "When your technique is consistent, add speed, a decision cue, or realistic pressure.",
    ]

def get_scored_categories(user):
    a = user["assessment"]
    pos = user["profile"]["position"]
    scores = {c: 0 for c in CATEGORIES}
    for c in a.get("weaknesses", []):
        if c in scores: scores[c] += 7
    for c in a.get("strengths", []):
        if c in scores: scores[c] += 1
    goal = a.get("goal", "")
    if "weakness" in goal.lower():
        for c in a.get("weaknesses", []):
            if c in scores: scores[c] += 3
    if "game" in goal.lower() or "higher" in goal.lower():
        for c in ["Soccer IQ", "First Touch"]:
            scores[c] += 1
    if a.get("pressure", 3) <= 2:
        for c in ["First Touch", "Soccer IQ", "Finishing", "Passing"]:
            scores[c] += 2
    if a.get("confidence", 3) <= 2:
        for c in ["First Touch", "Dribbling", "Finishing", "Passing"]:
            scores[c] += 1
    for i, c in enumerate(POSITION_BIAS.get(pos, CATEGORIES)):
        scores[c] += max(1, 5 - i)
    return sorted(scores, key=lambda c: (-scores[c], c))

def recommended_drills(user, limit=5):
    ranked_categories = get_scored_categories(user)
    a = user["assessment"]
    style_words = STYLE_KEYWORDS.get(user["profile"]["style"], [])
    rows = []
    for name, d in DRILL_INDEX.items():
        score = 0
        cat_rank = ranked_categories.index(d["category"]) if d["category"] in ranked_categories else 99
        score += max(0, 12 - cat_rank * 2)
        if d["category"] in a.get("weaknesses", []): score += 8
        if d["category"] in a.get("strengths", []): score += 1
        if d["category"] == POSITION_BIAS.get(user["profile"]["position"], [None])[0]: score += 3
        if any(word in (d["short"] + " " + d["name"]).lower() for word in style_words): score += 1
        score -= min(user["completion_counts"].get(name, 0), 3) * 2
        if name not in user["completed"]: score += 5
        else: score -= 10
        rows.append((score + random.random() * .01, name))
    rows.sort(reverse=True)
    return [name for _, name in rows[:limit]]

def ai_fallback(user, question):
    q = question.lower().strip()
    cats = user["assessment"].get("weaknesses", []) or ["First Touch"]
    weak = ", ".join(cats[:2])
    pos = user["profile"].get("position", "player")
    goal = user["assessment"].get("goal", "become more complete")
    openings = [
        "Good question.", "Yep — here's the football answer.", "Let's break it down.",
        "That's something players can actually train.", "For your game, I'd approach it like this.",
        "Here's the simple version.", "Think about it this way.", "A useful rule of thumb:",
    ]
    if any(x in q for x in ["plant foot", "planting foot"]):
        answers = [
            f"Your plant foot is the non-kicking foot. Put it beside the ball, point it roughly where you want the ball to go, and keep it stable. Then let the kicking leg do the work.",
            "For a clean strike, your support foot helps control balance and direction. Practice placing it beside the ball before worrying about hitting harder.",
            "A simple cue: support foot beside the ball, eyes on the contact, then swing through. Accuracy first; power comes later.",
        ]
        return random.choice(openings) + " " + random.choice(answers)
    if any(x in q for x in ["first touch", "touch under pressure", "control"]):
        return random.choice(openings) + f" Since your assessment points toward {weak}, I'd train first touch with a purpose: receive, take the ball away from the imagined defender, then play your next action. Start slow, then add pressure and speed."
    if any(x in q for x in ["dribble", "dribbling", "1v1", "elastico"]):
        return random.choice(openings) + " In a 1v1, don't spam moves. Sell one direction, shift the defender, then accelerate into the space you created. Your best move is the one you can execute at game speed."
    if any(x in q for x in ["shoot", "shooting", "finish", "finishing"]):
        return random.choice(openings) + " Focus on clean contact and picking a target before adding power. Try 3 rounds: controlled finishes, moving-ball finishes, then game-speed finishes."
    if any(x in q for x in ["pass", "passing"]):
        return random.choice(openings) + " Before the ball arrives, scan. Then choose the simplest pass that keeps your team moving. Work both feet and vary distance instead of only doing comfortable wall passes."
    if any(x in q for x in ["confidence", "nervous", "pressure", "anxious"]):
        return random.choice(openings) + " Pressure gets easier when your focus becomes tiny and specific. Pick one cue for the next action — scan, first touch, pass — instead of judging the whole performance."
    if any(x in q for x in ["practice", "train", "workout", "session"]):
        recs = recommended_drills(user, 3)
        return random.choice(openings) + f" I'd build today's session around {', '.join(recs)}. That matches your {pos} profile and your goal to {goal.lower()}."
    if "why" in q or "how" in q:
        return random.choice(openings) + f" The key is to connect the technique to a football decision. For your current profile, I'd give extra attention to {weak}, then test it at game speed."
    endings = [
        "Keep the quality high and stop a drill if your technique falls apart.",
        "Don't chase speed until the movement is reliable.",
        "A few focused reps are better than mindless hundreds.",
        "Then test the skill in a game-like situation.",
        "Use both feet when the drill allows it.",
        "If you can explain the decision, you usually understand the drill better.",
        "Build it slowly, then make it harder.",
        "The goal is transfer to matches, not just looking good in practice.",
    ]
    return random.choice(openings) + f" Based on your profile, I'd connect this to {weak}. " + random.choice(endings)

def ask_ai(user, question):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ai_fallback(user, question)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = (
            "You are FUT TUT, a friendly soccer training coach. Give concise, practical, age-appropriate "
            "football coaching. Never provide medical diagnosis. User profile: "
            f"position={user['profile']['position']}; style={user['profile']['style']}; "
            f"strengths={user['assessment'].get('strengths', [])}; weaknesses={user['assessment'].get('weaknesses', [])}; "
            f"goal={user['assessment'].get('goal')}. Question: {question}"
        )
        response = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5-mini"), input=prompt)
        text = getattr(response, "output_text", None)
        return text.strip() if text else ai_fallback(user, question)
    except Exception:
        return ai_fallback(user, question)

# ---------- Session state ----------
st.session_state.setdefault("page", "Home")
st.session_state.setdefault("selected_drill", "")
st.session_state.setdefault("active_drill", "")
st.session_state.setdefault("auth_mode", "login")
st.session_state.setdefault("quiz_step", 0)
st.session_state.setdefault("quiz_data", {})

# ---------- Authentication ----------
user = current_user()
if user is None:
    st.markdown("""
    <div class="hero">
      <div class="logo">FUT TUT ⚽</div>
      <p style="font-size:1.1rem;">Train smarter. Play better.</p>
      <p class="small-muted">Your soccer training, progress, and personalized plan in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    login_tab, signup_tab = st.tabs(["Log In", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="your username").strip().lower()
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In →", type="primary")
        if submitted:
            if not username or not password:
                st.error("Enter both your username and password.")
            elif username not in db["users"] or not verify_password(password, db["users"][username].get("password_hash", "")):
                st.error("Username or password is incorrect.")
            else:
                st.session_state.logged_in_user = username
                db["current_user"] = username
                save_db(db)
                st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            username = st.text_input("Choose a username", placeholder="3–20 letters/numbers")
            email = st.text_input("Email (optional)", help="Saved to your profile. Email verification and password-reset emails require a real authentication/email provider.")
            password = st.text_input("Create a password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            agree = st.checkbox("I understand this is a training app and I should involve a parent/guardian for account and public-release decisions.")
            submitted = st.form_submit_button("Create Account →", type="primary")
        if submitted:
            username_clean = username.strip().lower()
            if (not username_clean.isascii() or not username_clean.replace("_", "").isalnum() or not (3 <= len(username_clean) <= 20)):
                st.error("Username must be 3–20 characters using letters, numbers, or underscores.")
            elif username_clean in db["users"]:
                st.error("That username is already taken.")
            elif len(password) < 8:
                st.error("Use a password with at least 8 characters.")
            elif password != confirm:
                st.error("Passwords don't match.")
            elif not agree:
                st.error("Please check the box before creating the account.")
            else:
                u = blank_user()
                u["password_hash"] = hash_password(password)
                u["profile"]["name"] = username.strip()
                if email.strip():
                    u["profile"]["email"] = email.strip()
                db["users"][username_clean] = u
                db["current_user"] = username_clean
                save_db(db)
                st.session_state.logged_in_user = username_clean
                st.session_state.page = "Assessment"
                st.rerun()
    st.stop()

# ---------- Logged-in app ----------
user = normalize_user(user)
ensure_week(user)

# First-run assessment gate
if not user["assessment"].get("completed", False) and st.session_state.page == "Home":
    st.session_state.page = "Assessment"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## FUT <span class=\"brand-green\">TUT</span> ⚽", unsafe_allow_html=True)
    st.caption(f"@{st.session_state.logged_in_user}")
    nav = ["Home", "Drills", "Training Plan", "Assessment", "AI Coach", "Progress", "Profile"]
    for item in nav:
        if st.button(item, key="nav_" + item, use_container_width=True):
            st.session_state.page = item
            st.rerun()
    st.divider()
    if st.button("Log Out", use_container_width=True):
        db["current_user"] = ""
        save_db(db)
        for key in ["logged_in_user", "selected_drill", "active_drill"]:
            st.session_state.pop(key, None)
        st.rerun()

# ---------- Header ----------
st.markdown(
    f'<div class="small-muted">LEVEL {level_from_xp(user["xp"])} · {user["xp"]} XP · {user["profile"]["position"]}</div>',
    unsafe_allow_html=True,
)

# ---------- Home ----------
if st.session_state.page == "Home":
    recs = recommended_drills(user, 3)
    primary = recs[0] if recs else list(DRILL_INDEX)[0]
    progress, needed = level_progress(user["xp"])
    st.markdown(f"""
    <div class="hero">
      <div class="logo">FUT TUT</div>
      <p style="font-size:1.25rem;">Welcome back, {user["profile"]["name"] or st.session_state.logged_in_user}.</p>
      <span class="pill">{user["profile"]["position"]}</span>
      <span class="pill">{user["profile"]["style"]}</span>
      <span class="pill">{user["assessment"].get("goal", GOALS[0])}</span>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Level", level_from_xp(user["xp"]))
    c2.metric("XP", user["xp"])
    c3.metric("Sessions", user["sessions"])
    c4.metric("This week", f"{user['weekly_sessions']}/{user['weekly_goal']}")

    st.progress(min(1.0, progress / needed))
    st.caption(f"{progress}/{needed} XP toward the next level")

    st.markdown("### 🎯 Recommended for you")
    d = DRILL_INDEX[primary]
    st.markdown(f"""
    <div class="card">
      <h3>{d['name']}</h3>
      <p>{d['short']}</p>
      <span class="pill">{d['category']}</span>
      <span class="pill">{d['level']}</span>
      <span class="pill">{d['minutes']} min</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start This Drill →", key="home_start"):
        st.session_state.selected_drill = primary
        st.session_state.active_drill = primary
        st.session_state.page = "Drill"
        st.rerun()

    st.markdown("### Your focus")
    cols = st.columns(3)
    for i, cat in enumerate(get_scored_categories(user)[:3]):
        cols[i].markdown(f'<div class="card"><div class="big-number">{i+1}</div><b>{cat}</b><br><span class="small-muted">Priority from your assessment</span></div>', unsafe_allow_html=True)

# ---------- Drills ----------
elif st.session_state.page == "Drills":
    st.markdown("## Drills")
    f1,f2,f3 = st.columns(3)
    category = f1.selectbox("Category", CATEGORIES)
    level = f2.selectbox("Level", LEVELS)
    search = f3.text_input("Search drills", placeholder="e.g. first touch")
    items = [
        d for d in DRILL_INDEX.values()
        if d["category"] == category and d["level"] == level
        and search.lower() in d["name"].lower()
    ]
    for d in items:
        done = d["name"] in user["completed"]
        st.markdown(f"""
        <div class="card">
          <h3>{d['name']} {'✓' if done else ''}</h3>
          <p>{d['short']}</p>
          <span class="pill">{d['minutes']} min</span>
          <span class="pill">{d['level']}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Train Again" if done else "Start This Drill", key="start_"+d["name"]):
            st.session_state.selected_drill = d["name"]
            st.session_state.active_drill = d["name"]
            st.session_state.page = "Drill"
            st.rerun()

# ---------- Drill page ----------
elif st.session_state.page == "Drill":
    name = st.session_state.get("active_drill") or st.session_state.get("selected_drill")
    if name not in DRILL_INDEX:
        st.warning("Choose a drill first.")
        st.session_state.page = "Drills"
        st.rerun()
    d = DRILL_INDEX[name]
    done = name in user["completed"]
    st.markdown(f"## {d['name']}")
    st.caption(f"{d['category']} · {d['level']} · about {d['minutes']} minutes")
    st.markdown(f'<div class="card"><h3>What you are training</h3><p>{d["short"]}</p></div>', unsafe_allow_html=True)

    st.markdown("### How to do it")
    for i, step in enumerate(drill_instructions(d), 1):
        st.markdown(f"**{i}.** {step}")

    st.markdown("### Coach focus")
    focus = {
        "Finishing": "Pick a target before you strike. Clean contact first, power second.",
        "Dribbling": "Keep the ball close before the burst. Change direction, then accelerate.",
        "First Touch": "Your first touch should help your next action, not just stop the ball.",
        "Passing": "Scan before the ball arrives and pass with the pace your teammate needs.",
        "Speed": "Quality acceleration and controlled deceleration matter more than reckless sprinting.",
        "Soccer IQ": "Look before you act. Try to identify the next useful option early.",
    }[d["category"]]
    st.info(focus)

    st.markdown("### Progression")
    st.write("Once you can complete the drill cleanly, make it harder by adding speed, a weaker foot, a smaller space, a decision cue, or realistic pressure.")

    if done:
        st.success("✓ You've already claimed the XP for this drill. You can train it again anytime.")
        st.button("✓ XP Already Claimed", disabled=True, key="claimed_disabled")
    else:
        if st.button("Complete Drill  ·  Claim XP", key="complete_"+name):
            ok, xp, leveled = complete_drill(user, name)
            if ok:
                st.session_state.last_xp = xp
                st.session_state.last_level_up = leveled
                if leveled:
                    st.balloons()
                st.rerun()

    if st.button("← Back to Drills", key="back_drills"):
        st.session_state.page = "Drills"
        st.rerun()

# ---------- Training Plan ----------
elif st.session_state.page == "Training Plan":
    st.markdown("## Personalized Training Plan")
    recs = recommended_drills(user, 5)
    st.markdown(
        f'<div class="card"><h3>Built from your assessment</h3><p>Priority areas: {", ".join(get_scored_categories(user)[:3])}.</p><p>Goal: {user["assessment"].get("goal")}</p></div>',
        unsafe_allow_html=True,
    )
    duration = st.select_slider("Session length", options=[15, 30, 45, 60], value=30)
    slots = max(2, min(5, duration // 10))
    plan = recs[:slots]
    for i, name in enumerate(plan, 1):
        d = DRILL_INDEX[name]
        st.markdown(f"""
        <div class="card">
          <b>{i}. {name}</b><br>
          <span class="small-muted">{d['category']} · {d['level']} · {d['minutes']} min</span>
          <p>{d['short']}</p>
        </div>
        """, unsafe_allow_html=True)
    st.caption("Your plan updates automatically as you complete drills and change your assessment.")

# ---------- Assessment ----------
elif st.session_state.page == "Assessment":
    st.markdown("## 🧠 Player Assessment")
    st.write("This is the part that makes FUT TUT personal. Your answers directly change your recommended drills and training plan.")
    a = user["assessment"]
    p = user["profile"]

    with st.form("assessment_form"):
        name = st.text_input("What should FUT TUT call you?", value=p.get("name", ""))
        position = st.selectbox("What position do you mainly play?", POSITIONS, index=POSITIONS.index(p.get("position","Winger")) if p.get("position","Winger") in POSITIONS else 0)
        strengths = st.multiselect("What are your biggest strengths?", CATEGORIES, default=[x for x in a.get("strengths", []) if x in CATEGORIES])
        weaknesses = st.multiselect("What do you most want to improve?", CATEGORIES, default=[x for x in a.get("weaknesses", []) if x in CATEGORIES])
        confidence = st.slider("How confident do you feel in matches?", 1, 5, int(a.get("confidence", 3)), help="1 = not very confident, 5 = very confident")
        pressure = st.slider("How comfortable are you when you're under pressure?", 1, 5, int(a.get("pressure", 3)), help="1 = struggle under pressure, 5 = very comfortable")
        style = st.selectbox("What type of training do you prefer?", STYLES, index=STYLES.index(p.get("style","Balanced")) if p.get("style","Balanced") in STYLES else 0)
        goal = st.selectbox("What's your biggest goal right now?", GOALS, index=GOALS.index(a.get("goal", GOALS[0])) if a.get("goal", GOALS[0]) in GOALS else 0)
        training_days = st.slider("How many days per week do you want to train?", 1, 7, int(a.get("training_days", 3)))
        submitted = st.form_submit_button("Save Assessment & Build My Plan")

    if submitted:
        if not weaknesses:
            st.error("Pick at least one area you want to improve so FUT TUT can personalize your plan.")
        else:
            user["profile"]["name"] = name.strip() or st.session_state.logged_in_user
            user["profile"]["position"] = position
            user["profile"]["style"] = style
            user["assessment"] = {
                "completed": True,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "confidence": confidence,
                "pressure": pressure,
                "goal": goal,
                "training_days": training_days,
            }
            update_user(user)
            st.success("Assessment saved — your recommendations are now personalized.")
            st.session_state.page = "Training Plan"
            st.rerun()

# ---------- AI Coach ----------
elif st.session_state.page == "AI Coach":
    st.markdown("## 🤖 FUT TUT AI Coach")
    st.write("Ask about technique, drills, soccer IQ, match preparation, or how to train a skill.")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for msg in st.session_state.chat[-12:]:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])
    question = st.chat_input("Ask FUT TUT Coach something...")
    if question:
        st.session_state.chat.append({"role":"user","text":question})
        answer = ask_ai(user, question)
        st.session_state.chat.append({"role":"assistant","text":answer})
        st.rerun()

# ---------- Progress ----------
elif st.session_state.page == "Progress":
    st.markdown("## 📈 Progress")
    c1,c2,c3 = st.columns(3)
    c1.metric("Level", level_from_xp(user["xp"]))
    c2.metric("Total XP", user["xp"])
    c3.metric("Unique drills", len(user["completed"]))

    st.markdown("### Weekly goal")
    st.progress(min(1.0, user["weekly_sessions"] / max(1, user["weekly_goal"])))
    st.write(f"{user['weekly_sessions']} / {user['weekly_goal']} training sessions this week")

    st.markdown("### Categories")
    for cat in CATEGORIES:
        count = sum(1 for x in user["completed"] if DRILL_INDEX.get(x, {}).get("category") == cat)
        st.write(f"**{cat}** — {count} unique drills completed")

    st.markdown("### Recent training")
    if not user["recent_sessions"]:
        st.info("Complete a drill and your training history will appear here.")
    else:
        for s in user["recent_sessions"][:10]:
            st.markdown(f"- **{s['drill']}** · {s['category']} · +{s['xp']} XP · {s['date'][:10]}")

# ---------- Profile ----------
elif st.session_state.page == "Profile":
    st.markdown("## 👤 Profile")
    with st.form("profile_form"):
        name = st.text_input("Display name", value=user["profile"].get("name", ""))
        position = st.selectbox("Position", POSITIONS, index=POSITIONS.index(user["profile"].get("position","Winger")))
        style = st.selectbox("Training style", STYLES, index=STYLES.index(user["profile"].get("style","Balanced")))
        weekly_goal = st.slider("Weekly session goal", 1, 7, int(user.get("weekly_goal", 5)))
        save = st.form_submit_button("Save Profile")
    if save:
        user["profile"]["name"] = name.strip() or st.session_state.logged_in_user
        user["profile"]["position"] = position
        user["profile"]["style"] = style
        user["weekly_goal"] = weekly_goal
        update_user(user)
        st.success("Profile saved.")
        st.rerun()

    st.markdown("### Account")
    st.caption("Your FUT TUT progress is stored under your account in the app's data file.")
    if st.button("Retake Player Assessment"):
        user["assessment"]["completed"] = False
        update_user(user)
        st.session_state.page = "Assessment"
        st.rerun()

# ---------- Small level-up notice ----------
if st.session_state.get("last_level_up"):
    st.success(f"🔥 LEVEL UP! You reached Level {level_from_xp(user['xp'])}.")
    st.session_state.last_level_up = False
