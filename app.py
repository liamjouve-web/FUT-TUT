import os
import json
import random
import tempfile
import base64
from datetime import date, datetime, timedelta

import streamlit as st

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================================================
# FUT TUT — CONFIG
# =========================================================
st.set_page_config(
    page_title="FUT TUT ⚽",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "futtut_data.json"
MAX_LEVEL = 20
XP_PER_LEVEL = 250

CATEGORIES = ["Finishing", "Dribbling", "First Touch", "Passing", "Speed", "Soccer IQ"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
POSITIONS = ["Winger", "Striker", "Midfielder", "Defender", "Fullback", "Goalkeeper"]
STYLES = ["Balanced", "Technical", "Match-like"]

# =========================================================
# DRILL LIBRARY
# =========================================================
DRILL_SEEDS = {
    "Finishing": [
        ("One-Touch Finishing", "Beginner", "10 min", "20 finishes", "Finish quickly after receiving a pass.", "Quick decision-making and clean contact."),
        ("Near-Post Finishing", "Beginner", "10 min", "15 finishes", "Attack from a wide angle and finish into the near corner.", "Body shape and placement."),
        ("Far-Corner Placement", "Beginner", "12 min", "20 finishes", "Build consistency placing shots away from the keeper.", "Accuracy over power."),
        ("Moving Ball Finish", "Intermediate", "15 min", "20 finishes", "Receive while moving and finish with your next touch.", "Control at speed."),
        ("Cutback Finishing", "Intermediate", "15 min", "20 finishes", "Attack the box and finish cutback passes.", "Timing your run."),
        ("Weak-Foot Finishing", "Intermediate", "15 min", "15 finishes", "Build confidence finishing with your weaker foot.", "Clean technique."),
        ("First-Time Volley", "Advanced", "15 min", "15 finishes", "Attack aerial service and finish cleanly.", "Timing and balance."),
        ("Pressure Finishing", "Advanced", "20 min", "20 finishes", "Create a shooting angle while pressure closes you down.", "Speed of decision-making."),
        ("Three-Zone Finishing", "Advanced", "20 min", "30 finishes", "Finish from central, left and right shooting zones.", "Adaptability."),
        ("Rebound Finishing", "Advanced", "15 min", "20 finishes", "React quickly to second-ball opportunities around goal.", "Reactions and positioning."),
    ],
    "Dribbling": [
        ("Cone Slalom", "Beginner", "10 min", "8 runs", "Build close control through a cone slalom.", "Close control."),
        ("Inside-Outside", "Beginner", "10 min", "5 x 30 sec", "Develop rhythm with inside and outside touches.", "Touch rhythm."),
        ("Figure Eight", "Beginner", "12 min", "8 rounds", "Improve turning and close control.", "Turning mechanics."),
        ("Change of Direction", "Intermediate", "15 min", "12 attacks", "Explode away after a sharp change of direction.", "Change of pace."),
        ("Elastico Reps", "Intermediate", "12 min", "30 attempts", "Practice the elastico from slow to match speed.", "Clean contact and timing."),
        ("1v1 Attack", "Intermediate", "15 min", "12 attacks", "Combine feints with acceleration in 1v1 situations.", "Timing and confidence."),
        ("Tight-Space Dribbling", "Advanced", "15 min", "5 x 45 sec", "Control the ball in a small area under constant movement.", "Control under pressure."),
        ("Speed Dribble", "Advanced", "15 min", "10 runs", "Combine longer touches with high-speed running.", "Ball control at speed."),
        ("Move + Burst", "Advanced", "18 min", "12 attacks", "Use a move to beat a defender and explode away.", "Game-speed dribbling."),
        ("Stop-Start Dribbling", "Advanced", "15 min", "12 runs", "Change speed repeatedly to create separation.", "Changes of pace."),
    ],
    "First Touch": [
        ("Wall First Touch", "Beginner", "10 min", "50 touches", "Improve control from simple wall passes.", "Soft first touch."),
        ("Open-Body Receive", "Beginner", "12 min", "30 reps", "Receive while opening your body to the field.", "Scanning and body shape."),
        ("First Touch Across Body", "Beginner", "10 min", "30 touches", "Move the ball across your body after receiving.", "Directional control."),
        ("Turn on First Touch", "Intermediate", "15 min", "25 turns", "Receive and turn in one fluid movement.", "Touch direction."),
        ("High-Ball Control", "Intermediate", "15 min", "20 controls", "Bring bouncing or aerial balls under control.", "Cushioning the ball."),
        ("Receive Under Pressure", "Intermediate", "15 min", "20 reps", "Control while reacting to a nearby defender.", "Awareness before receiving."),
        ("Back-Foot Receiving", "Advanced", "15 min", "30 reps", "Receive on the back foot to keep play moving.", "Playing forward quickly."),
        ("First Touch Escape", "Advanced", "18 min", "20 escapes", "Use the first touch to escape a tight situation.", "First touch under pressure."),
        ("Match-Speed Receiving", "Advanced", "20 min", "30 reps", "Practice receiving at realistic game speed.", "Real-game control."),
        ("Receive-and-Play", "Advanced", "18 min", "25 reps", "Receive, orient and play the next action quickly.", "Speed from control to action."),
    ],
    "Passing": [
        ("Two-Touch Wall Passing", "Beginner", "10 min", "50 passes", "Build passing rhythm with a wall.", "Technique and consistency."),
        ("One-Touch Wall Passing", "Beginner", "10 min", "50 passes", "Improve speed with one-touch combinations.", "Passing rhythm."),
        ("Passing Gates", "Beginner", "12 min", "40 passes", "Pass accurately through small cone gates.", "Accuracy."),
        ("Third-Man Passing", "Intermediate", "15 min", "20 combinations", "Improve combination play with a third player.", "Movement after passing."),
        ("Split Passes", "Intermediate", "15 min", "25 passes", "Thread passes through narrow spaces.", "Weight and precision."),
        ("Long-Passing Technique", "Intermediate", "18 min", "25 passes", "Practice controlled longer passes.", "Balance and contact."),
        ("Weak-Foot Passing", "Advanced", "15 min", "50 passes", "Develop confidence passing with your weaker side.", "Technique under repetition."),
        ("Pressure Passing", "Advanced", "18 min", "30 passes", "Make quick passing decisions under pressure.", "Speed of thought."),
        ("Switch of Play", "Advanced", "20 min", "20 switches", "Practice changing the point of attack.", "Awareness and execution."),
        ("Third-Line Combination", "Advanced", "18 min", "20 combinations", "Link three passing lanes with movement.", "Speed and awareness."),
    ],
    "Speed": [
        ("Acceleration Starts", "Beginner", "10 min", "8 starts", "Practice quick acceleration over short distances.", "First few steps."),
        ("Cone Sprints", "Beginner", "12 min", "8 sprints", "Build repeated sprint quality.", "Quality speed."),
        ("Reaction Sprint", "Beginner", "12 min", "10 reactions", "React quickly to a direction cue.", "Reaction speed."),
        ("Sprint + Ball", "Intermediate", "15 min", "8 runs", "Combine acceleration with ball control.", "Speed with control."),
        ("Change-of-Direction Sprint", "Intermediate", "15 min", "8 runs", "Accelerate, cut and accelerate again.", "Deceleration and re-acceleration."),
        ("Curved Sprint Runs", "Intermediate", "15 min", "8 runs", "Practice curved movements useful for attacking runs.", "Running angle."),
        ("Repeated Sprint", "Advanced", "18 min", "10 sprints", "Practice repeated bursts with controlled recovery.", "Consistent effort."),
        ("Explosive First Step", "Advanced", "15 min", "10 starts", "Improve your first movement when attacking space.", "Acceleration mechanics."),
        ("Game-Speed Running", "Advanced", "20 min", "10 runs", "Mix jogs, bursts and changes like a match.", "Changing gears."),
        ("Burst + Recover", "Advanced", "18 min", "10 rounds", "Alternate short bursts and controlled recovery.", "Repeatable acceleration."),
    ],
    "Soccer IQ": [
        ("Scanning Drill", "Beginner", "10 min", "20 receives", "Build the habit of checking your surroundings before receiving.", "Scanning."),
        ("Shoulder Check", "Beginner", "10 min", "30 checks", "Practice checking both shoulders before receiving.", "Awareness."),
        ("Find the Space", "Beginner", "12 min", "20 movements", "Move away from defenders into open space.", "Movement without the ball."),
        ("Third-Man Run", "Intermediate", "15 min", "15 combinations", "Recognize when to run beyond the receiver.", "Timing."),
        ("Winger Decision-Making", "Intermediate", "15 min", "20 decisions", "Choose between dribbling, passing and crossing.", "Decision-making."),
        ("When to Carry", "Intermediate", "15 min", "20 decisions", "Recognize when carrying is better than passing.", "Recognizing space."),
        ("Defensive Scanning", "Advanced", "15 min", "20 checks", "Track runners while staying aware of the ball.", "Positioning."),
        ("Final-Third Choices", "Advanced", "18 min", "20 decisions", "Improve choices around the box.", "Fast decisions."),
        ("Match Reading", "Advanced", "20 min", "20 situations", "Recognize what the game is asking for.", "Understanding the game."),
        ("Space + Timing", "Advanced", "18 min", "20 decisions", "Combine movement, scanning and timing.", "Reading the next action."),
    ],
}


def build_drills():
    drills = []
    for category, rows in DRILL_SEEDS.items():
        for name, level, time_, reps, description, focus in rows:
            drills.append({
                "name": name,
                "category": category,
                "level": level,
                "time": time_,
                "reps": reps,
                "description": description,
                "equipment": "Ball, cones, partner" if category == "Soccer IQ" else "Ball, cones",
                "steps": [
                    "Set up your space and equipment.",
                    "Start at a controlled pace so the technique stays clean.",
                    "Perform the drill with your selected repetitions.",
                    "Repeat from both sides when the drill allows it.",
                    "Only add speed or pressure when your control is consistent.",
                ],
                "focus": focus,
                "mistakes": "Rushing the repetition, losing balance, or taking a touch without a clear purpose.",
                "progression": "Add speed, reduce space, use the weaker foot, or add a passive defender.",
                "tip": "Quality repetitions matter more than forcing speed.",
            })
    return drills


DRILLS = build_drills()
DRILL_BY_NAME = {d["name"]: d for d in DRILLS}

# =========================================================
# DATA
# =========================================================
DEFAULT_DATA = {
    "xp": 0,
    "sessions": 0,
    "completed": [],
    "completion_counts": {},
    "player_name": "Player",
    "favorite_position": "Winger",
    "weekly_goal": 5,
    "weekly_sessions": 0,
    "week_key": "",
    "training_dates": [],
    "challenge_claimed": [],
    "recent_sessions": [],
}


def fresh_defaults():
    return json.loads(json.dumps(DEFAULT_DATA))


def load_data():
    if not os.path.exists(DATA_FILE):
        return fresh_defaults()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return fresh_defaults()
        saved = fresh_defaults()
        saved.update(raw)
        for key, expected_type in {
            "completed": list,
            "completion_counts": dict,
            "training_dates": list,
            "challenge_claimed": list,
            "recent_sessions": list,
        }.items():
            if not isinstance(saved.get(key), expected_type):
                saved[key] = expected_type()
        repaired = []
        for item in saved["recent_sessions"]:
            if isinstance(item, dict):
                repaired.append({
                    "name": item.get("name", "Drill"),
                    "category": item.get("category", "Training"),
                    "xp": int(item.get("xp", 0)),
                    "date": item.get("date", ""),
                })
        saved["recent_sessions"] = repaired[:10]
        return saved
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return fresh_defaults()


data = load_data()


def save_data():
    temp = DATA_FILE + ".tmp"
    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp, DATA_FILE)
    except OSError:
        if os.path.exists(temp):
            try:
                os.remove(temp)
            except OSError:
                pass


# =========================================================
# SESSION STATE
# =========================================================
STATE_DEFAULTS = {
    "intro_seen": False,
    "page": "Home",
    "selected_drill": None,
    "recommended_drill": None,
    "active_session": False,
    "session_plan": [],
    "session_index": 0,
    "session_name": "",
    "session_total_xp": 0,
    "session_bonus_given": False,
    "coach_plan": [],
    "coach_plan_name": "",
    "video_analysis": "",
    "video_signature": "",
}
for key, value in STATE_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CORE HELPERS
# =========================================================
def current_week_key():
    return date.today().strftime("%Y-%W")


def reset_week_if_needed():
    if data.get("week_key") != current_week_key():
        data["week_key"] = current_week_key()
        data["weekly_sessions"] = 0
        save_data()


def get_streak():
    dates = set(data.get("training_dates", []))
    if not dates:
        return 0
    streak = 0
    day = date.today()
    while day.isoformat() in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def record_training_day():
    today = date.today().isoformat()
    if today not in data["training_dates"]:
        data["training_dates"].append(today)
    data["weekly_sessions"] = int(data.get("weekly_sessions", 0)) + 1
    save_data()


def get_level(xp):
    return min(MAX_LEVEL, xp // XP_PER_LEVEL + 1)


def level_progress(xp):
    level = get_level(xp)
    if level >= MAX_LEVEL:
        return 1.0
    return max(0.0, min(1.0, (xp - (level - 1) * XP_PER_LEVEL) / XP_PER_LEVEL))


def next_level_text(xp):
    level = get_level(xp)
    if level >= MAX_LEVEL:
        return "MAX LEVEL"
    return f"{level * XP_PER_LEVEL - xp} XP to Level {level + 1}"


def completion_xp(drill):
    repeats = int(data["completion_counts"].get(drill["name"], 0))
    if repeats > 0:
        return 5
    return {"Beginner": 25, "Intermediate": 30, "Advanced": 35}[drill["level"]]


def complete_drill(drill):
    gain = completion_xp(drill)
    name = drill["name"]
    data["xp"] += gain
    data["sessions"] += 1
    data["completed"].append(name)
    data["completion_counts"][name] = int(data["completion_counts"].get(name, 0)) + 1
    data["recent_sessions"].insert(0, {
        "name": name,
        "category": drill["category"],
        "xp": gain,
        "date": datetime.now().strftime("%b %d, %Y"),
    })
    data["recent_sessions"] = data["recent_sessions"][:10]
    record_training_day()
    return gain


def category_rating(category):
    names = [d["name"] for d in DRILLS if d["category"] == category]
    completed_count = sum(int(data["completion_counts"].get(n, 0)) for n in names)
    return min(99, 50 + completed_count * 4)


def choose_recommendation(exclude=None):
    options = [d for d in DRILLS if d["name"] != exclude]
    options.sort(key=lambda d: int(data["completion_counts"].get(d["name"], 0)))
    pool = options[:max(8, len(options) // 3)] or options
    chosen = random.choice(pool)
    st.session_state.recommended_drill = chosen["name"]
    return chosen


def get_recommendation():
    name = st.session_state.recommended_drill
    if name in DRILL_BY_NAME:
        return DRILL_BY_NAME[name]
    seed = date.today().toordinal() + int(data["xp"])
    chosen = random.Random(seed).choice(DRILLS)
    st.session_state.recommended_drill = chosen["name"]
    return chosen


def go_to(page):
    st.session_state.page = page
    st.rerun()


# =========================================================
# CHALLENGES / ACHIEVEMENTS
# =========================================================
def challenges():
    out = []
    for category in CATEGORIES:
        names = [d["name"] for d in DRILLS if d["category"] == category][:3]
        out.append({"name": f"{category} Starter", "category": category, "drills": names, "reward": 75})
    return out


def challenge_complete(challenge):
    completed = set(data["completed"])
    return all(name in completed for name in challenge["drills"])


def claim_challenge(challenge):
    key = challenge["name"]
    if key in data["challenge_claimed"] or not challenge_complete(challenge):
        return False
    data["xp"] += challenge["reward"]
    data["challenge_claimed"].append(key)
    save_data()
    return True


def achievements():
    completed = set(data["completed"])
    unique = len(completed)
    total = len(DRILLS)
    categories_done = {d["category"] for d in DRILLS if d["name"] in completed}
    return [
        ("First Drill", "Complete your first drill.", data["sessions"] >= 1),
        ("Skill Builder", "Complete 10 different drills.", unique >= 10),
        ("Century", "Earn 100 XP.", data["xp"] >= 100),
        ("All-Rounder", "Train in every category.", len(categories_done) == len(CATEGORIES)),
        ("Twenty-Five", "Complete 25 different drills.", unique >= 25),
        ("Halfway", f"Complete at least half of all {total} drills.", unique >= total / 2),
        ("Level 5", "Reach Level 5.", get_level(data["xp"]) >= 5),
        ("Complete Player", "Complete every drill.", unique >= total),
    ]


# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
.stApp {
    background:
      radial-gradient(circle at 6% 12%, rgba(255,255,255,.85) 0 1px, transparent 2px),
      radial-gradient(circle at 14% 72%, rgba(255,255,255,.65) 0 1px, transparent 2px),
      radial-gradient(circle at 25% 29%, rgba(255,255,255,.8) 0 1px, transparent 2px),
      radial-gradient(circle at 36% 86%, rgba(255,255,255,.7) 0 1px, transparent 2px),
      radial-gradient(circle at 48% 15%, rgba(255,255,255,.8) 0 1px, transparent 2px),
      radial-gradient(circle at 59% 56%, rgba(255,255,255,.65) 0 1px, transparent 2px),
      radial-gradient(circle at 70% 11%, rgba(255,255,255,.78) 0 1px, transparent 2px),
      radial-gradient(circle at 80% 77%, rgba(255,255,255,.7) 0 1px, transparent 2px),
      radial-gradient(circle at 92% 33%, rgba(255,255,255,.75) 0 1px, transparent 2px),
      #000 !important;
    color: #fff;
}
.block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 4rem; }
h1,h2,h3,h4,p,label,span,div { font-family: Arial, Helvetica, sans-serif; }
h1,h2,h3,h4 { color:#fff !important; }
p { color:#cfcfcf; }
section[data-testid="stSidebar"] { background:#050505 !important; border-right:1px solid #222; }
section[data-testid="stSidebar"] * { color:#fff !important; }
.hero { background:linear-gradient(145deg,rgba(255,255,255,.09),rgba(255,255,255,.025)); border:1px solid #303030; border-radius:26px; padding:32px; margin-bottom:22px; box-shadow:0 20px 80px rgba(0,0,0,.2); }
.card { background:rgba(12,12,12,.96); border:1px solid #282828; border-radius:20px; padding:22px; margin-bottom:16px; }
.eyebrow { color:#8c8c8c; text-transform:uppercase; letter-spacing:.12em; font-size:.76rem; font-weight:800; }
.big-title { font-size:clamp(2.5rem,6vw,5rem); font-weight:950; letter-spacing:-4px; line-height:.95; margin-top:5px; }
.stat-card { background:#0b0b0b; border:1px solid #272727; border-radius:18px; padding:19px; text-align:center; min-height:116px; }
.stat-num { font-size:2rem; font-weight:950; }
.stat-label { color:#888; font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; }
.stButton > button { background:#fff !important; color:#000 !important; border:1px solid #fff !important; border-radius:12px !important; min-height:46px !important; font-weight:850 !important; transition:.18s ease; }
.stButton > button:hover { background:#e9e9e9 !important; color:#000 !important; transform:translateY(-1px); }
/* White boxes = black text */
div[data-baseweb="select"] > div { background:#fff !important; color:#000 !important; border:1px solid #d8d8d8 !important; border-radius:12px !important; }
div[data-baseweb="select"] * { color:#000 !important; }
div[data-baseweb="select"] span { color:#000 !important; }
div[data-baseweb="select"] input { color:#000 !important; caret-color:#000 !important; }
div[data-baseweb="popover"] { background:#fff !important; border:1px solid #ddd !important; border-radius:14px !important; box-shadow:0 20px 60px rgba(0,0,0,.55) !important; overflow:hidden !important; }
div[data-baseweb="popover"] * { color:#000 !important; }
div[data-baseweb="menu"] { background:#fff !important; }
div[data-baseweb="menu"] li { background:#fff !important; color:#000 !important; }
div[data-baseweb="menu"] li * { color:#000 !important; }
div[data-baseweb="menu"] li:hover { background:#eee !important; color:#000 !important; }
div[data-baseweb="menu"] li:hover * { color:#000 !important; }
[role="listbox"] { background:#fff !important; color:#000 !important; }
[role="option"] { background:#fff !important; color:#000 !important; }
[role="option"] * { color:#000 !important; }
[role="option"]:hover,[role="option"][aria-selected="true"] { background:#eee !important; color:#000 !important; }
[role="option"]:hover *,[role="option"][aria-selected="true"] * { color:#000 !important; }
input,textarea { background:#fff !important; color:#000 !important; border:1px solid #d8d8d8 !important; border-radius:12px !important; }
input::placeholder,textarea::placeholder { color:#666 !important; }
[data-testid="stFileUploader"] { background:#0d0d0d !important; border:1px dashed #444 !important; border-radius:16px !important; }
[data-testid="stFileUploader"] * { color:#fff !important; }
details { background:#0c0c0c !important; border:1px solid #282828 !important; border-radius:14px !important; }
details summary { color:#fff !important; }
hr { border-color:#242424 !important; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# INTRO
# =========================================================
if not st.session_state.intro_seen:
    st.markdown("""
    <style>
    .intro { min-height:78vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
    .intro-title { font-size:clamp(3.5rem,9vw,7rem); font-weight:950; letter-spacing:-6px; animation:pop .9s ease-out; }
    .intro-sub { margin-top:10px; color:#aaa; font-size:.9rem; letter-spacing:.18em; font-weight:800; }
    @keyframes pop { 0%{transform:scale(.65);opacity:0} 65%{transform:scale(1.08);opacity:1} 100%{transform:scale(1);opacity:1} }
    </style>
    <div class="intro"><div class="intro-title">FUT ⚽ TUT</div><div class="intro-sub">YOUR TRAINING. YOUR PROGRESS. YOUR GAME.</div></div>
    """, unsafe_allow_html=True)
    if st.button("ENTER FUT TUT ⚡", use_container_width=True):
        st.session_state.intro_seen = True
        st.rerun()
    st.stop()


# =========================================================
# SIDEBAR
# =========================================================
reset_week_if_needed()
PAGES = ["Home", "Training", "Start Session", "AI Coach", "Video Analysis", "Challenges", "Progress", "Profile"]

with st.sidebar:
    st.markdown("<div style='font-size:2rem;font-weight:950;'>FUT TUT ⚽</div>", unsafe_allow_html=True)
    st.caption("TRAIN. IMPROVE. PLAY.")

    picked = st.radio("Navigate", PAGES, index=PAGES.index(st.session_state.page), label_visibility="collapsed", key="nav")
    if picked != st.session_state.page:
        st.session_state.page = picked
        st.rerun()

    st.markdown("---")
    st.metric("Level", get_level(data["xp"]))
    st.metric("XP", data["xp"])
    st.metric("Streak", f"{get_streak()} 🔥")


# =========================================================
# DRILL CARD
# =========================================================
def render_drill(drill, actions=True, key_prefix="drill"):
    st.markdown(f"""
    <div class="card">
      <div class="eyebrow">{drill['category']} · {drill['level']}</div>
      <h2 style="margin-bottom:6px;">{drill['name']}</h2>
      <p>{drill['description']}</p>
      <div style="color:#aaa;margin-top:12px;">⏱ {drill['time']} &nbsp; • &nbsp; 🔁 {drill['reps']} &nbsp; • &nbsp; 🎯 {drill['focus']}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Drill details"):
        for i, step in enumerate(drill["steps"], 1):
            st.write(f"**{i}.** {step}")
        st.write(f"**Equipment:** {drill['equipment']}")
        st.write(f"**Common mistakes:** {drill['mistakes']}")
        st.write(f"**Progression:** {drill['progression']}")
        st.write(f"**Coach tip:** {drill['tip']}")

    if actions:
        a, b = st.columns(2)
        with a:
            if st.button("✅ Complete Drill", key=f"complete_{key_prefix}", use_container_width=True):
                gain = complete_drill(drill)
                choose_recommendation(exclude=drill["name"])
                st.success(f"+{gain} XP earned! ⚡")
                st.rerun()
        with b:
            if st.button("🔄 New Recommendation", key=f"new_{key_prefix}", use_container_width=True):
                choose_recommendation(exclude=drill["name"])
                st.rerun()


# =========================================================
# HOME
# =========================================================
if st.session_state.page == "Home":
    rec = get_recommendation()

    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">WELCOME BACK, {str(data['player_name']).upper()}</div>
      <div class="big-title">FUT TUT ⚽</div>
      <div style="color:#aaa;margin-top:14px;font-size:1.05rem;">YOUR TRAINING. YOUR PROGRESS. YOUR GAME.</div>
    </div>
    """, unsafe_allow_html=True)

    stats = [("XP", data["xp"]), ("Level", get_level(data["xp"])), ("Drills Completed", data["sessions"]), ("Day Streak", f"{get_streak()} 🔥")]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(f"<div class='stat-card'><div class='stat-num'>{value}</div><div class='stat-label'>{label}</div></div>", unsafe_allow_html=True)

    st.markdown("## Today's Recommendation")
    render_drill(rec, actions=False, key_prefix="home")

    a, b, c = st.columns(3)
    with a:
        if st.button("▶️ Start Drill", key="home_start", use_container_width=True):
            st.session_state.selected_drill = rec["name"]
            go_to("Training")
    with b:
        if st.button("🔄 Change Drill", key="home_change", use_container_width=True):
            choose_recommendation(exclude=rec["name"])
            st.rerun()
    with c:
        if st.button("🧠 AI Coach", key="home_coach", use_container_width=True):
            go_to("AI Coach")

    st.markdown("## Quick Start")
    a, b = st.columns(2)
    with a:
        st.markdown("<div class='card'><h3>⚡ Build a Session</h3><p>Choose your time, difficulty and style, then train through a complete plan.</p></div>", unsafe_allow_html=True)
        if st.button("Build Session", key="home_session", use_container_width=True):
            go_to("Start Session")
    with b:
        st.markdown("<div class='card'><h3>📈 Track Progress</h3><p>See skill ratings, XP, streaks, achievements and recent training.</p></div>", unsafe_allow_html=True)
        if st.button("View Progress", key="home_progress", use_container_width=True):
            go_to("Progress")


# =========================================================
# TRAINING
# =========================================================
elif st.session_state.page == "Training":
    st.title("Training ⚽")
    st.caption("Find a drill, study it, then complete it.")

    a, b, c = st.columns(3)
    with a:
        category = st.selectbox("Category", ["All"] + CATEGORIES, key="train_category")
    with b:
        difficulty = st.selectbox("Difficulty", ["All"] + LEVELS, key="train_difficulty")
    with c:
        search = st.text_input("Search", placeholder="Search drills...", key="train_search")

    filtered = DRILLS[:]
    if category != "All":
        filtered = [d for d in filtered if d["category"] == category]
    if difficulty != "All":
        filtered = [d for d in filtered if d["level"] == difficulty]
    if search.strip():
        q = search.strip().lower()
        filtered = [d for d in filtered if q in d["name"].lower() or q in d["description"].lower()]

    st.markdown(f"<div class='eyebrow'>{len(filtered)} DRILLS AVAILABLE</div>", unsafe_allow_html=True)

    if not filtered:
        st.warning("No drills match those filters.")
    else:
        names = [d["name"] for d in filtered]
        if st.session_state.selected_drill not in names:
            st.session_state.selected_drill = names[0]
        chosen_name = st.selectbox("Select Drill", names, index=names.index(st.session_state.selected_drill), key="train_selected")
        st.session_state.selected_drill = chosen_name
        render_drill(DRILL_BY_NAME[chosen_name], actions=True, key_prefix=f"training_{chosen_name}")


# =========================================================
# SESSION BUILDER
# =========================================================
elif st.session_state.page == "Start Session":
    st.title("Start a Session ⚡")

    if not st.session_state.active_session:
        a, b = st.columns(2)
        with a:
            session_category = st.selectbox("Category", ["Mixed"] + CATEGORIES, key="session_category")
            duration = st.selectbox("Duration", [15, 30, 45, 60], format_func=lambda x: f"{x} minutes", key="session_duration")
        with b:
            session_level = st.selectbox("Difficulty", ["Mixed"] + LEVELS, key="session_level")
            style = st.selectbox("Style", STYLES, key="session_style")

        preferred = set(CATEGORIES)
        if style == "Technical":
            preferred = {"First Touch", "Passing", "Dribbling"}
        elif style == "Match-like":
            preferred = {"Finishing", "Soccer IQ", "Speed", "Dribbling"}

        pool = DRILLS[:]
        if session_category != "Mixed":
            pool = [d for d in pool if d["category"] == session_category]
        elif style != "Balanced":
            styled = [d for d in pool if d["category"] in preferred]
            if styled:
                pool = styled
        if session_level != "Mixed":
            pool = [d for d in pool if d["level"] == session_level]

        target = min({15: 3, 30: 5, 45: 7, 60: 9}[duration], len(pool))
        st.info(f"This session will use {target} drills with no duplicates.")

        if st.button("🚀 Build My Session", key="build_session", use_container_width=True):
            shuffled = pool[:]
            random.shuffle(shuffled)
            st.session_state.session_plan = shuffled[:target]
            st.session_state.session_index = 0
            st.session_state.session_total_xp = 0
            st.session_state.session_bonus_given = False
            st.session_state.session_name = f"{style} {duration}-Minute Session"
            st.session_state.active_session = True
            st.rerun()

    else:
        plan = st.session_state.session_plan
        idx = st.session_state.session_index

        if idx < len(plan):
            current = plan[idx]
            st.markdown(f"<div class='hero'><div class='eyebrow'>{st.session_state.session_name}</div><h1>Drill {idx + 1} of {len(plan)}</h1><p>Session XP: {st.session_state.session_total_xp}</p></div>", unsafe_allow_html=True)
            st.progress((idx + 1) / len(plan), text=f"Progress {idx + 1}/{len(plan)}")
            render_drill(current, actions=False, key_prefix=f"session_{idx}")

            a, b = st.columns(2)
            with a:
                if st.button("✅ Complete Current Drill", key=f"session_complete_{idx}", use_container_width=True):
                    gain = complete_drill(current)
                    st.session_state.session_total_xp += gain
                    st.session_state.session_index += 1
                    choose_recommendation(exclude=current["name"])
                    st.rerun()
            with b:
                if st.button("❌ End Session", key="end_session", use_container_width=True):
                    st.session_state.active_session = False
                    st.session_state.session_plan = []
                    st.session_state.session_index = 0
                    st.session_state.session_total_xp = 0
                    st.session_state.session_bonus_given = False
                    st.rerun()
        else:
            if not st.session_state.session_bonus_given:
                data["xp"] += 50
                st.session_state.session_total_xp += 50
                st.session_state.session_bonus_given = True
                save_data()

            st.success("SESSION COMPLETE! 🏆")
            st.markdown(f"<div class='hero'><div class='eyebrow'>FULL SESSION FINISHED</div><h1>+{st.session_state.session_total_xp} XP</h1><p>You completed all {len(plan)} drills and received the +50 session bonus.</p></div>", unsafe_allow_html=True)

            if st.button("🔥 Build Another Session", key="another_session", use_container_width=True):
                st.session_state.active_session = False
                st.session_state.session_plan = []
                st.session_state.session_index = 0
                st.session_state.session_total_xp = 0
                st.session_state.session_bonus_given = False
                st.rerun()


# =========================================================
# AI COACH
# =========================================================
elif st.session_state.page == "AI Coach":
    st.title("AI Coach 🧠⚽")
    st.caption("Build a focused plan around your position and priorities.")

    a, b = st.columns(2)
    with a:
        position = st.selectbox("Position", POSITIONS, index=POSITIONS.index(data["favorite_position"]) if data["favorite_position"] in POSITIONS else 0, key="coach_position")
        focus = st.selectbox("Main Focus", ["Confidence", "Dribbling", "Finishing", "First Touch", "Passing", "Speed", "Soccer IQ", "All-Around"], key="coach_focus")
    with b:
        duration = st.selectbox("Duration", [20, 30, 45, 60], format_func=lambda x: f"{x} minutes", key="coach_duration")
        style = st.selectbox("Style", STYLES, key="coach_style")

    role_preferences = {
        "Winger": ["Dribbling", "First Touch", "Speed", "Finishing", "Soccer IQ"],
        "Striker": ["Finishing", "First Touch", "Dribbling", "Speed", "Soccer IQ"],
        "Midfielder": ["Passing", "First Touch", "Soccer IQ", "Dribbling", "Speed"],
        "Defender": ["First Touch", "Passing", "Soccer IQ", "Speed", "Dribbling"],
        "Fullback": ["Speed", "Passing", "First Touch", "Dribbling", "Soccer IQ"],
        "Goalkeeper": ["First Touch", "Passing", "Soccer IQ"],
    }
    preferred = role_preferences[position][:]
    if style == "Technical":
        preferred = ["First Touch", "Passing", "Dribbling"] + preferred
    elif style == "Match-like":
        preferred = ["Soccer IQ", "Finishing", "Speed", "Dribbling"] + preferred

    pool = []
    seen = set()
    for category_name in preferred:
        for drill in DRILLS:
            focused = focus in {"Confidence", "All-Around"} or focus not in CATEGORIES or drill["category"] == focus
            if drill["category"] == category_name and focused and drill["name"] not in seen:
                seen.add(drill["name"])
                pool.append(drill)
    if len(pool) < 3:
        pool = DRILLS[:]

    target = {20: 3, 30: 4, 45: 6, 60: 8}[duration]

    if st.button("🧠 Generate Coach Plan", key="generate_coach", use_container_width=True):
        randomized = pool[:]
        random.shuffle(randomized)
        st.session_state.coach_plan = randomized[:min(target, len(randomized))]
        st.session_state.coach_plan_name = f"{position} · {focus}"
        st.rerun()

    if st.session_state.coach_plan:
        st.markdown(f"<div class='hero'><div class='eyebrow'>COACH PLAN</div><h2>{st.session_state.coach_plan_name}</h2><p>Built around your position, focus, duration and style.</p></div>", unsafe_allow_html=True)
        for i, drill in enumerate(st.session_state.coach_plan, 1):
            st.markdown(f"<div class='card'><div class='eyebrow'>DRILL {i}</div><h3>{drill['name']}</h3><p>{drill['description']}</p><div style='color:#aaa;'>{drill['category']} · {drill['level']} · {drill['time']}</div></div>", unsafe_allow_html=True)
        if st.button("▶️ Start This Coach Plan", key="start_coach_plan", use_container_width=True):
            st.session_state.session_plan = st.session_state.coach_plan[:]
            st.session_state.session_index = 0
            st.session_state.session_total_xp = 0
            st.session_state.session_bonus_given = False
            st.session_state.session_name = st.session_state.coach_plan_name
            st.session_state.active_session = True
            go_to("Start Session")


# =========================================================
# VIDEO ANALYSIS
# =========================================================
elif st.session_state.page == "Video Analysis":
    st.title("Video Analysis 🎥⚽")
    st.caption("Upload a soccer clip and get AI feedback based on sampled frames.")

    video = st.file_uploader("Upload a soccer video", type=["mp4", "mov", "avi", "mkv", "webm"], key="video_upload")
    focus = st.selectbox("Analysis focus", ["Overall performance", "Dribbling", "First touch", "Passing", "Finishing", "Movement", "Decision-making"], key="video_focus")
    st.info("The AI reviews sampled frames. It is coaching feedback, not a medical or professional biomechanics assessment.")

    def extract_frames(uploaded_file, max_frames=8):
        if cv2 is None:
            raise RuntimeError("OpenCV is not installed. Run: pip install opencv-python")
        suffix = os.path.splitext(uploaded_file.name)[1] or ".mp4"
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(uploaded_file.getbuffer())
                temp_path = temp.name
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise RuntimeError("Could not open the video.")
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
            if total_frames <= 0:
                raise RuntimeError("The video has no readable frames.")
            positions = [int(i * max(total_frames - 1, 1) / max(max_frames - 1, 1)) for i in range(max_frames)]
            frames = []
            for frame_no in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ok, frame = cap.read()
                if not ok:
                    continue
                h, w = frame.shape[:2]
                if w > 1280:
                    nw = 1280
                    nh = int(h * nw / w)
                    frame = cv2.resize(frame, (nw, nh))
                ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                if ok:
                    frames.append({"image": base64.b64encode(encoded.tobytes()).decode("utf-8"), "timestamp": frame_no / fps if fps > 0 else 0})
            cap.release()
            if not frames:
                raise RuntimeError("No usable frames could be extracted.")
            return frames
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def get_openai_client():
        if OpenAI is None:
            return None
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("OPENAI_API_KEY")
            except Exception:
                api_key = None
        if not api_key:
            return None
        return OpenAI(api_key=api_key)

    def analyze_video(frames, focus_text):
        client = get_openai_client()
        if client is None:
            raise RuntimeError("OpenAI is not configured. Set OPENAI_API_KEY in your environment or Streamlit secrets.")

        content = [{"type": "input_text", "text": f"""
You are an encouraging soccer coach reviewing sampled frames from a player's training video.
Focus: {focus_text}
Only describe things that are reasonably visible. Do not claim exact speed, force, injury risk, or measurements that cannot be established from images.
Use exactly these sections:
## OVERALL
## WHAT LOOKS GOOD
## TOP 3 IMPROVEMENTS
## TECHNIQUE
## MATCH TRANSFER
## NEXT DRILLS
## COACH VERDICT
Be specific, practical and encouraging.
"""}]

        for frame in frames:
            content.append({
                "type": "input_image",
                "image_url": "data:image/jpeg;base64," + frame["image"],
                "detail": "low",
            })

        model = os.environ.get("FUT_TUT_AI_MODEL", "gpt-5.6-luna")
        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": content}],
        )
        return response.output_text

    if video:
        st.video(video)
        if st.button("🔎 Analyze My Video", key="analyze_video", use_container_width=True):
            try:
                signature = f"{video.name}|{video.size}|{focus}"
                with st.spinner("Reviewing the clip..."):
                    frames = extract_frames(video)
                    result = analyze_video(frames, focus)
                st.session_state.video_analysis = result
                st.session_state.video_signature = signature
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.video_analysis:
        st.markdown("## AI Coach Report")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(st.session_state.video_analysis)
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# CHALLENGES
# =========================================================
elif st.session_state.page == "Challenges":
    st.title("Challenges 🏆")
    st.caption("Complete the first three drills in a category to unlock +75 XP once.")

    for challenge in challenges():
        done_count = sum(1 for name in challenge["drills"] if name in data["completed"])
        claimed = challenge["name"] in data["challenge_claimed"]
        st.markdown(f"<div class='card'><div class='eyebrow'>{challenge['category']}</div><h2>{challenge['name']}</h2><p>{done_count}/3 completed · Reward +{challenge['reward']} XP</p></div>", unsafe_allow_html=True)
        for name in challenge["drills"]:
            st.write(f"{'✅' if name in data['completed'] else '⬜'} {name}")

        if claimed:
            st.success("Reward already claimed ✅")
        elif challenge_complete(challenge):
            if st.button(f"🎁 Claim +{challenge['reward']} XP", key=f"claim_{challenge['name']}", use_container_width=True):
                if claim_challenge(challenge):
                    st.success("Reward claimed! 🏆")
                    st.rerun()
                else:
                    st.warning("That reward has already been claimed.")
        else:
            st.info("Complete all three drills to unlock this reward.")


# =========================================================
# PROGRESS
# =========================================================
elif st.session_state.page == "Progress":
    st.title("Progress 📈")
    st.progress(level_progress(data["xp"]), text=next_level_text(data["xp"]))

    stats = [("XP", data["xp"]), ("Level", get_level(data["xp"])), ("Drills Completed", data["sessions"]), ("Streak", f"{get_streak()} 🔥")]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, stats):
        with col:
            st.metric(label, value)

    st.markdown("## Skill Ratings")
    cols = st.columns(3)
    for i, category in enumerate(CATEGORIES):
        with cols[i % 3]:
            rating = category_rating(category)
            st.markdown(f"<div class='card'><div class='eyebrow'>{category}</div><div class='stat-num'>{rating}</div><div class='stat-label'>Skill Rating</div></div>", unsafe_allow_html=True)
            st.progress(rating / 99)

    st.markdown("## Weekly Goal")
    goal = max(1, int(data.get("weekly_goal", 5)))
    weekly = int(data.get("weekly_sessions", 0))
    st.write(f"**{weekly}/{goal} training days**")
    st.progress(min(1.0, weekly / goal))

    st.markdown("## Recent Training")
    if not data["recent_sessions"]:
        st.info("No completed drills yet.")
    else:
        for item in data["recent_sessions"]:
            name = item.get("name", "Drill")
            category = item.get("category", "Training")
            xp = item.get("xp", 0)
            when = item.get("date", "")
            st.write(f"⚽ **{name}** — {category} — +{xp} XP")
            if when:
                st.caption(str(when))

    st.markdown("## Achievements")
    for name, description, unlocked in achievements():
        icon = "🏆" if unlocked else "🔒"
        st.markdown(f"<div class='card'><div style='font-size:1.1rem;font-weight:900;'>{icon} {name}</div><div style='color:#999;margin-top:5px;'>{description}</div></div>", unsafe_allow_html=True)


# =========================================================
# PROFILE
# =========================================================
elif st.session_state.page == "Profile":
    st.title("Profile 👤")

    player_name = st.text_input("Player Name", value=str(data["player_name"]), key="profile_name")
    position = st.selectbox("Favorite Position", POSITIONS, index=POSITIONS.index(data["favorite_position"]) if data["favorite_position"] in POSITIONS else 0, key="profile_position")
    goal = st.number_input("Weekly Training Goal", min_value=1, max_value=14, value=max(1, min(14, int(data["weekly_goal"]))), step=1, key="profile_goal")

    if st.button("💾 Save Profile", key="save_profile", use_container_width=True):
        data["player_name"] = player_name.strip() or "Player"
        data["favorite_position"] = position
        data["weekly_goal"] = int(goal)
        save_data()
        st.success("Profile saved! ✅")
        st.rerun()

    st.markdown("## Player")
    a, b, c = st.columns(3)
    with a:
        st.metric("Name", data["player_name"])
    with b:
        st.metric("Position", data["favorite_position"])
    with c:
        st.metric("Weekly Goal", f"{data['weekly_goal']} days")
