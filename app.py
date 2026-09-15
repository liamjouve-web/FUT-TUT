import os
import json
import random
import re
import time
import html
import difflib
from datetime import datetime, date, timedelta

import streamlit as st
import streamlit.components.v1 as components

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# =========================================================
# FUT TUT 3.1 — mobile-first soccer training app
# =========================================================

st.set_page_config(
    page_title="FUT TUT ⚽",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "futtut_data.json"
VIDEO_DIR = "videos"
XP_PER_LEVEL = 250
MAX_LEVEL = 20

CATEGORIES = ["Finishing", "Dribbling", "First Touch", "Passing", "Speed", "Soccer IQ"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
POSITIONS = ["Winger", "Striker", "Midfielder", "Defender", "Fullback", "Goalkeeper"]
STYLES = ["Balanced", "Technical", "Match-like"]

# Put hosted MP4 URLs here later. Key = drill video_key generated below.
VIDEO_URLS = {}


# =========================================================
# DRILLS
# =========================================================

DRILL_SEEDS = {
    "Finishing": [
        ("One-Touch Finishing", "Beginner", "10 min", "20 finishes", "Finish quickly after receiving a pass.", "Quick decisions and clean contact."),
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
        ("Inside-Outside", "Beginner", "10 min", "5 × 30 sec", "Develop rhythm with inside and outside touches.", "Touch rhythm."),
        ("Figure Eight", "Beginner", "12 min", "8 rounds", "Improve turning and close control.", "Turning mechanics."),
        ("Change of Direction", "Intermediate", "15 min", "12 attacks", "Explode away after a sharp change of direction.", "Change of pace."),
        ("Elastico Reps", "Intermediate", "12 min", "30 attempts", "Practice the elastico from slow to match speed.", "Clean contact and timing."),
        ("1v1 Attack", "Intermediate", "15 min", "12 attacks", "Combine feints with acceleration in 1v1 situations.", "Timing and confidence."),
        ("Tight-Space Dribbling", "Advanced", "15 min", "5 × 45 sec", "Control the ball in a small area under constant movement.", "Control under pressure."),
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
        for i, (name, level, duration, reps, description, focus) in enumerate(rows):
            key = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            drills.append({
                "id": f"{category.lower().replace(' ', '_')}_{i+1}",
                "name": name,
                "category": category,
                "level": level,
                "time": duration,
                "reps": reps,
                "description": description,
                "focus": focus,
                "xp": {"Beginner": 25, "Intermediate": 30, "Advanced": 35}[level],
                "video_key": key,
                "steps": [
                    "Set up your space and equipment safely.",
                    "Start controlled so your technique stays clean.",
                    "Perform the listed repetitions with purpose.",
                    "Repeat from both sides when appropriate.",
                    "Only increase speed when control stays consistent.",
                ],
                "mistakes": "Rushing repetitions, losing balance, or taking a touch without a clear purpose.",
                "progression": "Add speed, reduce space, use your weaker foot, or add appropriate pressure.",
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
    "training_dates": [],
    "challenge_claimed": [],
    "recent_sessions": [],
    "daily_goal_date": "",
    "daily_goal_progress": 0,
    "xp_claimed": [],
    "daily_bonus_date": "",
}


def fresh_data():
    return json.loads(json.dumps(DEFAULT_DATA))


def load_data():
    if not os.path.exists(DATA_FILE):
        return fresh_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return fresh_data()
        result = fresh_data()
        result.update(raw)
        for key in ["completed", "training_dates", "challenge_claimed", "recent_sessions", "xp_claimed"]:
            if not isinstance(result.get(key), list):
                result[key] = []
        if not isinstance(result.get("completion_counts"), dict):
            result["completion_counts"] = {}
        result["completed"] = list(dict.fromkeys(x for x in result["completed"] if x in DRILL_BY_NAME))
        result["xp_claimed"] = list(dict.fromkeys(x for x in result["xp_claimed"] if x in DRILL_BY_NAME))
        return result
    except Exception:
        try:
            backup = DATA_FILE + ".broken"
            if os.path.exists(backup):
                os.remove(backup)
            os.replace(DATA_FILE, backup)
        except Exception:
            pass
        return fresh_data()


data = load_data()


def save_data():
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, DATA_FILE)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


# =========================================================
# SESSION STATE
# =========================================================

STATE_DEFAULTS = {
    "page": "Home",
    "selected_drill": None,
    "intro_seen": False,
    "drill_active": False,
    "drill_started_at": None,
    "drill_duration_seconds": 600,
    "completion_flash": None,
    "level_up_to": None,
    "session_active": False,
    "session_plan": [],
    "session_index": 0,
    "session_xp": 0,
    "session_name": "",
    "session_bonus_claimed": False,
    "coach_messages": [],
    "coach_context": {},
}

for key, value in STATE_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HELPERS
# =========================================================

def esc(value):
    return html.escape(str(value))


def render_html(body):
    if hasattr(st, "html"):
        st.html(body)
    else:
        st.markdown(body, unsafe_allow_html=True)


def go_to(page, drill_name=None):
    if drill_name:
        st.session_state.selected_drill = drill_name
    st.session_state.page = page
    st.rerun()


def get_level(xp=None):
    xp = int(data.get("xp", 0) if xp is None else xp)
    return min(MAX_LEVEL, xp // XP_PER_LEVEL + 1)


def level_progress(xp=None):
    xp = int(data.get("xp", 0) if xp is None else xp)
    level = get_level(xp)
    if level >= MAX_LEVEL:
        return 1.0
    start = (level - 1) * XP_PER_LEVEL
    return min(1.0, max(0.0, (xp - start) / XP_PER_LEVEL))


def xp_to_next_level():
    level = get_level()
    return 0 if level >= MAX_LEVEL else max(0, level * XP_PER_LEVEL - int(data.get("xp", 0)))


def today_key():
    return date.today().isoformat()


def current_week():
    return date.today().strftime("%Y-%W")


def reset_daily_goal():
    if data.get("daily_goal_date") != today_key():
        data["daily_goal_date"] = today_key()
        data["daily_goal_progress"] = 0
        save_data()


def daily_done():
    reset_daily_goal()
    return int(data.get("daily_goal_progress", 0)) >= 1


def weekly_training_days():
    week = current_week()
    return sum(
        1 for v in data.get("training_dates", [])
        if isinstance(v, str) and v[:10] and date.fromisoformat(v[:10]).strftime("%Y-%W") == week
    )


def get_streak():
    dates = {str(v)[:10] for v in data.get("training_dates", [])}
    if not dates:
        return 0
    current = date.today()
    if current.isoformat() not in dates:
        current -= timedelta(days=1)
    streak = 0
    while current.isoformat() in dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def record_training_day():
    if today_key() not in data["training_dates"]:
        data["training_dates"].append(today_key())


def add_xp(amount):
    amount = max(0, int(amount))
    if not amount:
        return False
    old_level = get_level()
    data["xp"] = int(data.get("xp", 0)) + amount
    new_level = get_level()
    if new_level > old_level:
        st.session_state.level_up_to = new_level
    save_data()
    return True


def complete_drill(drill):
    """Record every completion; permanently award each drill's XP only once."""
    reset_daily_goal()
    name = drill["name"]
    first_time = name not in data["completed"]
    if first_time:
        data["completed"].append(name)

    data["completion_counts"][name] = int(data["completion_counts"].get(name, 0)) + 1
    data["sessions"] = int(data.get("sessions", 0)) + 1
    data["daily_goal_progress"] = min(1, int(data.get("daily_goal_progress", 0)) + 1)
    record_training_day()
    data["recent_sessions"].insert(0, {
        "name": name,
        "category": drill["category"],
        "xp": drill["xp"] if name not in data["xp_claimed"] else 0,
        "date": datetime.now().strftime("%b %d, %Y"),
    })
    data["recent_sessions"] = data["recent_sessions"][:12]

    xp_new = name not in data["xp_claimed"]
    gain = drill["xp"] if xp_new else 0
    if xp_new:
        data["xp_claimed"].append(name)
    save_data()
    if gain:
        add_xp(gain)
    else:
        save_data()
    return gain, xp_new, first_time


def category_completed_count(category):
    return sum(1 for d in DRILLS if d["category"] == category and d["name"] in data["completed"])


def skill_rating(category):
    count = category_completed_count(category)
    total = sum(1 for d in DRILLS if d["category"] == category)
    return min(99, 50 + int(count / max(1, total) * 49))


def is_unlocked(drill):
    idx = [d for d in DRILLS if d["category"] == drill["category"]].index(drill)
    completed = category_completed_count(drill["category"])
    # Start with two drills available, then unlock one new drill for each completed drill.
    return idx < min(10, completed + 2)


def recommendation():
    available = [d for d in DRILLS if d["name"] not in data["completed"]]
    source = available or DRILLS
    position = data.get("favorite_position", "Winger")
    preferred = {
        "Winger": ["Dribbling", "Speed", "First Touch", "Finishing"],
        "Striker": ["Finishing", "First Touch", "Dribbling"],
        "Midfielder": ["Passing", "First Touch", "Soccer IQ"],
        "Defender": ["First Touch", "Passing", "Soccer IQ"],
        "Fullback": ["Speed", "Passing", "Dribbling"],
        "Goalkeeper": ["First Touch", "Passing", "Soccer IQ"],
    }.get(position, CATEGORIES)
    pool = [d for d in source if d["category"] in preferred] or source
    return random.Random(date.today().toordinal() * 991 + int(data.get("xp", 0))).choice(pool)


def duration_seconds(text):
    text = str(text).lower()
    nums = [int(x) for x in re.findall(r"\d+", text)]
    if "sec" in text and nums:
        if "x" in text or "×" in text:
            return max(15, nums[0] * nums[1])
        return max(15, nums[0])
    return max(60, (nums[0] if nums else 10) * 60)


def format_seconds(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def video_for(drill):
    key = drill["video_key"]
    if key in VIDEO_URLS and VIDEO_URLS[key]:
        return VIDEO_URLS[key]
    path = os.path.join(VIDEO_DIR, key + ".mp4")
    return path if os.path.exists(path) else None


def challenges():
    return [
        {"name": f"{cat} Starter", "category": cat, "drills": [d["name"] for d in DRILLS if d["category"] == cat][:3], "reward": 75}
        for cat in CATEGORIES
    ]


def challenge_complete(ch):
    return all(name in data["completed"] for name in ch["drills"])


def claim_challenge(ch):
    if ch["name"] in data["challenge_claimed"] or not challenge_complete(ch):
        return False
    data["challenge_claimed"].append(ch["name"])
    save_data()
    add_xp(ch["reward"])
    return True


def achievements():
    completed = len(data["completed"])
    categories = sum(1 for cat in CATEGORIES if category_completed_count(cat) > 0)
    return [
        ("⚡", "First Touch", "Complete your first drill.", completed >= 1),
        ("🔥", "On Fire", "Reach a 3-day streak.", get_streak() >= 3),
        ("💯", "Century", "Earn 100 XP.", data["xp"] >= 100),
        ("🧠", "All-Rounder", "Train every skill category.", categories == 6),
        ("🏆", "Skill Builder", "Complete 10 drills.", completed >= 10),
        ("⭐", "Level 5", "Reach Level 5.", get_level() >= 5),
        ("👑", "Elite", "Reach Level 10.", get_level() >= 10),
        ("🌟", "Complete Player", "Complete every drill.", completed >= len(DRILLS)),
    ]


def build_session_plan(duration, category, difficulty, style):
    target = {15: 3, 30: 5, 45: 7, 60: 9}[duration]
    pool = DRILLS[:]
    if category != "Mixed":
        pool = [d for d in pool if d["category"] == category]
    if difficulty != "Mixed":
        pool = [d for d in pool if d["level"] == difficulty]
    if style == "Technical":
        filtered = [d for d in pool if d["category"] in ["First Touch", "Passing", "Dribbling"]]
        pool = filtered or pool
    elif style == "Match-like":
        filtered = [d for d in pool if d["category"] in ["Soccer IQ", "Finishing", "Dribbling", "Speed"]]
        pool = filtered or pool
    incomplete = [d for d in pool if d["name"] not in data["completed"]]
    pool = incomplete or pool
    random.shuffle(pool)
    return pool[:min(target, len(pool))]


def _coach_normalize(text):
    """Normalize casual/typo-heavy player messages without changing meaning."""
    raw = re.sub(r"[^a-z0-9\s'?!+-]", " ", text.lower())
    raw = re.sub(r"\s+", " ", raw).strip()

    # Common soccer/chat shorthand and typo fixes.
    replacements = {
        "u": "you", "ur": "your", "r": "are", "im": "i am", "idk": "i do not know",
        "tmrw": "tomorrow", "tmr": "tomorrow", "plz": "please", "pls": "please",
        "bc": "because", "b4": "before", "w": "with", "abt": "about",
        "wrk": "work", "wrkng": "working", "dribl": "dribble", "dribblng": "dribbling",
        "passng": "passing", "finshing": "finishing", "finsh": "finish",
        "touchh": "touch", "frist": "first", "firt": "first", "thouch": "touch",
        "soccer iq": "soccer iq", "socer": "soccer", "sokcer": "soccer",
        "wng": "winger", "strikr": "striker", "mid": "midfielder", "middy": "midfielder",
        "def": "defender", "gk": "goalkeeper", "keeper": "goalkeeper",
    }
    words=[]
    for word in raw.split():
        words.append(replacements.get(word, word))
    normalized=" ".join(words)

    vocab = set(CATEGORIES + POSITIONS + [
        "drill", "training", "train", "plan", "week", "tomorrow", "today", "progress",
        "stats", "level", "xp", "tactics", "formation", "match", "game", "passing",
        "finishing", "dribbling", "speed", "touch", "first touch", "confidence", "nervous",
        "pressure", "skills", "position", "easier", "harder", "why", "recommend", "recommendation",
        "session", "time", "minutes", "beginner", "intermediate", "advanced", "winger", "striker",
    ])
    vocab.update(d['name'].lower() for d in DRILLS)

    # Word-level fuzzy repair for obvious misspellings.
    repaired=[]
    for word in normalized.split():
        if len(word) < 4:
            repaired.append(word)
            continue
        matches=difflib.get_close_matches(word, list(vocab), n=1, cutoff=0.78)
        if matches and abs(len(matches[0])-len(word)) <= 3:
            repaired.append(matches[0])
        else:
            repaired.append(word)
    return " ".join(repaired)


def _coach_extract_topic(text):
    topics = {
        "finishing": "Finishing", "shooting": "Finishing", "scoring": "Finishing",
        "dribbling": "Dribbling", "dribble": "Dribbling", "1v1": "Dribbling",
        "first touch": "First Touch", "touch": "First Touch", "control": "First Touch",
        "passing": "Passing", "pass": "Passing", "speed": "Speed", "sprint": "Speed",
        "soccer iq": "Soccer IQ", "tactics": "Soccer IQ", "decision": "Soccer IQ",
    }
    for key, category in topics.items():
        if key in text:
            return category
    return None


def _coach_find_drill(category=None, level=None, exclude_completed=True):
    pool = DRILLS[:]
    if category:
        pool = [d for d in pool if d["category"] == category]
    if level:
        pool = [d for d in pool if d["level"].lower() == level.lower()]
    if exclude_completed:
        remaining=[d for d in pool if d["name"] not in data["completed"]]
        pool = remaining or pool
    if not pool:
        return recommendation()
    return min(pool, key=lambda d: (d['name'] in data['completed'], d['level']))


def _coach_session_plan(days=3):
    pos=data.get("favorite_position", "Winger")
    weak=min(CATEGORIES, key=lambda c: skill_rating(c))
    preferred={
        "Winger":["Dribbling","First Touch","Speed","Finishing"],
        "Striker":["Finishing","First Touch","Dribbling","Speed"],
        "Midfielder":["Passing","First Touch","Soccer IQ","Dribbling"],
        "Defender":["Soccer IQ","First Touch","Passing","Speed"],
        "Fullback":["Speed","Passing","Dribbling","Soccer IQ"],
        "Goalkeeper":["First Touch","Passing","Soccer IQ"],
    }.get(pos, CATEGORIES)
    categories=[weak] + [c for c in preferred if c != weak]
    picks=[]
    for cat in categories:
        d=_coach_find_drill(cat)
        if d["name"] not in [x["name"] for x in picks]:
            picks.append(d)
        if len(picks)>=days:
            break
    while len(picks)<days:
        picks.append(recommendation())
    return picks[:days]


def offline_coach_response(prompt):
    """Context-aware local coach with fuzzy typo handling and follow-up memory."""
    raw=prompt.strip()
    text=_coach_normalize(raw)
    pos=data.get("favorite_position", "Winger")
    completed=len(data.get("completed", []))
    streak=get_streak()
    level=get_level()
    xp=int(data.get("xp",0))
    ratings={c:skill_rating(c) for c in CATEGORIES}
    strongest=max(ratings, key=ratings.get)
    weakest=min(ratings, key=ratings.get)

    # Carry lightweight conversational context across turns.
    prior=st.session_state.get("coach_context", {})
    topic=_coach_extract_topic(text) or prior.get("topic")
    if topic:
        st.session_state.coach_context={"topic":topic}

    # Safety boundary around injury/medical questions.
    if any(word in text for word in ["injury","injured","hurt","pain","knee","ankle","concussion","dizzy","fainted","swollen"]):
        return (
            "I can help with soccer training, but I can't diagnose an injury. 🛑 "
            "For pain or an injury, tell a parent/guardian and follow advice from a qualified healthcare professional. "
            "When you're cleared to train, I can adapt a FUT TUT plan around that guidance."
        )

    # Conversational acknowledgements / greetings.
    if re.search(r"\b(hello|hi|hey|yo|sup|good morning|good afternoon|good evening)\b", text):
        return (
            f"Yo {player} 👋⚽ I'm locked in. You're Level {level}, {xp} XP, {completed} drills, "
            f"and a {streak}-day streak. Tell me what you're trying to improve and I'll build from your actual FUT TUT progress."
        )

    if re.search(r"\b(thanks|thank you|thx|ty)\b", text):
        return "Anytime 😎⚽ Keep it simple, keep the reps clean, and we'll build from there."

    # Follow-up modifiers that work even when the player only says "make it easier".
    if "easier" in text or "simpler" in text or "beginner" in text:
        d=_coach_find_drill(topic or weakest, "Beginner")
        return f"Yep — let's dial it back. **{d['name']}** is the easiest fit: {d['description']} Focus on {d['focus'].lower()} and keep the pace controlled. 🎯"

    if "harder" in text or "more difficult" in text or "advanced" in text:
        d=_coach_find_drill(topic or strongest, "Advanced")
        return f"Let's level it up. 🔥 Try **{d['name']}**: {d['description']} The challenge is {d['focus'].lower()}. Only add speed when your control stays solid."

    if "why" in text and topic:
        d=_coach_find_drill(topic)
        return f"Because **{d['name']}** attacks the exact area you mentioned: **{d['focus'].lower()}**. It also fits your current FUT TUT progression, so you're not jumping randomly between skills."

    # Explicit drill requests, including misspelled categories.
    if any(k in text for k in ["drill", "practice", "train", "work on", "what should"]):
        category=topic
        chosen=_coach_find_drill(category)
        st.session_state.coach_context={"topic": chosen["category"], "drill": chosen["name"]}
        return (
            f"I'd use **{chosen['name']}**. 🎯\n\n"
            f"**Why:** {chosen['description']}\n\n"
            f"**Focus:** {chosen['focus']}\n"
            f"**Dose:** {chosen['time']} · {chosen['reps']} · +{chosen['xp']} XP\n\n"
            f"That's a {chosen['level'].lower()} {chosen['category'].lower()} option."
        )

    # Time-aware requests.
    minute_match=re.search(r"\b(\d{1,3})\s*(?:min|mins|minute|minutes)\b", text)
    if minute_match:
        minutes=int(minute_match.group(1))
        if minutes <= 15:
            plan=[_coach_find_drill(topic or weakest)]
        elif minutes <= 30:
            plan=_coach_session_plan(2)
        else:
            plan=_coach_session_plan(3)
        lines="\n".join(f"**{i+1}. {d['name']}** — {d['time']}" for i,d in enumerate(plan))
        return f"You've got **{minutes} minutes**, so here's a realistic FUT TUT plan for a {pos.lower()}:\n\n{lines}\n\nKeep the quality high rather than trying to cram in everything. ⚽"

    # Plan / schedule requests.
    if any(k in text for k in ["plan", "program", "schedule", "week", "tomorrow", "next few days"]):
        days=3 if "3" in text else 5 if "5" in text else 3
        picks=_coach_session_plan(days)
        lines=[]
        for i,d in enumerate(picks,1):
            reason="weak-area work" if d["category"]==weakest else "position fit"
            lines.append(f"**Day {i}: {d['name']}** — {d['category']} · {d['time']} · {reason}")
        return f"Here's a **{days}-day {pos.lower()} plan** built from your actual FUT TUT profile:\n\n" + "\n".join(lines) + "\n\nThe idea is simple: build your weakest area without ignoring the skills your position needs most. 🔥"

    # Progress / stats.
    if any(k in text for k in ["progress", "stats", "level", "how am i doing", "how i am doing", "good am i"]):
        return (
            f"**Your FUT TUT check-in:** Level **{level}**, **{xp} XP**, **{completed}/60 drills**, and a **{streak}-day streak**. 🔥\n\n"
            f"Strongest: **{strongest} ({ratings[strongest]}/99)**\n"
            f"Biggest opportunity: **{weakest} ({ratings[weakest]}/99)**\n\n"
            f"For a {pos.lower()}, I'd put your next training emphasis on **{weakest}** while keeping {strongest.lower()} as a strength."
        )

    # Position-specific advice.
    if any(k in text for k in ["position", "winger", "striker", "midfielder", "defender", "fullback", "goalkeeper"]):
        focus={
            "Winger":"1v1 attack, first touch, acceleration, and final-third decisions",
            "Striker":"finishing, movement, first touch, and fast decisions around the box",
            "Midfielder":"scanning, receiving on the back foot, passing, and managing space",
            "Defender":"scanning, first touch, passing, positioning, and timing",
            "Fullback":"speed, passing, 1v1 play, and timing attacking runs",
            "Goalkeeper":"distribution, first touch, scanning, and decision-making",
        }.get(pos,"first touch, passing, and decision-making")
        return f"As a **{pos}**, I'd build around **{focus}**. ⚽ Your current weakest FUT TUT area is **{weakest} ({ratings[weakest]}/99)**, so that's the first place I'd attack."

    # Tactics / match play.
    if any(k in text for k in ["tactic", "formation", "match", "game", "play better", "decision", "space"]):
        return (
            "Use this simple decision ladder: **scan → identify space → choose the safest useful action → execute**. 👀⚽\n\n"
            "If the defender gives you space, carry. If a teammate has the better angle, pass. If you're isolated with a defender and have support behind you, attack the 1v1 with a clear move."
        )

    # Confidence / pressure.
    if any(k in text for k in ["confidence", "nervous", "pressure", "afraid", "scared", "overthink"]):
        return (
            "When pressure hits, shrink the task. 🧠⚽ Don't try to prove everything on one touch. Use one cue: **scan → decide → play**. "
            "After the action, reset instead of replaying it in your head. Your next decision is the only one you need to solve."
        )

    # XP / rewards.
    if any(k in text for k in ["xp", "reward", "points", "claim"]):
        claimed=len(data.get("xp_claimed", []))
        return f"You've earned **{xp} XP** and claimed XP on **{claimed} drills**. ✅ Each drill's XP reward is protected so repeating a drill can't farm infinite points."

    # "What can you do?" / capability prompt.
    if any(k in text for k in ["what can you", "help me", "can you", "options"]):
        return (
            "A lot 😎 I can pick drills, build short or multi-day plans, explain why a drill fits, compare skills, "
            "help with position-specific play, talk tactics, check your FUT TUT progress, and adjust a plan when you say things like **make it easier**, **harder**, or **I only have 20 minutes**."
        )

    # Graceful final response that still uses profile data.
    rec=_coach_find_drill(topic)
    st.session_state.coach_context={"topic": rec["category"], "drill": rec["name"]}
    return (
        f"I get what you're asking — and you don't have to type perfectly. 😎⚽ "
        f"Based on your **{pos.lower()}** profile and your current progress, I'd start with **{rec['name']}**. "
        f"Your biggest development opportunity right now is **{weakest}**, so that's what I'd prioritize. "
        f"You can also tell me a time limit, like **20 minutes**, or say **make it easier** and I'll adapt the plan."
    )

def primary_button(label, key, disabled=False):
    return st.button(label, key=key, use_container_width=True, type="primary", disabled=disabled)


# =========================================================
# GLOBAL UI
# =========================================================

st.markdown("""
<style>
:root{--green:#58cc02;--green-dark:#46a900;--blue:#1cb0f6;--blue-dark:#1595cf;--yellow:#ffc800;--purple:#9b5cff;--bg:#f6f7f8;--line:#e4e7eb;--text:#202124;--muted:#70757a;--shadow:0 5px 0 rgba(0,0,0,.055)}
.stApp{background:radial-gradient(circle at 10% 0%,rgba(88,204,2,.10),transparent 30%),radial-gradient(circle at 100% 10%,rgba(28,176,246,.08),transparent 28%),var(--bg)}
.block-container{max-width:760px;padding:1rem 1rem 7rem}
header{background:transparent!important}#MainMenu,footer{visibility:hidden}
h1,h2,h3,p,div,span,label,button,input,textarea{font-family:Arial,Helvetica,sans-serif}
h1{font-weight:950!important;letter-spacing:-2px;color:var(--text)!important}
h2,h3{color:var(--text)!important;font-weight:900!important}
p{color:#5f6368!important}
/* Force predictable text colors on mobile/dark-mode browsers */
.intro-wrap,.intro-wrap *{color:#202124!important}.page-title,.page-title *,.section-heading,.section-heading *{color:#202124!important}
.intro-wordmark{color:#202124!important;text-shadow:none!important}.intro-wordmark span{color:#58cc02!important}
.intro-wordmark span{color:#58cc02!important}
.section-heading,.section-heading *{color:#202124!important}
.custom-dark-card,.custom-dark-card *{color:#fff!important}

.stButton>button{min-height:52px;border-radius:16px!important;font-weight:900!important;border:2px solid #dedfe1!important;box-shadow:var(--shadow)!important;transition:transform .12s ease,box-shadow .12s ease!important}
.stButton>button:hover{transform:translateY(-1px)}.stButton>button:active{transform:translateY(2px);box-shadow:0 2px 0 rgba(0,0,0,.05)!important}
.stButton>button[kind="primary"]{background:var(--green)!important;color:white!important;border-color:var(--green-dark)!important;box-shadow:0 4px 0 var(--green-dark)!important}
div[data-baseweb="select"]>div,input,textarea{border-radius:14px!important}.stProgress>div>div>div>div,.stProgress>div>div{border-radius:999px!important}
[data-testid="stChatMessage"]{border-radius:18px;margin-bottom:9px}
@media(max-width:700px){.block-container{padding-left:12px;padding-right:12px;padding-top:.55rem}.stButton>button{min-height:56px;font-size:1rem!important}h1{font-size:2.2rem!important}}
.card{background:#fff;border:2px solid var(--line);border-radius:22px;box-shadow:var(--shadow);padding:18px;margin:12px 0}
.eyebrow{font-size:.68rem;font-weight:950;letter-spacing:.13em;color:#888}.inverse{color:rgba(255,255,255,.83)!important}.row{display:flex;justify-content:space-between;align-items:center;gap:10px}
.hero{background:linear-gradient(135deg,#58cc02,#7be121);color:#fff;border-radius:28px;padding:26px 23px;box-shadow:0 7px 0 #46a900;margin:10px 0 18px}.hero-title{font-size:clamp(2.5rem,10vw,4rem);font-weight:950;letter-spacing:-3px;line-height:.97;margin-top:7px}.hero-sub{font-weight:750;color:rgba(255,255,255,.92);margin-top:7px}.hero-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:20px}.hero-stats div{background:rgba(255,255,255,.16);padding:11px 8px;border-radius:15px;text-align:center}.hero-stats strong,.hero-stats span{display:block}.hero-stats strong{font-size:1.18rem}.hero-stats span{font-size:.62rem;font-weight:900;letter-spacing:.08em;opacity:.8}
.pill{background:#eef9e8;color:#46a900;border-radius:999px;padding:6px 10px;font-size:.72rem;font-weight:950}.mission{display:flex;justify-content:space-between;gap:14px;align-items:center;background:#fff8df;border:2px solid #f1dd8a;border-radius:22px;padding:18px;margin:12px 0}.mission.done{background:#effbe9;border-color:#bfeaa8}.mission-title{font-size:1.3rem;font-weight:950;margin-top:3px}.mission-sub{color:#777;font-weight:650}.check{width:42px;height:42px;border-radius:50%;background:#ffc800;display:grid;place-items:center;font-weight:950;flex:0 0 auto}
.drill-card{background:#fff;border:2px solid var(--line);border-radius:22px;box-shadow:var(--shadow);padding:20px;margin:12px 0}.drill-name{font-size:1.7rem;font-weight:950;letter-spacing:-.7px;margin:7px 0}.desc{color:#5f6368;line-height:1.45}.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}.meta span{background:#f4f6f7;color:#73787d;border-radius:999px;padding:7px 10px;font-size:.75rem;font-weight:850}
.drill-hero{background:linear-gradient(135deg,#1f2124,#343940);color:#fff;border-radius:27px;padding:25px;box-shadow:0 7px 0 #151719;margin:10px 0 18px}.drill-hero .eyebrow{color:#b2b7bb}.drill-title{font-size:clamp(2.1rem,8vw,3.6rem);font-weight:950;letter-spacing:-2px;line-height:1;margin-top:8px}.drill-sub{color:#d9dde1;line-height:1.45;margin-top:10px}.drill-hero .meta span{background:rgba(255,255,255,.10);color:#fff}
.step{display:flex;gap:13px;align-items:center;background:#fff;border:2px solid var(--line);border-radius:20px;box-shadow:var(--shadow);padding:14px;margin:10px 0}.num{width:39px;height:39px;border-radius:50%;background:#58cc02;color:#fff;display:grid;place-items:center;font-weight:950;flex:0 0 auto}.step-text{font-weight:750;color:#34383c}.focus{background:#eef8ff;border:2px solid #ccecff;border-radius:22px;padding:18px;margin:12px 0}.focus-title{font-size:1.2rem;font-weight:950;margin-top:4px}.tip{color:#5d6870;margin-top:7px}
.video-box{border-radius:22px;background:#17191c;color:#fff;padding:34px 20px;text-align:center;margin:12px 0}.play{width:64px;height:64px;border-radius:50%;background:#58cc02;color:#fff;display:grid;place-items:center;margin:0 auto 12px;font-size:1.4rem}.video-title{font-size:1.2rem;font-weight:950}.video-sub{color:#b8bec4;max-width:500px;margin:5px auto 0;line-height:1.4}
.coach-note{background:#eef9e8;border:2px solid #ccefb9;border-radius:22px;padding:16px 18px;margin:12px 0;color:#263223}.coach-note strong{color:#2f7608}.coach-actions{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.coach-actions div{background:#fff;border:2px solid var(--line);border-radius:16px;padding:10px;text-align:center;font-size:.76rem;font-weight:900;color:#555}@media(max-width:700px){.coach-actions{grid-template-columns:1fr 1fr}.coach-actions div:last-child{grid-column:1/-1}}
.timer{background:linear-gradient(135deg,#58cc02,#78df20);color:#fff;border-radius:27px;padding:24px;text-align:center;box-shadow:0 7px 0 #46a900;margin:16px 0}.timer-label{font-size:.68rem;font-weight:950;letter-spacing:.15em;color:rgba(255,255,255,.82)}.timer-number{font-size:clamp(3.6rem,17vw,6rem);font-weight:950;letter-spacing:-4px;line-height:1;margin:6px 0}.timer-note{font-weight:750;color:rgba(255,255,255,.92)}
.success{background:#effbe9;border:2px solid #bfeaa8;border-radius:24px;padding:24px;text-align:center;margin:15px 0}.success-icon{font-size:3rem}.success-title{font-size:1.7rem;font-weight:950}.success-xp{font-size:2rem;font-weight:950;color:#46a900}.success-sub{color:#6f777d;margin-top:5px}.info{background:#eef7ff;border:2px solid #c9e9ff;border-radius:24px;padding:22px;text-align:center;margin:15px 0}
.path-head,.path,.skill,.achievement,.history,.challenge,.mini{background:#fff;border:2px solid var(--line);border-radius:21px;box-shadow:var(--shadow);margin:10px 0}.path-head{padding:18px;display:flex;justify-content:space-between;align-items:center}.path-title{font-size:1.5rem;font-weight:950}.orb{width:50px;height:50px;border-radius:50%;display:grid;place-items:center;background:#eef9e8}.path{display:flex;gap:13px;align-items:center;padding:14px}.path.locked{opacity:.52}.path.done{background:#f7fff2;border-color:#bfeaa8}.path-icon{font-size:1.5rem;min-width:36px;text-align:center}.path-name{font-weight:950;font-size:1.08rem;margin:4px 0}.path-meta{font-size:.76rem;color:#777;font-weight:800}
.session,.current,.finish{border-radius:27px;padding:24px;box-shadow:0 7px 0 #1595cf;margin:14px 0;color:#fff;background:linear-gradient(135deg,#1cb0f6,#43c4ff)}.session-big{font-size:2.5rem;font-weight:950}.session-sub{font-weight:750;color:rgba(255,255,255,.9)}.session-list{display:grid;gap:7px;margin-top:15px}.session-list span{background:rgba(255,255,255,.13);border-radius:12px;padding:8px 10px;font-weight:750}.current{padding:25px;background:linear-gradient(135deg,#58cc02,#78df20);box-shadow:0 7px 0 #46a900}.current-title{font-size:2.2rem;font-weight:950;line-height:1;margin-top:7px;letter-spacing:-1px}.current-meta{margin-top:9px;font-weight:800}.finish{background:linear-gradient(135deg,#ffc800,#ffd83f);box-shadow:0 7px 0 #d9aa00;text-align:center;color:#252525}.finish .trophy{font-size:4rem}.finish-title{font-size:2.3rem;font-weight:950}.finish-xp{font-size:2rem;font-weight:950}.finish-sub{font-weight:700;color:#5b5b5b}
.progress-hero,.player{background:linear-gradient(135deg,#58cc02,#78df20);color:#fff;border-radius:27px;padding:25px;box-shadow:0 7px 0 #46a900;margin:12px 0 18px}.progress-level{font-size:3rem;font-weight:950;letter-spacing:-2px}.skill{padding:16px}.skill-top{display:flex;justify-content:space-between}.skill-num{font-size:2rem;font-weight:950}.skill-icon{font-size:2rem}.achievement{display:flex;gap:14px;align-items:center;padding:15px 17px}.achievement.locked{opacity:.5}.achievement-icon{font-size:1.8rem;width:38px}.achievement-name{font-size:1.02rem;font-weight:950}.achievement-desc{color:#777}.history{display:flex;justify-content:space-between;gap:12px;padding:15px 17px}.history-date{color:#888;font-size:.76rem;margin-top:4px}.history-xp{font-weight:950;color:#46a900}.challenge{padding:18px}.challenge-title{font-size:1.4rem;font-weight:950;margin:4px 0}.challenge-meta{color:#777;font-weight:800}.mini{text-align:center;padding:14px}.mini strong{font-size:1.55rem;font-weight:950;display:block}.mini span{font-size:.67rem;font-weight:900;letter-spacing:.08em;color:#888}.player{background:linear-gradient(135deg,#1cb0f6,#43c4ff);box-shadow:0 7px 0 #1595cf}.player-ball{font-size:3rem}.player-name{font-size:2rem;font-weight:950}.player-sub{font-weight:800;color:rgba(255,255,255,.9)}
.levelup{background:linear-gradient(135deg,#9b5cff,#c084ff);color:#fff;border-radius:29px;padding:30px;text-align:center;box-shadow:0 8px 0 #7e44cb;margin:10px 0 18px}.levelup-orb{font-size:4rem}.levelup-title{font-size:3rem;font-weight:950}.levelup-sub{font-weight:750;color:rgba(255,255,255,.92)}
</style>
""", unsafe_allow_html=True)


# =========================================================
# INTRO SPLASH — no button
# =========================================================

if not st.session_state.intro_seen:
    render_html("""
    <div class="intro-wrap">
      <div class="intro-ball">⚽</div>
      <div class="intro-logo">FUT <span>TUT</span></div>
      <div class="intro-tag">TRAIN • PLAY • IMPROVE</div>
      <div class="intro-loader"><i></i><i></i><i></i></div>
    </div>
    <style>
      .intro-wrap{min-height:80vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
      .intro-ball{font-size:5.2rem;animation:ball .95s cubic-bezier(.2,.9,.2,1) both, float 1.6s 1s ease-in-out infinite alternate;filter:drop-shadow(0 12px 15px rgba(0,0,0,.12))}
      .intro-logo{font-size:clamp(3rem,12vw,5.7rem);font-weight:950;letter-spacing:-5px;line-height:.9;margin-top:17px;animation:up .7s .2s ease-out both}
      .intro-logo span{color:#58cc02}.intro-tag{margin-top:17px;font-size:.78rem;letter-spacing:.2em;font-weight:950;color:#777;animation:fade .7s .55s ease both}
      .intro-loader{display:flex;gap:6px;margin-top:23px}.intro-loader i{display:block;width:7px;height:7px;border-radius:50%;background:#58cc02;animation:dot .9s infinite ease-in-out}.intro-loader i:nth-child(2){animation-delay:.12s}.intro-loader i:nth-child(3){animation-delay:.24s}
      @keyframes ball{from{opacity:0;transform:translateY(80px) scale(.4) rotate(-180deg)}to{opacity:1;transform:translateY(0) scale(1) rotate(0)}}
      @keyframes float{from{transform:translateY(0)}to{transform:translateY(-10px)}}@keyframes up{from{opacity:0;transform:translateY(16px) scale(.96)}to{opacity:1;transform:none}}@keyframes fade{from{opacity:0}to{opacity:1}}@keyframes dot{0%,100%{transform:scale(.7);opacity:.45}50%{transform:scale(1.1);opacity:1}}
    </style>
    """)
    time.sleep(1.8)
    st.session_state.intro_seen = True
    st.rerun()


# Daily rollover before page rendering.
reset_daily_goal()

# Level-up overlay has priority after an XP event.
if st.session_state.level_up_to:
    render_html(f"""
    <div class="levelup">
      <div class="levelup-orb">⬆️</div>
      <div class="eyebrow inverse">LEVEL UP</div>
      <div class="levelup-title">Level {int(st.session_state.level_up_to)}</div>
      <div class="levelup-sub">Your training is paying off. Keep building. ⚡</div>
    </div>
    """)
    if primary_button("CONTINUE →", "dismiss_level"):
        st.session_state.level_up_to = None
        st.rerun()
    st.stop()

level = get_level()
player = str(data.get("player_name", "Player")).strip() or "Player"


# =========================================================
# TOP BAR
# =========================================================

l, m, r = st.columns([1.15, 1.7, 1.15])
with l:
    if st.button("⚽ FUT TUT", key="top_home", use_container_width=True):
        go_to("Home")
with m:
    st.markdown(f"<div style='text-align:center;padding-top:10px;font-weight:950;color:#777;font-size:.74rem;letter-spacing:.07em'>LEVEL {level}</div>", unsafe_allow_html=True)
with r:
    st.markdown(f"<div style='text-align:right;padding-top:8px;font-weight:950'>🔥 {get_streak()}</div>", unsafe_allow_html=True)


def bottom_nav(active):
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    items = [("🏠", "Home"), ("🗺️", "Training"), ("⚡", "Start Session"), ("🤖", "AI Coach"), ("📈", "Progress")]
    cols = st.columns(5)
    for col, (icon, target) in zip(cols, items):
        with col:
            if st.button(icon, key=f"nav_{target}", use_container_width=True, type="primary" if active == target else "secondary"):
                go_to(target)
    st.markdown(f"<div style='text-align:center;color:#999;font-size:.64rem;font-weight:900;letter-spacing:.08em;margin-top:4px'>{esc(active.upper())}</div>", unsafe_allow_html=True)


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "Home":
    rec = recommendation()
    done = daily_done()

    render_html(f"""
    <div class="hero">
      <div class="eyebrow inverse">WELCOME BACK</div>
      <div class="hero-title">Hey, {esc(player)} 👋</div>
      <div class="hero-sub">Build your game one focused session at a time.</div>
      <div class="hero-stats">
        <div><strong>{data['xp']}</strong><span>XP</span></div>
        <div><strong>Lv {level}</strong><span>LEVEL</span></div>
        <div><strong>{get_streak()}🔥</strong><span>STREAK</span></div>
      </div>
    </div>
    """)

    render_html(f"""
    <div class="card"><div class="row"><div class="eyebrow">LEVEL PROGRESS</div><div class="pill">⚡ {data['xp']} XP</div></div>
      <div style="display:flex;align-items:center;gap:12px;margin-top:8px"><strong style="font-size:2rem">{level}</strong><div><strong>{xp_to_next_level() if level < MAX_LEVEL else 0} XP</strong><div style="color:#888;font-size:.78rem;font-weight:800">{'until Level '+str(level+1) if level < MAX_LEVEL else 'MAX LEVEL'}</div></div></div>
    </div>
    """)
    st.progress(level_progress(), text=(f"{xp_to_next_level()} XP until Level {level+1}" if level < MAX_LEVEL else "MAX LEVEL"))

    render_html(f"""
    <div class="mission {'done' if done else ''}">
      <div><div class="eyebrow">TODAY'S MISSION</div><div class="mission-title">Complete 1 drill {'✅' if done else '🎯'}</div><div class="mission-sub">{'Daily goal complete. Nice work.' if done else 'One focused session keeps the streak moving.'}</div></div>
      <div class="check">{'✓' if done else '1'}</div>
    </div>
    """)
    st.progress(1 if done else 0, text="Daily goal complete 🔥" if done else "0 / 1 drills")
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>⭐ Recommended for you</div>")
    render_html(f"""
    <div class="drill-card"><div class="row"><div class="eyebrow">{esc(rec['category'])} · {esc(rec['level'])}</div><div class="pill">+{rec['xp']} XP</div></div>
      <div class="drill-name">{esc(rec['name'])}</div><div class="desc">{esc(rec['description'])}</div>
      <div class="meta"><span>⏱ {esc(rec['time'])}</span><span>🔁 {esc(rec['reps'])}</span><span>🎯 {esc(rec['focus'])}</span></div>
    </div>
    """)
    if primary_button("START TODAY'S DRILL →", "home_start"):
        go_to("Drill", rec["name"])

    a,b = st.columns(2)
    with a:
        if st.button("🗺️ TRAINING PATH", key="home_training", use_container_width=True):
            go_to("Training")
    with b:
        if st.button("⚡ BUILD SESSION", key="home_session", use_container_width=True):
            go_to("Start Session")
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>Your numbers</div>")
    a,b,c = st.columns(3)
    for col, value, label in [(a, len(data['completed']), 'DRILLS'), (b, data['sessions'], 'TRAINING'), (c, weekly_training_days(), 'THIS WEEK')]:
        with col:
            render_html(f"<div class='mini'><strong>{value}</strong><span>{label}</span></div>")

    bottom_nav("Home")


# =========================================================
# DRILL
# =========================================================

elif st.session_state.page == "Drill":
    drill = DRILL_BY_NAME.get(st.session_state.selected_drill) or recommendation()
    st.session_state.selected_drill = drill["name"]

    if st.button("← BACK", key="drill_back"):
        st.session_state.drill_active = False
        go_to("Home")

    render_html(f"""
    <div class="drill-hero"><div class="eyebrow">{esc(drill['category'])} · {esc(drill['level'])}</div>
      <div class="drill-title">{esc(drill['name'])}</div><div class="drill-sub">{esc(drill['description'])}</div>
      <div class="meta"><span>⏱ {esc(drill['time'])}</span><span>🔁 {esc(drill['reps'])}</span><span>⚡ +{drill['xp']} XP</span></div>
    </div>
    """)
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>🎥 Watch & learn</div>")
    local_or_hosted = video_for(drill)
    uploaded = st.session_state.get("uploaded_video") if st.session_state.get("uploaded_video_key") == drill["video_key"] else None
    video_source = uploaded or local_or_hosted
    if video_source:
        try:
            st.video(video_source)
        except Exception:
            st.warning("That video could not be played. You can still complete the drill.")
    else:
        render_html("<div class='video-box'><div class='play'>▶</div><div class='video-title'>Demo video slot ready</div><div class='video-sub'>Add videos/<i>video-key</i>.mp4 or a hosted MP4 URL in VIDEO_URLS. You can also upload one below for this session.</div></div>")

    uploaded_file = st.file_uploader("Optional demo video", type=["mp4", "mov", "webm"], key=f"video_upload_{drill['id']}")
    if uploaded_file is not None:
        st.session_state.uploaded_video = uploaded_file
        st.session_state.uploaded_video_key = drill["video_key"]
        st.video(uploaded_file)
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>📚 How to do it</div>")
    for i, step in enumerate(drill["steps"], 1):
        render_html(f"<div class='step'><div class='num'>{i}</div><div class='step-text'>{esc(step)}</div></div>")

    render_html(f"<div class='focus'><div class='eyebrow'>COACH FOCUS</div><div class='focus-title'>{esc(drill['focus'])}</div><div class='tip'>💡 {esc(drill['tip'])}</div></div>")

    duration = duration_seconds(drill["time"])
    if not st.session_state.drill_active:
        if primary_button("▶ START DRILL", "drill_start"):
            st.session_state.drill_active = True
            st.session_state.drill_started_at = time.time()
            st.session_state.drill_duration_seconds = duration
            st.session_state.completion_flash = None
            st.rerun()
    else:
        started = float(st.session_state.drill_started_at or time.time())
        elapsed = max(0, int(time.time() - started))
        remaining = max(0, duration - elapsed)

        # Live countdown is client-side so the numbers actually move without Streamlit reruns.
        timer_html = f"""
        <div class='timer'><div class='timer-label'>DRILL IN PROGRESS</div><div id='futtut-live-timer' class='timer-number'>{format_seconds(remaining)}</div><div class='timer-note'>Stay controlled. Quality first.</div></div>
        <script>
        const started={started}; const duration={duration}; const el=document.getElementById('futtut-live-timer');
        function tick(){{const left=Math.max(0,duration-Math.floor(Date.now()/1000-started)); const m=String(Math.floor(left/60)).padStart(2,'0'); const s=String(left%60).padStart(2,'0'); if(el) el.textContent=m+':'+s;}}
        tick(); setInterval(tick,250);
        </script>
        """
        components.html(timer_html, height=170, scrolling=False)
        st.progress(min(1, elapsed / max(1, duration)), text=f"{format_seconds(elapsed)} elapsed · {format_seconds(remaining)} left")

        if primary_button("✅ COMPLETE DRILL", "complete_active"):
            gain, xp_new, first_time = complete_drill(drill)
            st.session_state.drill_active = False
            st.session_state.drill_started_at = None
            st.session_state.completion_flash = {"gain": gain, "xp_new": xp_new, "first_time": first_time, "name": drill["name"]}
            st.rerun()
        if st.button("⏸ PAUSE / EXIT", key="pause_drill", use_container_width=True):
            st.session_state.drill_active = False
            st.session_state.drill_started_at = None
            st.rerun()

    if st.session_state.completion_flash:
        flash = st.session_state.completion_flash
        if flash["gain"]:
            render_html(f"<div class='success'><div class='success-icon'>🎉</div><div class='success-title'>DRILL COMPLETE</div><div class='success-xp'>+{flash['gain']} XP</div><div class='success-sub'>XP claimed once and safely locked against duplicates.</div></div>")
            try: st.balloons()
            except Exception: pass
        else:
            render_html("<div class='info'><div class='success-icon'>✅</div><div class='success-title'>TRAINING RECORDED</div><div class='success-sub'>You've already claimed this drill's XP, so repeating it records training without creating duplicate XP.</div></div>")

        same = [d for d in DRILLS if d["category"] == drill["category"]]
        idx = same.index(drill)
        next_drill = same[idx + 1] if idx + 1 < len(same) and is_unlocked(same[idx + 1]) else None
        c1,c2 = st.columns(2)
        with c1:
            if next_drill and st.button("NEXT DRILL →", key="next_drill", use_container_width=True):
                st.session_state.completion_flash = None
                go_to("Drill", next_drill["name"])
        with c2:
            if st.button("DONE", key="drill_done", use_container_width=True):
                st.session_state.completion_flash = None
                go_to("Home")

    with st.expander("🧠 Coach notes"):
        st.write(f"**Common mistake:** {drill['mistakes']}")
        st.write(f"**Progression:** {drill['progression']}")

    bottom_nav("Training")


# =========================================================
# TRAINING PATH
# =========================================================

elif st.session_state.page == "Training":
    render_html("<div class='page-title' style='font-size:2.2rem;font-weight:950;color:#202124!important;letter-spacing:-1.5px;margin:8px 0 4px;'>🗺️ Training Path</div>")
    st.caption("A clear skill tree: learn, complete, unlock, repeat.")
    category = st.selectbox("Skill", CATEGORIES, key="training_skill")
    drills = [d for d in DRILLS if d["category"] == category]
    complete_count = category_completed_count(category)

    render_html(f"<div class='path-head'><div><div class='eyebrow'>{esc(category.upper())}</div><div class='path-title'>{complete_count}/{len(drills)} completed</div></div><div class='orb'>⚡</div></div>")
    st.progress(complete_count / max(1,len(drills)), text=f"{complete_count}/{len(drills)} completed")

    for i, drill in enumerate(drills,1):
        unlocked = is_unlocked(drill)
        complete = drill["name"] in data["completed"]
        icon = "✅" if complete else ("▶" if unlocked else "🔒")
        render_html(f"<div class='path {'done' if complete else 'locked' if not unlocked else ''}'><div class='path-icon'>{icon}</div><div><div class='eyebrow'>DRILL {i} · {esc(drill['level'])}</div><div class='path-name'>{esc(drill['name'])}</div><div class='path-meta'>{esc(drill['time'])} · +{drill['xp']} XP</div></div></div>")
        if unlocked:
            if st.button("VIEW DRILL →", key=f"view_{drill['id']}", use_container_width=True):
                go_to("Drill", drill["name"])
        else:
            st.caption("🔒 Complete an earlier drill in this skill to unlock it.")

    c1,c2 = st.columns(2)
    with c1:
        if st.button("🏆 CHALLENGES", key="training_challenges", use_container_width=True): go_to("Challenges")
    with c2:
        if st.button("👤 PROFILE", key="training_profile", use_container_width=True): go_to("Profile")
    bottom_nav("Training")


# =========================================================
# SESSION BUILDER
# =========================================================

elif st.session_state.page == "Start Session":
    render_html("<div class='page-title' style='font-size:2.2rem;font-weight:950;color:#202124!important;letter-spacing:-1.5px;margin:8px 0 4px;'>⚡ Training Session</div>")
    st.caption("Build a focused session, lock the plan, and finish it cleanly.")

    if not st.session_state.session_active:
        duration = st.select_slider("Session length", [15,30,45,60], value=30, format_func=lambda x:f"{x} min")
        category = st.selectbox("Main skill", ["Mixed"] + CATEGORIES, key="session_category")
        difficulty = st.selectbox("Difficulty", ["Mixed"] + LEVELS, key="session_difficulty")
        style = st.selectbox("Training style", STYLES, key="session_style")

        with st.spinner("Building your session…"):
            preview = build_session_plan(duration, category, difficulty, style)

        render_html(f"<div class='session'><div class='eyebrow inverse'>SESSION PREVIEW</div><div class='session-big'>{len(preview)} drills</div><div class='session-sub'>{duration} min · {esc(style)} · {esc(category)}</div><div class='session-list'>{''.join(f'<span>✓ {esc(d["name"])}</span>' for d in preview)}</div></div>")

        if primary_button("🚀 START SESSION", "start_session"):
            st.session_state.session_plan = build_session_plan(duration, category, difficulty, style)
            st.session_state.session_index = 0
            st.session_state.session_xp = 0
            st.session_state.session_bonus_claimed = False
            st.session_state.session_name = f"{style} Session"
            st.session_state.session_active = True
            st.rerun()
    else:
        plan = st.session_state.session_plan
        i = int(st.session_state.session_index)
        if i < len(plan):
            current = plan[i]
            st.progress(i / max(1,len(plan)), text=f"Drill {i+1} of {len(plan)}")
            render_html(f"<div class='current'><div class='eyebrow inverse'>{esc(st.session_state.session_name)}</div><div class='current-title'>{esc(current['name'])}</div><div class='current-meta'>⚡ +{current['xp']} XP · {esc(current['time'])} · {esc(current['reps'])}</div></div>")
            st.write(current["description"])
            render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>📚 How to do it</div>")
            for step in current["steps"]:
                st.write("• " + step)
            if st.button("✅ COMPLETE & NEXT", key=f"session_next_{i}", use_container_width=True, type="primary"):
                gain, xp_new, _ = complete_drill(current)
                if xp_new:
                    st.session_state.session_xp += gain
                st.session_state.session_index += 1
                st.rerun()
            if st.button("❌ END SESSION", key="end_session", use_container_width=True):
                st.session_state.session_active = False
                st.session_state.session_plan = []
                st.session_state.session_index = 0
                st.rerun()
        else:
            if not st.session_state.session_bonus_claimed:
                add_xp(50)
                st.session_state.session_xp += 50
                st.session_state.session_bonus_claimed = True
            render_html(f"<div class='finish'><div class='trophy'>🏆</div><div class='finish-title'>SESSION COMPLETE</div><div class='finish-xp'>+{st.session_state.session_xp} XP</div><div class='finish-sub'>Your session bonus was added exactly once. The plan is now complete.</div></div>")
            if primary_button("🔥 BUILD ANOTHER SESSION", "another_session"):
                st.session_state.session_active = False
                st.session_state.session_plan = []
                st.session_state.session_index = 0
                st.session_state.session_xp = 0
                st.session_state.session_bonus_claimed = False
                st.rerun()
            if st.button("🏠 BACK HOME", key="session_home", use_container_width=True):
                st.session_state.session_active = False
                st.session_state.session_plan = []
                go_to("Home")
    bottom_nav("Start Session")


# =========================================================
# AI COACH
# =========================================================

elif st.session_state.page == "AI Coach":
    render_html("""<div class='section-heading' style='font-size:2rem;font-weight:950;color:#202124!important;margin:8px 0 4px;'>🤖 AI Coach</div><div style='color:#686d72;font-weight:650;margin-bottom:12px;'>Your built-in FUT TUT coach works without an API key.</div>""")

    render_html(f"""<div class='coach-note'><strong>Coach profile</strong><br>{esc(data.get('favorite_position','Winger'))} · Level {get_level()} · {data['xp']} XP · {len(data['completed'])} drills · {get_streak()}🔥</div><div class='coach-actions'><div>🎯 Drill help</div><div>🗓️ Training plans</div><div>🧠 Tactics & progress</div></div>""")

    if not st.session_state.coach_messages:
        st.session_state.coach_messages = [{"role":"assistant","content":f"Hey {player} 👋⚽ I'm your FUT TUT Coach. You're Level {get_level()} with {len(data['completed'])} drills completed. What are we working on?"}]

    for message in st.session_state.coach_messages:
        with st.chat_message(message["role"], avatar="⚽" if message["role"] == "assistant" else "🧑"):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask your coach anything about soccer…", key="coach_chat")
    if prompt:
        prompt = prompt.strip()
        if prompt:
            st.session_state.coach_messages.append({"role":"user","content":prompt})
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                try: api_key = st.secrets.get("OPENAI_API_KEY")
                except Exception: api_key = None

            if api_key and OpenAI is not None:
                try:
                    completed_names = ", ".join(data["completed"][-15:]) or "None yet"
                    system_prompt = f"""
You are FUT TUT Coach, a practical and encouraging soccer-development coach.
Player name: {player}
Position: {data.get('favorite_position','Winger')}
Level: {get_level()}
XP: {data['xp']}
Streak: {get_streak()}
Completed FUT TUT drills: {completed_names}
Available FUT TUT drills: {', '.join(d['name'] for d in DRILLS)}

Give soccer-development advice that is useful, age-appropriate, and safety-conscious.
Personalize suggestions from the player's progress and position.
Do not claim to have observed the player physically unless the player provides the observation.
Do not diagnose injuries or medical conditions.
Only name FUT TUT drills from the available list above.
Keep answers focused and actionable.
"""
                    conversation = [{"role":"system","content":system_prompt}] + st.session_state.coach_messages[-12:]
                    model = os.environ.get("FUT_TUT_AI_MODEL", "gpt-5")
                    with st.spinner("Coach is thinking…"):
                        client = OpenAI(api_key=api_key)
                        response = client.responses.create(model=model, input=conversation)
                        answer = response.output_text
                except Exception:
                    # Never make the Coach unusable just because an optional backend failed.
                    answer = offline_coach_response(prompt) + "\n\n_(Local Coach mode — no external AI needed.)_"
            else:
                answer = offline_coach_response(prompt)
            st.session_state.coach_messages.append({"role":"assistant","content":answer})
            st.rerun()

    if st.button("🗑️ CLEAR CHAT", key="clear_chat", use_container_width=True):
        st.session_state.coach_messages = []
        st.rerun()
    bottom_nav("AI Coach")


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "Progress":
    render_html("<div class='page-title' style='font-size:2.2rem;font-weight:950;color:#202124!important;letter-spacing:-1.5px;margin:8px 0 4px;'>📈 Your Progress</div>")
    render_html(f"<div class='progress-hero'><div class='eyebrow inverse'>CURRENT LEVEL</div><div class='progress-level'>Level {get_level()}</div><div style='font-weight:800;color:rgba(255,255,255,.9)'>{data['xp']} total XP</div></div>")
    st.progress(level_progress(), text=(f"{xp_to_next_level()} XP until Level {get_level()+1}" if get_level() < MAX_LEVEL else "MAX LEVEL"))
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>⚽ Skill ratings</div>")
    for category in CATEGORIES:
        rating = skill_rating(category)
        render_html(f"<div class='skill'><div class='skill-top'><div><div class='eyebrow'>{esc(category)}</div><div class='skill-num'>{rating}</div></div><div class='skill-icon'>{'🔥' if rating >= 70 else '⚡'}</div></div></div>")
        st.progress(rating / 99)
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>🔥 Weekly goal</div>")
    week = weekly_training_days(); goal = max(1,int(data.get("weekly_goal",5)))
    st.progress(min(1,week/goal), text=f"{week}/{goal} training days")
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>🏆 Achievements</div>")
    for icon, name, desc, unlocked in achievements():
        render_html(f"<div class='achievement {'locked' if not unlocked else ''}'><div class='achievement-icon'>{icon if unlocked else '🔒'}</div><div><div class='achievement-name'>{esc(name)}</div><div class='achievement-desc'>{esc(desc)}</div></div></div>")
    render_html("<div class='section-heading' style='font-size:1.3rem;font-weight:950;color:#202124!important;margin:22px 0 10px;'>🕘 Recent training</div>")
    if not data["recent_sessions"]:
        st.info("Your training history will appear here.")
    else:
        for item in data["recent_sessions"]:
            render_html(f"<div class='history'><div><strong>⚽ {esc(item['name'])}</strong><div class='history-date'>{esc(item['category'])} · {esc(item['date'])}</div></div><div class='history-xp'>{'+'+str(item['xp'])+' XP' if item['xp'] else 'repeat'}</div></div>")

    c1,c2 = st.columns(2)
    with c1:
        if st.button("🏆 CHALLENGES", key="progress_challenges", use_container_width=True): go_to("Challenges")
    with c2:
        if st.button("👤 PROFILE", key="progress_profile", use_container_width=True): go_to("Profile")
    bottom_nav("Progress")


# =========================================================
# CHALLENGES
# =========================================================

elif st.session_state.page == "Challenges":
    render_html("<div class='page-title' style='font-size:2.2rem;font-weight:950;color:#202124!important;letter-spacing:-1.5px;margin:8px 0 4px;'>🏆 Challenges</div>")
    st.caption("One-time bonus XP quests.")
    for ch in challenges():
        done_count = sum(1 for name in ch["drills"] if name in data["completed"])
        claimed = ch["name"] in data["challenge_claimed"]
        render_html(f"<div class='challenge'><div class='eyebrow'>{esc(ch['category'])}</div><div class='challenge-title'>{esc(ch['name'])}</div><div class='challenge-meta'>{done_count}/3 complete · +{ch['reward']} XP</div></div>")
        st.progress(done_count/3)
        for name in ch["drills"]: st.write(f"{'✅' if name in data['completed'] else '⬜'} {name}")
        if claimed:
            st.success("Reward claimed ✅")
        elif challenge_complete(ch):
            if primary_button(f"🎁 CLAIM +{ch['reward']} XP", f"claim_{ch['name']}"):
                claim_challenge(ch)
                try: st.balloons()
                except Exception: pass
                st.rerun()
        else:
            st.caption("Complete all three drills to unlock the reward.")
    bottom_nav("Training")


# =========================================================
# PROFILE
# =========================================================

elif st.session_state.page == "Profile":
    render_html("<div class='page-title' style='font-size:2.2rem;font-weight:950;color:#202124!important;letter-spacing:-1.5px;margin:8px 0 4px;'>👤 Profile</div>")
    name = st.text_input("Player name", value=player, max_chars=30)
    position = st.selectbox("Favorite position", POSITIONS, index=POSITIONS.index(data["favorite_position"]) if data["favorite_position"] in POSITIONS else 0)
    goal = st.number_input("Weekly training goal", min_value=1, max_value=14, value=int(data.get("weekly_goal",5)))
    if primary_button("💾 SAVE PROFILE", "save_profile"):
        data["player_name"] = name.strip() or "Player"
        data["favorite_position"] = position
        data["weekly_goal"] = int(goal)
        save_data()
        st.success("Profile saved ⚡")
        st.rerun()
    render_html(f"<div class='player'><div class='player-ball'>⚽</div><div class='player-name'>{esc(data['player_name'])}</div><div class='player-sub'>{esc(data['favorite_position'])} · Level {get_level()}</div></div>")
    a,b = st.columns(2)
    with a:
        st.metric("Total XP", data["xp"]); st.metric("Drills", len(data["completed"]))
    with b:
        st.metric("Level", get_level()); st.metric("Streak", f"{get_streak()} 🔥")
    bottom_nav("Profile")

else:
    st.session_state.page = "Home"
    st.rerun()
