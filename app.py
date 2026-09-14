import os
import json
import random
import re
import time
import tempfile
import base64
from datetime import datetime, date, timedelta

import streamlit as st


# =========================================================
# FUT TUT 2.0
# Duolingo-inspired soccer training game
# =========================================================

st.set_page_config(
    page_title="FUT TUT ⚽",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "futtut_data.json"

XP_PER_LEVEL = 250
MAX_LEVEL = 20

CATEGORIES = [
    "Finishing",
    "Dribbling",
    "First Touch",
    "Passing",
    "Speed",
    "Soccer IQ",
]

LEVELS = ["Beginner", "Intermediate", "Advanced"]

POSITIONS = [
    "Winger",
    "Striker",
    "Midfielder",
    "Defender",
    "Fullback",
    "Goalkeeper",
]

STYLES = [
    "Balanced",
    "Technical",
    "Match-like",
]


# =========================================================
# DRILL LIBRARY
# =========================================================

DRILL_SEEDS = {
    "Finishing": [
        ("One-Touch Finishing", "Beginner", "10 min", "20 finishes",
         "Finish quickly after receiving a pass.", "Quick decisions and clean contact."),
        ("Near-Post Finishing", "Beginner", "10 min", "15 finishes",
         "Attack from a wide angle and finish into the near corner.", "Body shape and placement."),
        ("Far-Corner Placement", "Beginner", "12 min", "20 finishes",
         "Build consistency placing shots away from the keeper.", "Accuracy over power."),
        ("Moving Ball Finish", "Intermediate", "15 min", "20 finishes",
         "Receive while moving and finish with your next touch.", "Control at speed."),
        ("Cutback Finishing", "Intermediate", "15 min", "20 finishes",
         "Attack the box and finish cutback passes.", "Timing your run."),
        ("Weak-Foot Finishing", "Intermediate", "15 min", "15 finishes",
         "Build confidence finishing with your weaker foot.", "Clean technique."),
        ("First-Time Volley", "Advanced", "15 min", "15 finishes",
         "Attack aerial service and finish cleanly.", "Timing and balance."),
        ("Pressure Finishing", "Advanced", "20 min", "20 finishes",
         "Create a shooting angle while pressure closes you down.", "Speed of decision-making."),
        ("Three-Zone Finishing", "Advanced", "20 min", "30 finishes",
         "Finish from central, left and right shooting zones.", "Adaptability."),
        ("Rebound Finishing", "Advanced", "15 min", "20 finishes",
         "React quickly to second-ball opportunities around goal.", "Reactions and positioning."),
    ],

    "Dribbling": [
        ("Cone Slalom", "Beginner", "10 min", "8 runs",
         "Build close control through a cone slalom.", "Close control."),
        ("Inside-Outside", "Beginner", "10 min", "5 × 30 sec",
         "Develop rhythm with inside and outside touches.", "Touch rhythm."),
        ("Figure Eight", "Beginner", "12 min", "8 rounds",
         "Improve turning and close control.", "Turning mechanics."),
        ("Change of Direction", "Intermediate", "15 min", "12 attacks",
         "Explode away after a sharp change of direction.", "Change of pace."),
        ("Elastico Reps", "Intermediate", "12 min", "30 attempts",
         "Practice the elastico from slow to match speed.", "Clean contact and timing."),
        ("1v1 Attack", "Intermediate", "15 min", "12 attacks",
         "Combine feints with acceleration in 1v1 situations.", "Timing and confidence."),
        ("Tight-Space Dribbling", "Advanced", "15 min", "5 × 45 sec",
         "Control the ball in a small area under constant movement.", "Control under pressure."),
        ("Speed Dribble", "Advanced", "15 min", "10 runs",
         "Combine longer touches with high-speed running.", "Ball control at speed."),
        ("Move + Burst", "Advanced", "18 min", "12 attacks",
         "Use a move to beat a defender and explode away.", "Game-speed dribbling."),
        ("Stop-Start Dribbling", "Advanced", "15 min", "12 runs",
         "Change speed repeatedly to create separation.", "Changes of pace."),
    ],

    "First Touch": [
        ("Wall First Touch", "Beginner", "10 min", "50 touches",
         "Improve control from simple wall passes.", "Soft first touch."),
        ("Open-Body Receive", "Beginner", "12 min", "30 reps",
         "Receive while opening your body to the field.", "Scanning and body shape."),
        ("First Touch Across Body", "Beginner", "10 min", "30 touches",
         "Move the ball across your body after receiving.", "Directional control."),
        ("Turn on First Touch", "Intermediate", "15 min", "25 turns",
         "Receive and turn in one fluid movement.", "Touch direction."),
        ("High-Ball Control", "Intermediate", "15 min", "20 controls",
         "Bring bouncing or aerial balls under control.", "Cushioning the ball."),
        ("Receive Under Pressure", "Intermediate", "15 min", "20 reps",
         "Control while reacting to a nearby defender.", "Awareness before receiving."),
        ("Back-Foot Receiving", "Advanced", "15 min", "30 reps",
         "Receive on the back foot to keep play moving.", "Playing forward quickly."),
        ("First Touch Escape", "Advanced", "18 min", "20 escapes",
         "Use the first touch to escape a tight situation.", "First touch under pressure."),
        ("Match-Speed Receiving", "Advanced", "20 min", "30 reps",
         "Practice receiving at realistic game speed.", "Real-game control."),
        ("Receive-and-Play", "Advanced", "18 min", "25 reps",
         "Receive, orient and play the next action quickly.", "Speed from control to action."),
    ],

    "Passing": [
        ("Two-Touch Wall Passing", "Beginner", "10 min", "50 passes",
         "Build passing rhythm with a wall.", "Technique and consistency."),
        ("One-Touch Wall Passing", "Beginner", "10 min", "50 passes",
         "Improve speed with one-touch combinations.", "Passing rhythm."),
        ("Passing Gates", "Beginner", "12 min", "40 passes",
         "Pass accurately through small cone gates.", "Accuracy."),
        ("Third-Man Passing", "Intermediate", "15 min", "20 combinations",
         "Improve combination play with a third player.", "Movement after passing."),
        ("Split Passes", "Intermediate", "15 min", "25 passes",
         "Thread passes through narrow spaces.", "Weight and precision."),
        ("Long-Passing Technique", "Intermediate", "18 min", "25 passes",
         "Practice controlled longer passes.", "Balance and contact."),
        ("Weak-Foot Passing", "Advanced", "15 min", "50 passes",
         "Develop confidence passing with your weaker side.", "Technique under repetition."),
        ("Pressure Passing", "Advanced", "18 min", "30 passes",
         "Make quick passing decisions under pressure.", "Speed of thought."),
        ("Switch of Play", "Advanced", "20 min", "20 switches",
         "Practice changing the point of attack.", "Awareness and execution."),
        ("Third-Line Combination", "Advanced", "18 min", "20 combinations",
         "Link three passing lanes with movement.", "Speed and awareness."),
    ],

    "Speed": [
        ("Acceleration Starts", "Beginner", "10 min", "8 starts",
         "Practice quick acceleration over short distances.", "First few steps."),
        ("Cone Sprints", "Beginner", "12 min", "8 sprints",
         "Build repeated sprint quality.", "Quality speed."),
        ("Reaction Sprint", "Beginner", "12 min", "10 reactions",
         "React quickly to a direction cue.", "Reaction speed."),
        ("Sprint + Ball", "Intermediate", "15 min", "8 runs",
         "Combine acceleration with ball control.", "Speed with control."),
        ("Change-of-Direction Sprint", "Intermediate", "15 min", "8 runs",
         "Accelerate, cut and accelerate again.", "Deceleration and re-acceleration."),
        ("Curved Sprint Runs", "Intermediate", "15 min", "8 runs",
         "Practice curved movements useful for attacking runs.", "Running angle."),
        ("Repeated Sprint", "Advanced", "18 min", "10 sprints",
         "Practice repeated bursts with controlled recovery.", "Consistent effort."),
        ("Explosive First Step", "Advanced", "15 min", "10 starts",
         "Improve your first movement when attacking space.", "Acceleration mechanics."),
        ("Game-Speed Running", "Advanced", "20 min", "10 runs",
         "Mix jogs, bursts and changes like a match.", "Changing gears."),
        ("Burst + Recover", "Advanced", "18 min", "10 rounds",
         "Alternate short bursts and controlled recovery.", "Repeatable acceleration."),
    ],

    "Soccer IQ": [
        ("Scanning Drill", "Beginner", "10 min", "20 receives",
         "Build the habit of checking your surroundings before receiving.", "Scanning."),
        ("Shoulder Check", "Beginner", "10 min", "30 checks",
         "Practice checking both shoulders before receiving.", "Awareness."),
        ("Find the Space", "Beginner", "12 min", "20 movements",
         "Move away from defenders into open space.", "Movement without the ball."),
        ("Third-Man Run", "Intermediate", "15 min", "15 combinations",
         "Recognize when to run beyond the receiver.", "Timing."),
        ("Winger Decision-Making", "Intermediate", "15 min", "20 decisions",
         "Choose between dribbling, passing and crossing.", "Decision-making."),
        ("When to Carry", "Intermediate", "15 min", "20 decisions",
         "Recognize when carrying is better than passing.", "Recognizing space."),
        ("Defensive Scanning", "Advanced", "15 min", "20 checks",
         "Track runners while staying aware of the ball.", "Positioning."),
        ("Final-Third Choices", "Advanced", "18 min", "20 decisions",
         "Improve choices around the box.", "Fast decisions."),
        ("Match Reading", "Advanced", "20 min", "20 situations",
         "Recognize what the game is asking for.", "Understanding the game."),
        ("Space + Timing", "Advanced", "18 min", "20 decisions",
         "Combine movement, scanning and timing.", "Reading the next action."),
    ],
}


def build_drills():
    drills = []

    for category, rows in DRILL_SEEDS.items():
        for index, row in enumerate(rows):
            name, level, time_text, reps, description, focus = row

            drills.append({
                "id": f"{category.lower().replace(' ', '_')}_{index + 1}",
                "name": name,
                "category": category,
                "level": level,
                "time": time_text,
                "reps": reps,
                "description": description,
                "focus": focus,
                "xp": {
                    "Beginner": 25,
                    "Intermediate": 30,
                    "Advanced": 35,
                }[level],
                "video_url": None,
                "steps": [
                    "Set up your space and equipment.",
                    "Start controlled so your technique stays clean.",
                    "Perform the drill for the listed repetitions.",
                    "Repeat from both sides when possible.",
                    "Only increase speed when your control is consistent.",
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
}


def fresh_data():
    return json.loads(json.dumps(DEFAULT_DATA))


def load_data():
    if not os.path.exists(DATA_FILE):
        return fresh_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            raw = json.load(file)

        if not isinstance(raw, dict):
            return fresh_data()

        result = fresh_data()
        result.update(raw)

        if not isinstance(result.get("completed"), list):
            result["completed"] = []

        if not isinstance(result.get("completion_counts"), dict):
            result["completion_counts"] = {}

        if not isinstance(result.get("training_dates"), list):
            result["training_dates"] = []

        if not isinstance(result.get("challenge_claimed"), list):
            result["challenge_claimed"] = []

        if not isinstance(result.get("recent_sessions"), list):
            result["recent_sessions"] = []

        result["completed"] = list(dict.fromkeys(
            name for name in result["completed"]
            if name in DRILL_BY_NAME
        ))

        return result

    except Exception:
        return fresh_data()


data = load_data()


def save_data():
    temporary = DATA_FILE + ".tmp"

    try:
        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        os.replace(temporary, DATA_FILE)

    except Exception:
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
        except Exception:
            pass


# =========================================================
# SESSION STATE
# =========================================================

SESSION_DEFAULTS = {
    "page": "Home",
    "selected_drill": None,

    "drill_active": False,
    "drill_started_at": None,
    "drill_elapsed": 0,

    "session_active": False,
    "session_plan": [],
    "session_index": 0,
    "session_xp": 0,
    "session_name": "",
    "session_bonus_claimed": False,

    "coach_messages": [],

    "show_level_up": False,
    "last_xp_gain": 0,

    "intro_seen": False,
}

for key, value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HELPERS
# =========================================================

def go_to(page):
    st.session_state.page = page
    st.rerun()


def get_level(xp=None):
    if xp is None:
        xp = data["xp"]

    return min(MAX_LEVEL, int(xp) // XP_PER_LEVEL + 1)


def level_progress(xp=None):
    if xp is None:
        xp = data["xp"]

    level = get_level(xp)

    if level >= MAX_LEVEL:
        return 1.0

    current_level_xp = (level - 1) * XP_PER_LEVEL
    return min(
        1.0,
        max(
            0.0,
            (xp - current_level_xp) / XP_PER_LEVEL
        )
    )


def xp_to_next_level():
    level = get_level()

    if level >= MAX_LEVEL:
        return 0

    return level * XP_PER_LEVEL - data["xp"]


def current_week():
    return date.today().strftime("%Y-%W")


def weekly_training_days():
    week = current_week()
    count = 0

    for value in data.get("training_dates", []):
        try:
            if date.fromisoformat(str(value)[:10]).strftime("%Y-%W") == week:
                count += 1
        except Exception:
            pass

    return count


def get_streak():
    dates = set(data.get("training_dates", []))

    if not dates:
        return 0

    today = date.today()
    streak = 0

    while today.isoformat() in dates:
        streak += 1
        today -= timedelta(days=1)

    return streak


def record_training_day():
    today = date.today().isoformat()

    if today not in data["training_dates"]:
        data["training_dates"].append(today)

    save_data()


def daily_goal_progress():
    if data.get("daily_goal_date") != date.today().isoformat():
        data["daily_goal_date"] = date.today().isoformat()
        data["daily_goal_progress"] = 0
        save_data()

    return min(1.0, data.get("daily_goal_progress", 0) / 1)


def add_xp(amount):
    old_level = get_level()

    data["xp"] += int(amount)

    new_level = get_level()

    if new_level > old_level:
        st.session_state.show_level_up = True

    st.session_state.last_xp_gain = int(amount)

    save_data()


def complete_drill(drill):
    """
    XP is awarded ONCE per drill.
    A completed drill can still be trained again,
    but it won't generate duplicate completion XP.
    """

    name = drill["name"]

    already_completed = name in data["completed"]

    if already_completed:
        record_training_day()
        return 0, False

    gain = drill["xp"]

    data["completed"].append(name)
    data["completion_counts"][name] = (
        int(data["completion_counts"].get(name, 0)) + 1
    )

    data["sessions"] += 1

    data["daily_goal_progress"] = min(
        1,
        int(data.get("daily_goal_progress", 0)) + 1
    )

    data["recent_sessions"].insert(
        0,
        {
            "name": name,
            "category": drill["category"],
            "xp": gain,
            "date": datetime.now().strftime("%b %d, %Y"),
        },
    )

    data["recent_sessions"] = data["recent_sessions"][:10]

    record_training_day()
    add_xp(gain)

    return gain, True


def skill_rating(category):
    names = [
        drill["name"]
        for drill in DRILLS
        if drill["category"] == category
    ]

    completed = sum(
        1
        for name in names
        if name in data["completed"]
    )

    return min(
        99,
        50 + int((completed / max(1, len(names))) * 49)
    )


def recommendation():
    uncompleted = [
        drill
        for drill in DRILLS
        if drill["name"] not in data["completed"]
    ]

    if not uncompleted:
        return random.choice(DRILLS)

    position = data.get("favorite_position", "Winger")

    position_categories = {
        "Winger": ["Dribbling", "Speed", "First Touch", "Finishing"],
        "Striker": ["Finishing", "First Touch", "Dribbling"],
        "Midfielder": ["Passing", "First Touch", "Soccer IQ"],
        "Defender": ["First Touch", "Passing", "Soccer IQ"],
        "Fullback": ["Speed", "Passing", "Dribbling"],
        "Goalkeeper": ["First Touch", "Passing", "Soccer IQ"],
    }

    preferred = position_categories.get(position, CATEGORIES)

    preferred_pool = [
        drill
        for drill in uncompleted
        if drill["category"] in preferred
    ]

    pool = preferred_pool or uncompleted

    # Stable daily recommendation.
    rng = random.Random(
        date.today().toordinal() + data["xp"]
    )

    return rng.choice(pool)


def drill_unlock_index(drill):
    category_drills = [
        d for d in DRILLS
        if d["category"] == drill["category"]
    ]

    return category_drills.index(drill)


def is_unlocked(drill):
    index = drill_unlock_index(drill)

    completed_in_category = sum(
        1
        for d in DRILLS
        if d["category"] == drill["category"]
        and d["name"] in data["completed"]
    )

    # First 2 are immediately playable.
    # Later drills unlock as the player progresses.
    return index <= completed_in_category + 1


# =========================================================
# ACHIEVEMENTS
# =========================================================

def achievements():
    completed = len(data["completed"])
    categories = sum(
        1
        for category in CATEGORIES
        if any(
            d["category"] == category and
            d["name"] in data["completed"]
            for d in DRILLS
        )
    )

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


# =========================================================
# CHALLENGES
# =========================================================

def challenges():
    result = []

    for category in CATEGORIES:
        drills = [
            d["name"]
            for d in DRILLS
            if d["category"] == category
        ][:3]

        result.append({
            "name": f"{category} Starter",
            "category": category,
            "drills": drills,
            "reward": 75,
        })

    return result


def challenge_complete(challenge):
    return all(
        name in data["completed"]
        for name in challenge["drills"]
    )


def claim_challenge(challenge):
    key = challenge["name"]

    if key in data["challenge_claimed"]:
        return False

    if not challenge_complete(challenge):
        return False

    data["challenge_claimed"].append(key)

    add_xp(challenge["reward"])

    return True


# =========================================================
# PREMIUM-STYLE UI
# =========================================================

st.markdown(
    """
<style>

:root {
    --green: #58cc02;
    --green-dark: #46a900;
    --blue: #1cb0f6;
    --yellow: #ffc800;
    --red: #ff4b4b;
    --purple: #ce82ff;

    --bg: #f7f7f7;
    --card: #ffffff;
    --text: #202124;
    --muted: #777777;
    --border: #e5e5e5;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(88,204,2,.10), transparent 30%),
        radial-gradient(circle at 100% 20%, rgba(28,176,246,.08), transparent 30%),
        var(--bg);
}

.block-container {
    max-width: 900px;
    padding-top: 1.2rem;
    padding-bottom: 7rem;
}

h1, h2, h3, h4, p, span, div, label {
    font-family: Arial, Helvetica, sans-serif;
}

h1 {
    font-weight: 900 !important;
    letter-spacing: -1.8px;
    color: var(--text) !important;
}

h2, h3 {
    color: var(--text) !important;
    font-weight: 850 !important;
}

p {
    color: #606060 !important;
}

/* Hide Streamlit chrome */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

/* Main app cards */

.ft-card {
    background: white;
    border: 2px solid var(--border);
    border-radius: 22px;
    padding: 22px;
    margin: 12px 0;
    box-shadow: 0 4px 0 rgba(0,0,0,.05);
}

.ft-card-green {
    background: linear-gradient(135deg, #58cc02, #78df20);
    border: 0;
    color: white;
    border-radius: 24px;
    padding: 26px;
    margin: 12px 0;
    box-shadow: 0 6px 0 #46a900;
}

.ft-card-blue {
    background: linear-gradient(135deg, #1cb0f6, #43c4ff);
    border: 0;
    color: white;
    border-radius: 24px;
    padding: 26px;
    margin: 12px 0;
    box-shadow: 0 6px 0 #1595cf;
}

.ft-card-yellow {
    background: linear-gradient(135deg, #ffc800, #ffd83f);
    border: 0;
    color: #222;
    border-radius: 24px;
    padding: 26px;
    margin: 12px 0;
    box-shadow: 0 6px 0 #d9aa00;
}

.eyebrow {
    font-size: .72rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: .12em;
    color: #8a8a8a !important;
}

.hero-title {
    font-size: clamp(2.4rem, 8vw, 4.4rem);
    line-height: .95;
    font-weight: 950;
    letter-spacing: -4px;
    color: white !important;
    margin: 8px 0;
}

.hero-sub {
    color: rgba(255,255,255,.9) !important;
    font-size: 1rem;
    font-weight: 650;
}

.big-number {
    font-size: 2.3rem;
    font-weight: 950;
    color: var(--text);
}

.small-label {
    font-size: .72rem;
    text-transform: uppercase;
    font-weight: 850;
    letter-spacing: .08em;
    color: #888;
}

/* Buttons */

.stButton > button {
    min-height: 52px !important;
    border-radius: 15px !important;
    border: 2px solid #dedede !important;
    background: white !important;
    color: #202124 !important;
    font-size: .98rem !important;
    font-weight: 900 !important;
    box-shadow: 0 3px 0 #d8d8d8 !important;
    transition: .12s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    border-color: #c8c8c8 !important;
}

.stButton > button:active {
    transform: translateY(2px);
    box-shadow: 0 1px 0 #d8d8d8 !important;
}

.primary-button .stButton > button {
    background: var(--green) !important;
    border-color: var(--green-dark) !important;
    color: white !important;
    box-shadow: 0 4px 0 var(--green-dark) !important;
}

/* Inputs */

div[data-baseweb="select"] > div,
input,
textarea {
    border-radius: 13px !important;
}

/* Progress */

.stProgress > div > div > div > div {
    border-radius: 999px !important;
}

.stProgress > div > div {
    border-radius: 999px !important;
}

/* Chat */

[data-testid="stChatMessage"] {
    border-radius: 18px;
    margin-bottom: 10px;
}

/* Mobile */

@media (max-width: 700px) {

    .block-container {
        padding-left: 14px;
        padding-right: 14px;
        padding-top: .8rem;
    }

    .ft-card {
        border-radius: 18px;
        padding: 18px;
    }

    .hero-title {
        font-size: 3rem;
    }

    .stButton > button {
        min-height: 55px !important;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# INTRO
# =========================================================

if not st.session_state.intro_seen:

    st.markdown(
        """
        <div style="
            min-height:70vh;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
        ">
            <div>
                <div style="
                    font-size:5rem;
                    font-weight:950;
                    letter-spacing:-6px;
                ">
                    FUT ⚽ TUT
                </div>

                <div style="
                    font-size:1rem;
                    font-weight:850;
                    letter-spacing:.16em;
                    color:#777;
                    margin-top:12px;
                ">
                    TRAIN LIKE YOU MEAN IT.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="primary-button">', unsafe_allow_html=True)

    if st.button(
        "START TRAINING ⚡",
        use_container_width=True,
        key="intro_start",
    ):
        st.session_state.intro_seen = True
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# =========================================================
# LEVEL-UP SCREEN
# =========================================================

if st.session_state.show_level_up:

    st.markdown(
        """
        <div class="ft-card-yellow" style="text-align:center;">
            <div style="font-size:4rem;">🏆</div>
            <div style="
                font-size:2.7rem;
                font-weight:950;
            ">
                LEVEL UP!
            </div>
            <div style="
                font-size:1.1rem;
                font-weight:800;
            ">
                You reached Level %s
            </div>
        </div>
        """
        % get_level(),
        unsafe_allow_html=True,
    )

    if st.button(
        "LET'S GO ⚡",
        use_container_width=True,
        key="dismiss_level",
    ):
        st.session_state.show_level_up = False
        st.rerun()

    st.stop()


# =========================================================
# TOP NAV
# =========================================================

top_left, top_mid, top_right = st.columns([1.4, 2, 1.4])

with top_left:
    if st.button(
        "⚽ FUT TUT",
        key="top_home",
        use_container_width=True,
    ):
        go_to("Home")

with top_mid:
    level = get_level()

    st.markdown(
        f"""
        <div style="text-align:center;">
            <div style="
                font-weight:950;
                color:#777;
                font-size:.72rem;
                letter-spacing:.08em;
            ">
                LEVEL {level}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    st.markdown(
        f"""
        <div style="
            text-align:right;
            font-weight:950;
            font-size:1rem;
            padding-top:8px;
        ">
            🔥 {get_streak()}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# BOTTOM NAV
# =========================================================

def bottom_nav():
    st.markdown("---")

    cols = st.columns(5)

    buttons = [
        ("🏠", "Home"),
        ("🗺️", "Training"),
        ("⚡", "Start Session"),
        ("🤖", "AI Coach"),
        ("📈", "Progress"),
    ]

    for col, (icon, page) in zip(cols, buttons):
        with col:
            if st.button(
                icon,
                key=f"bottom_{page}",
                use_container_width=True,
            ):
                go_to(page)


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "Home":

    rec = recommendation()

    player = str(data.get("player_name", "Player"))

    st.markdown(
        f"""
        <div class="ft-card-green">

            <div class="eyebrow" style="color:rgba(255,255,255,.8)!important;">
                WELCOME BACK
            </div>

            <div class="hero-title">
                Hey, {player} 👋
            </div>

            <div class="hero-sub">
                Ready to get better?
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # XP BAR

    st.markdown(
        f"""
        <div class="ft-card">

            <div style="
                display:flex;
                justify-content:space-between;
                font-weight:900;
            ">
                <span>Level {level}</span>
                <span>{data["xp"]} XP</span>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(
        level_progress(),
        text=f"{xp_to_next_level()} XP until Level {min(MAX_LEVEL, level + 1)}"
        if level < MAX_LEVEL
        else "MAX LEVEL",
    )

    # DAILY GOAL

    completed_today = int(data.get("daily_goal_progress", 0))

    st.markdown(
        """
        <div class="ft-card">
            <div class="eyebrow">TODAY'S MISSION</div>
            <h2 style="margin-bottom:4px;">Complete 1 drill 🎯</h2>
            <p>One focused session is all you need to keep your progress moving.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(
        1.0 if completed_today else 0.0,
        text="Daily goal complete! 🔥" if completed_today else "0 / 1 drills",
    )

    # RECOMMENDATION

    st.markdown("### ⭐ Recommended for you")

    st.markdown(
        f"""
        <div class="ft-card">

            <div class="eyebrow">
                {rec["category"]} · {rec["level"]}
            </div>

            <h2>{rec["name"]}</h2>

            <p>{rec["description"]}</p>

            <div style="
                display:flex;
                gap:14px;
                flex-wrap:wrap;
                font-weight:800;
                color:#777;
            ">
                <span>⏱ {rec["time"]}</span>
                <span>🔁 {rec["reps"]}</span>
                <span>⚡ +{rec["xp"]} XP</span>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="primary-button">', unsafe_allow_html=True)

    if st.button(
        "▶ START TODAY'S DRILL",
        use_container_width=True,
        key="home_start_drill",
    ):
        st.session_state.selected_drill = rec["name"]
        st.session_state.page = "Drill"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    a, b = st.columns(2)

    with a:
        if st.button(
            "🗺️ Training Path",
            use_container_width=True,
            key="home_training",
        ):
            go_to("Training")

    with b:
        if st.button(
            "⚡ Build Session",
            use_container_width=True,
            key="home_session",
        ):
            go_to("Start Session")

    # STATS

    st.markdown("### Your stats")

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            f"""
            <div class="ft-card" style="text-align:center;">
                <div class="big-number">{data["xp"]}</div>
                <div class="small-label">XP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b:
        st.markdown(
            f"""
            <div class="ft-card" style="text-align:center;">
                <div class="big-number">{len(data["completed"])}</div>
                <div class="small-label">DRILLS</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c:
        st.markdown(
            f"""
            <div class="ft-card" style="text-align:center;">
                <div class="big-number">{get_streak()}🔥</div>
                <div class="small-label">STREAK</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    bottom_nav()


# =========================================================
# DRILL PAGE
# =========================================================

elif st.session_state.page == "Drill":

    drill = DRILL_BY_NAME.get(
        st.session_state.selected_drill
    )

    if drill is None:
        st.session_state.selected_drill = recommendation()["name"]
        st.rerun()

    # BACK

    if st.button("← Back", key="drill_back"):
        st.session_state.drill_active = False
        go_to("Home")

    st.markdown(
        f"""
        <div class="ft-card">

            <div class="eyebrow">
                {drill["category"]} · {drill["level"]}
            </div>

            <h1>{drill["name"]}</h1>

            <p style="font-size:1.05rem;">
                {drill["description"]}
            </p>

            <div style="
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                font-weight:850;
            ">
                <span>⏱ {drill["time"]}</span>
                <span>🔁 {drill["reps"]}</span>
                <span>⚡ +{drill["xp"]} XP</span>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # VIDEO SLOT

    st.markdown("### 🎥 Watch & learn")

    if drill.get("video_url"):
        st.video(drill["video_url"])
    else:
        st.markdown(
            """
            <div class="ft-card-blue" style="text-align:center;">

                <div style="font-size:3rem;">🎥</div>

                <h2 style="color:white!important;">
                    Demo video coming soon
                </h2>

                <p style="color:white!important;">
                    Your FUT TUT video library will live here.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # INSTRUCTIONS

    st.markdown("### 📚 How to do it")

    for number, step in enumerate(drill["steps"], 1):

        st.markdown(
            f"""
            <div class="ft-card">

                <div style="
                    display:flex;
                    gap:14px;
                    align-items:center;
                ">

                    <div style="
                        width:38px;
                        height:38px;
                        border-radius:50%;
                        background:#58cc02;
                        color:white;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-weight:950;
                    ">
                        {number}
                    </div>

                    <div style="font-weight:750;">
                        {step}
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ACTIVE DRILL

    if not st.session_state.drill_active:

        st.markdown('<div class="primary-button">', unsafe_allow_html=True)

        if st.button(
            "▶ START DRILL",
            use_container_width=True,
            key="real_start_drill",
        ):
            st.session_state.drill_active = True
            st.session_state.drill_started_at = time.time()
            st.session_state.drill_elapsed = 0
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    else:

        elapsed = int(
            time.time() -
            st.session_state.drill_started_at
        )

        st.session_state.drill_elapsed = elapsed

        st.markdown(
            """
            <div class="ft-card-green" style="text-align:center;">

                <div class="eyebrow" style="color:white!important;">
                    DRILL ACTIVE
                </div>

                <div style="
                    font-size:4rem;
                    font-weight:950;
                    color:white;
                ">
                    %02d:%02d
                </div>

                <div class="hero-sub">
                    Stay focused. Quality first.
                </div>

            </div>
            """
            % (elapsed // 60, elapsed % 60),
            unsafe_allow_html=True,
        )

        st.progress(
            min(1.0, elapsed / 600),
            text="Training in progress",
        )

        st.markdown('<div class="primary-button">', unsafe_allow_html=True)

        if st.button(
            "✅ COMPLETE DRILL",
            use_container_width=True,
            key="complete_active_drill",
        ):

            gain, first_completion = complete_drill(drill)

            st.session_state.drill_active = False
            st.session_state.drill_started_at = None

            if first_completion:
                st.success(
                    f"🔥 GREAT WORK! +{gain} XP"
                )
            else:
                st.info(
                    "Drill completed again! "
                    "You've already earned its XP reward."
                )

            st.session_state.last_xp_gain = gain

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button(
            "⏸ Pause / Exit Drill",
            use_container_width=True,
            key="exit_active_drill",
        ):
            st.session_state.drill_active = False
            st.session_state.drill_started_at = None
            st.rerun()

    # COACH NOTES

    with st.expander("🧠 Coach notes"):
        st.write(f"**Main focus:** {drill['focus']}")
        st.write(f"**Common mistake:** {drill['mistakes']}")
        st.write(f"**Progression:** {drill['progression']}")
        st.write(f"**Coach tip:** {drill['tip']}")

    if drill["name"] in data["completed"]:
        st.success("✅ You've unlocked this drill's XP reward already.")

    bottom_nav()


# =========================================================
# TRAINING PATH
# =========================================================

elif st.session_state.page == "Training":

    st.title("🗺️ Training Path")
    st.caption("Your soccer skill tree. Complete drills to unlock the next ones.")

    selected_category = st.selectbox(
        "Choose a skill",
        CATEGORIES,
        key="path_category",
    )

    category_drills = [
        d for d in DRILLS
        if d["category"] == selected_category
    ]

    completed_category = sum(
        1
        for d in category_drills
        if d["name"] in data["completed"]
    )

    st.progress(
        completed_category / len(category_drills),
        text=f"{completed_category}/{len(category_drills)} completed",
    )

    for index, drill in enumerate(category_drills):

        unlocked = is_unlocked(drill)
        completed = drill["name"] in data["completed"]

        if completed:
            icon = "✅"
        elif unlocked:
            icon = "▶️"
        else:
            icon = "🔒"

        st.markdown(
            f"""
            <div class="ft-card">

                <div style="
                    display:flex;
                    align-items:center;
                    gap:15px;
                ">

                    <div style="
                        font-size:2rem;
                        min-width:45px;
                        text-align:center;
                    ">
                        {icon}
                    </div>

                    <div style="flex:1;">

                        <div class="eyebrow">
                            DRILL {index + 1} · {drill["level"]}
                        </div>

                        <h3 style="margin:4px 0;">
                            {drill["name"]}
                        </h3>

                        <div style="color:#777;">
                            {drill["time"]} · +{drill["xp"]} XP
                        </div>

                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if unlocked:

            if st.button(
                "VIEW DRILL →",
                key=f"path_{drill['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_drill = drill["name"]
                st.session_state.page = "Drill"
                st.rerun()

        else:
            st.caption(
                "🔒 Complete more drills in this skill to unlock this one."
            )

    bottom_nav()


# =========================================================
# SESSION BUILDER
# =========================================================

elif st.session_state.page == "Start Session":

    st.title("⚡ Training Session")
    st.caption("Build a focused session in seconds.")

    if not st.session_state.session_active:

        duration = st.select_slider(
            "Session length",
            options=[15, 30, 45, 60],
            value=30,
            format_func=lambda x: f"{x} min",
        )

        category = st.selectbox(
            "Main skill",
            ["Mixed"] + CATEGORIES,
        )

        difficulty = st.selectbox(
            "Difficulty",
            ["Mixed"] + LEVELS,
        )

        style = st.selectbox(
            "Training style",
            STYLES,
        )

        target_count = {
            15: 3,
            30: 5,
            45: 7,
            60: 9,
        }[duration]

        pool = DRILLS[:]

        if category != "Mixed":
            pool = [
                d for d in pool
                if d["category"] == category
            ]

        if difficulty != "Mixed":
            pool = [
                d for d in pool
                if d["level"] == difficulty
            ]

        if style == "Technical":
            pool = [
                d for d in pool
                if d["category"] in
                ["First Touch", "Passing", "Dribbling"]
            ] or pool

        elif style == "Match-like":
            pool = [
                d for d in pool
                if d["category"] in
                ["Soccer IQ", "Finishing", "Dribbling", "Speed"]
            ] or pool

        pool = [
            d for d in pool
            if d["name"] not in data["completed"]
        ] or pool

        plan = pool[:]
        random.shuffle(plan)
        plan = plan[:min(target_count, len(plan))]

        st.markdown(
            f"""
            <div class="ft-card-blue">

                <div class="eyebrow" style="color:white!important;">
                    YOUR SESSION
                </div>

                <div style="
                    font-size:2.3rem;
                    font-weight:950;
                    color:white;
                ">
                    {len(plan)} drills
                </div>

                <div class="hero-sub">
                    {duration} minutes · {style}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="primary-button">', unsafe_allow_html=True)

        if st.button(
            "🚀 START SESSION",
            use_container_width=True,
            key="start_generated_session",
        ):

            st.session_state.session_plan = plan
            st.session_state.session_index = 0
            st.session_state.session_xp = 0
            st.session_state.session_bonus_claimed = False
            st.session_state.session_name = (
                f"{style} Session"
            )
            st.session_state.session_active = True

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    else:

        plan = st.session_state.session_plan
        index = st.session_state.session_index

        if index < len(plan):

            current = plan[index]

            st.progress(
                index / len(plan),
                text=f"Drill {index + 1} of {len(plan)}",
            )

            st.markdown(
                f"""
                <div class="ft-card-green">

                    <div class="eyebrow" style="color:white!important;">
                        {st.session_state.session_name}
                    </div>

                    <div class="hero-title">
                        {current["name"]}
                    </div>

                    <div class="hero-sub">
                        +{current["xp"]} XP
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(current["description"])

            st.markdown("### How to do it")

            for step in current["steps"]:
                st.write("• " + step)

            if st.button(
                "✅ COMPLETE & NEXT",
                use_container_width=True,
                key=f"session_next_{index}",
            ):

                gain, first = complete_drill(current)

                if first:
                    st.session_state.session_xp += gain

                st.session_state.session_index += 1

                st.rerun()

            if st.button(
                "❌ END SESSION",
                use_container_width=True,
                key="end_session",
            ):
                st.session_state.session_active = False
                st.session_state.session_plan = []
                st.rerun()

        else:

            if not st.session_state.session_bonus_claimed:

                add_xp(50)

                st.session_state.session_xp += 50
                st.session_state.session_bonus_claimed = True

            st.markdown(
                f"""
                <div class="ft-card-yellow" style="text-align:center;">

                    <div style="font-size:4rem;">
                        🏆
                    </div>

                    <div style="
                        font-size:2.8rem;
                        font-weight:950;
                    ">
                        SESSION COMPLETE
                    </div>

                    <div style="
                        font-size:1.5rem;
                        font-weight:900;
                    ">
                        +{st.session_state.session_xp} XP
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "🔥 TRAIN AGAIN",
                use_container_width=True,
                key="train_again",
            ):
                st.session_state.session_active = False
                st.session_state.session_plan = []
                st.session_state.session_index = 0
                st.session_state.session_xp = 0
                st.rerun()

    bottom_nav()


# =========================================================
# AI COACH
# =========================================================

elif st.session_state.page == "AI Coach":

    st.title("🤖 AI Coach")
    st.caption("Your FUT TUT coach. Ask about training, technique, tactics, or your progress.")

    if not st.session_state.coach_messages:

        st.session_state.coach_messages = [
            {
                "role": "assistant",
                "content": (
                    f"Hey {data.get('player_name', 'Player')} 👋⚽ "
                    f"I'm your FUT TUT Coach. "
                    f"You're Level {get_level()} with "
                    f"{len(data['completed'])} drills completed. "
                    f"What are we working on?"
                ),
            }
        ]

    for message in st.session_state.coach_messages:

        avatar = "⚽" if message["role"] == "assistant" else "🧑"

        with st.chat_message(
            message["role"],
            avatar=avatar,
        ):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask your coach anything about soccer..."
    )

    if prompt:

        st.session_state.coach_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        # Try OpenAI if configured.
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            try:
                api_key = st.secrets.get("OPENAI_API_KEY")
            except Exception:
                api_key = None

        if api_key:

            try:

                from openai import OpenAI

                client = OpenAI(api_key=api_key)

                completed_names = ", ".join(
                    data["completed"][-12:]
                ) or "None yet"

                system_prompt = f"""
You are FUT TUT Coach, an encouraging soccer development coach.

Player:
Name: {data.get("player_name", "Player")}
Position: {data.get("favorite_position", "Winger")}
Level: {get_level()}
XP: {data["xp"]}
Streak: {get_streak()}
Completed drills: {completed_names}

Give practical soccer-development advice.
Do not pretend you observed the player physically unless they provide information.
Do not diagnose injuries or medical conditions.
Keep advice appropriate for a young soccer player.
When recommending FUT TUT drills, only recommend drills from the provided library.
Be encouraging but honest.
"""

                conversation = [
                    {
                        "role": "system",
                        "content": system_prompt,
                    }
                ]

                conversation.extend(
                    st.session_state.coach_messages[-10:]
                )

                response = client.responses.create(
                    model=os.environ.get(
                        "FUT_TUT_AI_MODEL",
                        "gpt-5",
                    ),
                    input=conversation,
                )

                answer = response.output_text

            except Exception as exc:

                answer = (
                    "I couldn't reach the AI Coach right now. "
                    "Check that your OpenAI API setup is configured correctly."
                )

        else:

            # Honest fallback — not pretending this is AI.
            prompt_lower = prompt.lower()

            if "drill" in prompt_lower:

                best = recommendation()

                answer = (
                    f"Based on your current progress, I'd start with "
                    f"**{best['name']}**. It's a {best['level']} "
                    f"{best['category']} drill worth +{best['xp']} XP. "
                    f"Open it from your recommended training path and focus "
                    f"on {best['focus'].lower()}."
                )

            elif "progress" in prompt_lower:

                answer = (
                    f"You're Level {get_level()} with {data['xp']} XP "
                    f"and {len(data['completed'])} different drills completed. "
                    f"Your current streak is {get_streak()} days. 🔥"
                )

            else:

                answer = (
                    "Your AI Coach is ready once an OpenAI API key is connected. "
                    "For now I can still use your FUT TUT progress to suggest "
                    "drills and training priorities."
                )

        st.session_state.coach_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    if st.button(
        "🗑️ Clear Coach Chat",
        use_container_width=True,
    ):
        st.session_state.coach_messages = []
        st.rerun()

    bottom_nav()


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "Progress":

    st.title("📈 Your Progress")

    st.markdown(
        f"""
        <div class="ft-card-green">

            <div class="eyebrow" style="color:white!important;">
                CURRENT LEVEL
            </div>

            <div class="hero-title">
                Level {get_level()}
            </div>

            <div class="hero-sub">
                {data["xp"]} total XP
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(
        level_progress(),
        text=(
            f"{xp_to_next_level()} XP until Level {get_level() + 1}"
            if get_level() < MAX_LEVEL
            else "MAX LEVEL"
        ),
    )

    # Skill cards

    st.markdown("### ⚽ Skill Ratings")

    for category in CATEGORIES:

        rating = skill_rating(category)

        st.markdown(
            f"""
            <div class="ft-card">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">

                    <div>
                        <div class="eyebrow">
                            {category}
                        </div>

                        <div style="
                            font-size:1.7rem;
                            font-weight:950;
                        ">
                            {rating}
                        </div>
                    </div>

                    <div style="
                        font-size:2rem;
                    ">
                        {"🔥" if rating >= 70 else "⚡"}
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.progress(rating / 99)

    # Weekly goal

    st.markdown("### 🔥 Weekly Goal")

    weekly = weekly_training_days()
    goal = max(1, int(data.get("weekly_goal", 5)))

    st.progress(
        min(1.0, weekly / goal),
        text=f"{weekly}/{goal} training days",
    )

    # Achievements

    st.markdown("### 🏆 Achievements")

    for icon, name, description, unlocked in achievements():

        opacity = "1" if unlocked else ".45"

        st.markdown(
            f"""
            <div class="ft-card"
                 style="opacity:{opacity};">

                <div style="
                    display:flex;
                    align-items:center;
                    gap:16px;
                ">

                    <div style="font-size:2rem;">
                        {icon if unlocked else "🔒"}
                    </div>

                    <div>

                        <div style="
                            font-size:1.1rem;
                            font-weight:950;
                        ">
                            {name}
                        </div>

                        <div style="color:#777;">
                            {description}
                        </div>

                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # Recent

    st.markdown("### 🕘 Recent Training")

    if not data["recent_sessions"]:
        st.info("Your training history will appear here.")

    else:

        for item in data["recent_sessions"]:

            st.markdown(
                f"""
                <div class="ft-card">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                    ">

                        <div>
                            <strong>⚽ {item["name"]}</strong>
                            <div style="color:#888;">
                                {item["category"]}
                            </div>
                        </div>

                        <div style="
                            font-weight:950;
                            color:#58a900;
                        ">
                            +{item["xp"]} XP
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    bottom_nav()


# =========================================================
# CHALLENGES
# =========================================================

elif st.session_state.page == "Challenges":

    st.title("🏆 Challenges")
    st.caption("Finish mini skill quests and collect bonus XP.")

    for challenge in challenges():

        done = sum(
            1
            for name in challenge["drills"]
            if name in data["completed"]
        )

        claimed = (
            challenge["name"]
            in data["challenge_claimed"]
        )

        st.markdown(
            f"""
            <div class="ft-card">

                <div class="eyebrow">
                    {challenge["category"]}
                </div>

                <h2>{challenge["name"]}</h2>

                <div style="
                    font-size:1.1rem;
                    font-weight:900;
                ">
                    {done}/3 completed
                </div>

                <div style="color:#777;">
                    Reward: +{challenge["reward"]} XP
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.progress(done / 3)

        for drill_name in challenge["drills"]:

            st.write(
                f"{'✅' if drill_name in data['completed'] else '⬜'} "
                f"{drill_name}"
            )

        if claimed:

            st.success("Reward claimed! ✅")

        elif challenge_complete(challenge):

            if st.button(
                f"🎁 CLAIM +{challenge['reward']} XP",
                use_container_width=True,
                key=f"claim_{challenge['name']}",
            ):

                if claim_challenge(challenge):
                    st.success("Reward claimed! 🏆")
                    st.rerun()

        else:

            st.info(
                "Complete all three drills to unlock this reward."
            )

    bottom_nav()


# =========================================================
# PROFILE
# =========================================================

elif st.session_state.page == "Profile":

    st.title("👤 Profile")

    name = st.text_input(
        "Player name",
        value=str(data.get("player_name", "Player")),
    )

    position = st.selectbox(
        "Favorite position",
        POSITIONS,
        index=(
            POSITIONS.index(data["favorite_position"])
            if data["favorite_position"] in POSITIONS
            else 0
        ),
    )

    goal = st.number_input(
        "Weekly training goal",
        min_value=1,
        max_value=14,
        value=int(data.get("weekly_goal", 5)),
    )

    if st.button(
        "💾 SAVE PROFILE",
        use_container_width=True,
    ):

        data["player_name"] = name.strip() or "Player"
        data["favorite_position"] = position
        data["weekly_goal"] = int(goal)

        save_data()

        st.success("Profile saved! ⚡")
        st.rerun()

    st.markdown("### Player card")

    st.markdown(
        f"""
        <div class="ft-card-blue">

            <div style="font-size:3rem;">
                ⚽
            </div>

            <div style="
                font-size:2rem;
                font-weight:950;
                color:white;
            ">
                {data["player_name"]}
            </div>

            <div class="hero-sub">
                {data["favorite_position"]} · Level {get_level()}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📊 Career stats")

    a, b = st.columns(2)

    with a:
        st.metric(
            "Total XP",
            data["xp"],
        )

        st.metric(
            "Drills",
            len(data["completed"]),
        )

    with b:
        st.metric(
            "Level",
            get_level(),
        )

        st.metric(
            "Streak",
            f"{get_streak()} 🔥",
        )

    bottom_nav()


# =========================================================
# FALLBACK
# =========================================================

else:

    st.session_state.page = "Home"
    st.rerun()
