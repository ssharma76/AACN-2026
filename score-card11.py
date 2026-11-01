import base64
from datetime import datetime, date
import json
import os
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ----------------- App Configuration -----------------
st.set_page_config(
    page_title="ANNUAL ATHLETICS CHAMPIONSHIP 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------- Persistent Configuration File -----------------
CONFIG_FILE = "video_config.json"
HEARTBEAT_FILE = "active_visitors.json"
TOTAL_VISITORS_FILE = "visitor_count.txt"

def load_video_config():
    default_cfg = {
        "yt_news_id": "xz-pqId7ym8",
        "yt_live_channel_id": "",
        "is_live_active": False,
        "gallery_dir": "gallery",
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return {**default_cfg, **data}
        except Exception:
            return default_cfg
    return default_cfg

def save_video_config(news_id, live_id, is_live, gallery_dir):
    cfg = {
        "yt_news_id": news_id,
        "yt_live_channel_id": live_id,
        "is_live_active": is_live,
        "gallery_dir": gallery_dir,
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        st.error(f"Error saving config: {e}")

# ----------------- Visitor Counter (Seed = 253) -----------------
def track_visitors():
    now = datetime.now().timestamp()
    INITIAL_SEED = 253

    if "has_counted_visit" not in st.session_state:
        count = INITIAL_SEED
        if os.path.exists(TOTAL_VISITORS_FILE):
            try:
                with open(TOTAL_VISITORS_FILE, "r") as f:
                    val = int(f.read().strip())
                    count = max(val, INITIAL_SEED)
            except Exception:
                count = INITIAL_SEED
        else:
            count = INITIAL_SEED

        count += 1
        try:
            with open(TOTAL_VISITORS_FILE, "w") as f:
                f.write(str(count))
        except Exception:
            pass
        st.session_state.has_counted_visit = True
        st.session_state.current_visit_count = count

    total_visits = st.session_state.get("current_visit_count", INITIAL_SEED)

    session_id = st.session_state.get("client_id", None)
    if not session_id:
        session_id = base64.b64encode(os.urandom(6)).decode()
        st.session_state.client_id = session_id

    heartbeats = {}
    if os.path.exists(HEARTBEAT_FILE):
        try:
            with open(HEARTBEAT_FILE, "r") as f:
                heartbeats = json.load(f)
        except Exception:
            heartbeats = {}

    heartbeats[session_id] = now
    active_heartbeats = {k: v for k, v in heartbeats.items() if now - v < 65}

    try:
        with open(HEARTBEAT_FILE, "w") as f:
            json.dump(active_heartbeats, f)
    except Exception:
        pass

    live_now = max(len(active_heartbeats), 1)
    return total_visits, live_now

# ----------------- Helper: Base64 Background & Image Encoder -----------------
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def load_gallery_images(gallery_path):
    if not gallery_path or not os.path.exists(gallery_path):
        return ""
    valid_ext = (".jpg", ".jpeg", ".png", ".webp")
    try:
        files = sorted(
            [f for f in os.listdir(gallery_path) if f.lower().endswith(valid_ext)],
            key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', x)]
        )
    except Exception:
        files = []

    if not files:
        return ""

    cards = ["""
        <div class="gallery-divider">
            📸 EVENT PHOTO GALLERY • TRACK & FIELD HIGHLIGHTS
        </div>
    """]
    for f in files:
        p = os.path.join(gallery_path, f)
        b64 = get_base64_image(p)
        if not b64:
            continue
        ev_label = os.path.splitext(f)[0].upper()
        cards.append(f"""
            <div class="gallery-photo-card">
                <div class="gallery-tag-pill">🏅 {ev_label}</div>
                <img src="data:image/jpeg;base64,{b64}" class="gallery-img" alt="{ev_label}" loading="lazy"/>
            </div>
        """)
    return "".join(cards)

# ----------------- Robust YouTube ID Extractor -----------------
def clean_yt_id(val):
    if not val:
        return ""
    val = str(val).strip()
    match = re.search(r'(?:v=|\/embed\/|\/live\/|youtu\.be\/|\/v\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})', val)
    if match:
        return match.group(1)
    return val

# ----------------- Safe Admin Credentials Fallback -----------------
try:
    ADMIN_USER = st.secrets["ADMIN_USER"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "ApsMeerut@2026"

# ----------------- Google Sheets Live Endpoints -----------------
SPREADSHEET_ID = "1SvVfpeE99a5KqPGxMjD_tQVYoMd-YUUT4ZGhelNE_FE"
RESULTS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=Results"
PP_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=House_Points"
CREDS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=Credentials"
ANNOUNCE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=Announcements"

def fetch_live_data():
    try:
        results_df = pd.read_csv(RESULTS_CSV_URL)
        results_df.columns = [
            c.strip().lower().replace(" ", "_").replace("/", "_").replace(".", "")
            for c in results_df.columns
        ]
    except Exception:
        results_df = pd.DataFrame()

    try:
        pp_df = pd.read_csv(PP_CSV_URL)
        pp_df.columns = [c.strip().lower() for c in pp_df.columns]
    except Exception:
        pp_df = pd.DataFrame(columns=["house", "pp_points"])

    try:
        announce_df = pd.read_csv(ANNOUNCE_CSV_URL)
        announce_df.columns = [c.strip().lower() for c in announce_df.columns]
    except Exception:
        announce_df = pd.DataFrame()

    return results_df, pp_df, announce_df

def fetch_credentials():
    try:
        creds_df = pd.read_csv(CREDS_CSV_URL)
        creds_df.columns = [c.strip().lower() for c in creds_df.columns]
        return dict(
            zip(creds_df["username"].astype(str), creds_df["password"].astype(str))
        )
    except Exception:
        return {"incharge1": "apspass2026", "incharge2": "apspass2026", ADMIN_USER: ADMIN_PASSWORD}

# ----------------- Canonical House Definitions -----------------
houses = ["CARIAPPA", "MANEKSHAW", "SUNDARJI", "VAIDYA"]

def normalize_house(name):
    if not name or pd.isna(name):
        return "MANEKSHAW"
    n = str(name).strip().upper()
    if n in ["C", "CAR", "CARIAPPA"]:
        return "CARIAPPA"
    elif n in ["M", "MAN", "MANEKSHAW"]:
        return "MANEKSHAW"
    elif n in ["S", "SUN", "SUNDARJI"]:
        return "SUNDARJI"
    elif n in ["V", "VAI", "VAIDYA"]:
        return "VAIDYA"
    return n

# ----------------- Session Routing -----------------
if "view_mode" not in st.session_state:
    st.session_state.view_mode = st.query_params.get("view", "display")

# =========================================================================
# 1. LOGIN & IN-CHARGE AUTHENTICATION
# =========================================================================
if st.session_state.view_mode == "login":
    bg_base64 = get_base64_image("final-image-green-2.png")

    bg_css = f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, rgba(2, 20, 45, 0.78), rgba(0, 10, 25, 0.85)), 
                    url("data:image/png;base64,{bg_base64}") no-repeat center center fixed !important;
        background-size: cover !important;
    }}
    header[data-testid="stHeader"], footer {{
        display: none !important;
    }}
    .main .block-container {{
        max-width: 520px !important;
        margin: 8vh auto auto auto !important;
        background: rgba(3, 20, 48, 0.95) !important;
        backdrop-filter: blur(16px);
        border-radius: 18px !important;
        padding: 26px 22px !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75) !important;
        border: 2px solid rgba(255, 215, 0, 0.5) !important;
    }}
    .landing-title {{
        text-align: center;
        color: #ffffff !important;
        font-size: 23px !important;
        font-weight: 900 !important;
        text-transform: uppercase;
    }}
    .motto-banner {{
        background: #ffd700;
        color: #001833;
        font-size: 13px;
        font-weight: 900;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
        margin: 6px auto;
        letter-spacing: 1px;
    }}
    </style>
    """
    st.markdown(bg_css, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="text-align: center;">
            <div style="font-size: 40px; margin-bottom: 5px;">🏆</div>
            <div class="landing-title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div style="color:#ffd700; font-weight:800; font-size:17px; margin-top: 4px;">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="motto-banner">⚡ RUN WITH COURAGE • RISE WITH PRIDE ⚡</div>
            <div style="color:#93c5fd; font-size:14px; font-weight:800; margin-bottom:15px;">(28th October – 5th November 2026)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    role = st.radio(
        "Select Portal View:",
        ["📺 Open Public Scoreboard", "🔒 In-Charge Console"],
    )

    if role == "📺 Open Public Scoreboard":
        if st.button("🚀 Launch Live Display", type="primary", use_container_width=True):
            st.session_state.view_mode = "display"
            st.query_params["view"] = "display"
            st.rerun()
    else:
        with st.form("login_form"):
            st.markdown("##### 🔑 Score In-Charge Sign In")
            u_name = st.text_input("Username").strip()
            p_word = st.text_input("Password", type="password").strip()
            submitted = st.form_submit_button("🔓 Unlock Controls", type="primary", use_container_width=True)
            if submitted:
                valid_creds = fetch_credentials()
                if u_name in valid_creds and valid_creds[u_name] == p_word:
                    st.session_state.view_mode = "admin"
                    st.session_state.logged_user = u_name
                    st.query_params["view"] = "admin"
                    st.success(f"Authenticated as {u_name}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# =========================================================================
# 2. SCORE IN-CHARGE PORTAL
# =========================================================================
elif st.session_state.view_mode == "admin":
    top_c1, top_c2, top_c3 = st.columns([5, 2.5, 2.5])
    top_c1.title("📝 In-Charge Portal")
    if top_c2.button("🖥️ Open Live Screen", use_container_width=True):
        st.session_state.view_mode = "display"
        st.query_params["view"] = "display"
        st.rerun()
    if top_c3.button("🚪 Logout", use_container_width=True):
        st.session_state.view_mode = "login"
        st.session_state.pop("logged_user", None)
        st.query_params.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🎥 Video & Event Photo Gallery Management")
    st.caption("Settings saved here are written to the server configuration and apply to all screens instantly.")

    current_cfg = load_video_config()

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("#### 1. News Highlights Video")
        input_news_link = st.text_input(
            "YouTube Video Link or ID:",
            value=current_cfg.get("yt_news_id", "xz-pqId7ym8"),
            help="Accepts any YouTube URL or 11-digit ID"
        )
        parsed_news = clean_yt_id(input_news_link)
        st.info(f"Target Active Video ID: **`{parsed_news}`**")

        st.markdown("#### 2. YouTube Live Stream")
        input_live_link = st.text_input(
            "Live Stream Link or Video ID:",
            value=current_cfg.get("yt_live_channel_id", ""),
            placeholder="e.g. live video ID or full YouTube URL"
        )
        parsed_live = clean_yt_id(input_live_link)
        if parsed_live:
            st.info(f"Target Live Stream ID: **`{parsed_live}`**")

    with col_v2:
        st.markdown("#### 3. Live Broadcast Switch")
        live_switch = st.toggle("🔴 Turn ON Live Stream Mode", value=current_cfg.get("is_live_active", False))
        if live_switch:
            st.success("● LIVE BROADCAST IS ACTIVE: Display board will show this live stream.")
        else:
            st.warning("○ LIVE BROADCAST IS OFF: Display board shows 'No Live Streaming Available Right Now'.")

        st.markdown("#### 4. Event Photos Folder Path")
        input_gallery_path = st.text_input(
            "Folder containing EV-1, EV-1-1 images:",
            value=current_cfg.get("gallery_dir", "gallery"),
            help="Provide local path (e.g. gallery or G:\\My Drive\\Athletics_Photos)"
        )
        if os.path.exists(input_gallery_path):
            img_count = len([f for f in os.listdir(input_gallery_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
            st.caption(f"✅ Folder found! Detected {img_count} event photo(s).")
        else:
            st.caption("⚠️ Folder does not exist yet. Creating default 'gallery' folder.")

        st.write("")
        if st.button("💾 Save All Settings to All Displays", type="primary", use_container_width=True):
            save_video_config(parsed_news, parsed_live, live_switch, input_gallery_path)
            st.success("Configuration successfully saved and active across all displays!")
            st.rerun()

    st.markdown("---")
    st.markdown(f"👉 **[Click Here to Open Master Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**")
    res_df, _, _ = fetch_live_data()
    if not res_df.empty:
        st.dataframe(res_df, use_container_width=True)

# =========================================================================
# 3. LIVE FULL-SCREEN DISPLAY BOARD (100VH AUTO-FIT VIEWPORT)
# =========================================================================
elif st.session_state.view_mode == "display":
    with st.sidebar:
        if st.button("⬅️ Switch to In-Charge Login"):
            st.session_state.view_mode = "login"
            st.query_params["view"] = "login"
            st.rerun()

        st.markdown("### 🎛️ Display Adjustments")
        scroll_speed = st.slider("Results Scroll Speed (seconds)", min_value=0, max_value=240, value=90, step=5)
        marquee_velocity = st.slider("Marquee Speed (px/s)", min_value=25, max_value=250, value=85, step=5)
        marquee_font_size = st.slider("Marquee Font (px)", min_value=13, max_value=28, value=16, step=1)
        marquee_bg_color = st.color_picker("Marquee Background", "#001833")
        marquee_text_color = st.color_picker("Marquee Text Color", "#FFE600")

    st.markdown(
        """
        <style>
        /* Zero outer Streamlit body padding for seamless 100vh fit */
        .block-container {
            padding: 0rem !important;
            margin: 0rem !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"], footer {
            display: none !important;
        }
        iframe {
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    @st.fragment(run_every=180)
    def render_live_screen():
        df, pp_df, ann_df = fetch_live_data()

        if not df.empty and "event_date" in df.columns:
            df["parsed_date"] = pd.to_datetime(df["event_date"], format="mixed", dayfirst=True, errors="coerce")
            df = df.sort_values(by="parsed_date", ascending=False).reset_index(drop=True)
            df["display_date"] = df["parsed_date"].dt.strftime("%d-%m-%Y")
            df["display_date"] = df["display_date"].fillna(df["event_date"])
        elif not df.empty:
            df["display_date"] = ""

        pp_dict = {}
        if not pp_df.empty and "house" in pp_df.columns and "pp_points" in pp_df.columns:
            for _, r in pp_df.iterrows():
                pp_dict[normalize_house(r["house"])] = int(r["pp_points"] if pd.notna(r["pp_points"]) else 0)

        tally = {
            h: {"Gold": 0, "Silver": 0, "Bronze": 0, "TotalMedals": 0, "PP": int(pp_dict.get(h, 0)), "EarnedPts": 0, "TP": 0}
            for h in houses
        }

        if not df.empty:
            for _, r in df.iterrows():
                gh = normalize_house(r.get("gold_house", ""))
                sh = normalize_house(r.get("silver_house", ""))
                bh = normalize_house(r.get("bronze_house", ""))

                if gh in tally:
                    tally[gh]["Gold"] += 1
                    try:
                        tally[gh]["EarnedPts"] += int(float(r.get("gold_points", 5)))
                    except Exception:
                        tally[gh]["EarnedPts"] += 5

                if sh in tally:
                    tally[sh]["Silver"] += 1
                    try:
                        tally[sh]["EarnedPts"] += int(float(r.get("silver_points", 4)))
                    except Exception:
                        tally[sh]["EarnedPts"] += 4

                if bh in tally:
                    tally[bh]["Bronze"] += 1
                    try:
                        tally[bh]["EarnedPts"] += int(float(r.get("bronze_points", 3)))
                    except Exception:
                        tally[bh]["EarnedPts"] += 3

        for h in tally:
            tally[h]["TotalMedals"] = tally[h]["Gold"] + tally[h]["Silver"] + tally[h]["Bronze"]
            tally[h]["TP"] = tally[h]["PP"] + tally[h]["EarnedPts"]

        sorted_houses = sorted(
            houses,
            key=lambda h: (tally[h]["TP"], tally[h]["Gold"], tally[h]["Silver"], tally[h]["Bronze"], tally[h]["TotalMedals"]),
            reverse=True,
        )

        tally_html = ""
        for rank, h in enumerate(sorted_houses, start=1):
            rank_display = "👑 1" if rank == 1 else f"#{rank}"
            tally_html += f"""
            <div class="house-tally-row">
                <div style="font-weight:900; color:#1e293b;">{rank_display}</div>
                <div><span class="house-box-label house-{h}">{h}</span></div>
                <div class="tally-num gold-text">{tally[h]['Gold']}</div>
                <div class="tally-num silver-text">{tally[h]['Silver']}</div>
                <div class="tally-num bronze-text">{tally[h]['Bronze']}</div>
                <div class="tally-num total-col">{tally[h]['TotalMedals']}</div>
                <div class="tally-num pp-col">{tally[h]['PP']}</div>
                <div class="tally-num tp-col">{tally[h]['TP']}</div>
            </div>
            """

        marquee_msg = "🏆 ANNUAL ATHLETICS CHAMPIONSHIP 2026 IS LIVE! Results and House Points updated directly from official records."
        if not ann_df.empty and "type" in ann_df.columns and "content" in ann_df.columns:
            m_row = ann_df[ann_df["type"].str.lower() == "marquee"]
            if not m_row.empty:
                marquee_msg = str(m_row.iloc[0]["content"])

        cards_html = ""
        if df.empty:
            cards_html = """
            <div style="text-align:center; padding: 40px 15px; color:#1e293b; font-weight:900; font-size:18px;">
                🏆 Events are underway! Results will appear here as soon as verified.
            </div>
            """
        else:
            for idx, r in df.iterrows():
                gh = normalize_house(r.get("gold_house", ""))
                sh = normalize_house(r.get("silver_house", ""))
                bh = normalize_house(r.get("bronze_house", ""))

                def format_stacked(val):
                    if pd.isna(val) or not str(val).strip():
                        return "-"
                    return str(val).replace("\n", "<br>")

                cards_html += f"""
                <div class="event-doc-card">
                    <div class="doc-card-header">
                        <span class="doc-badge-event">{r.get('event_name', '')}</span>
                        <span class="doc-badge-cat">{r.get('category', '')}</span>
                        <span class="doc-date-badge">📅 {r.get('display_date', '')}</span>
                    </div>
                    <div class="table-responsive-wrapper">
                        <table class="doc-sub-table">
                            <thead>
                                <tr>
                                    <th>Place</th>
                                    <th>Team / Athlete</th>
                                    <th>Class</th>
                                    <th>Adm. No.</th>
                                    <th>Ti/Ht/Dis</th>
                                    <th>House</th>
                                    <th>Pts</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="row-gold">
                                    <td class="place-badge gold-bg">1st 🥇</td>
                                    <td class="daylight-name">{format_stacked(r.get('gold_student_name', ''))}</td>
                                    <td class="daylight-bold-class">{r.get('gold_class_sec', '-')}</td>
                                    <td class="daylight-bold-adm">{format_stacked(r.get('gold_adm_no', ''))}</td>
                                    <td class="daylight-bold-perf">{r.get('gold_perf_(time_ht_dis)', '-')}</td>
                                    <td><span class="mini-house-badge house-{gh}">{gh}</span></td>
                                    <td class="bold-pts">+{r.get('gold_points', 5)}</td>
                                </tr>
                                <tr class="row-silver">
                                    <td class="place-badge silver-bg">2nd 🥈</td>
                                    <td class="daylight-name">{format_stacked(r.get('silver_student_name', ''))}</td>
                                    <td class="daylight-bold-class">{r.get('silver_class_sec', '-')}</td>
                                    <td class="daylight-bold-adm">{format_stacked(r.get('silver_adm_no', ''))}</td>
                                    <td class="daylight-bold-perf">{r.get('silver_perf_(time_ht_dis)', '-')}</td>
                                    <td><span class="mini-house-badge house-{sh}">{sh}</span></td>
                                    <td class="bold-pts">+{r.get('silver_points', 4)}</td>
                                </tr>
                                <tr class="row-bronze">
                                    <td class="place-badge bronze-bg">3rd 🥉</td>
                                    <td class="daylight-name">{format_stacked(r.get('bronze_student_name', ''))}</td>
                                    <td class="daylight-bold-class">{r.get('bronze_class_sec', '-')}</td>
                                    <td class="daylight-bold-adm">{format_stacked(r.get('bronze_adm_no', ''))}</td>
                                    <td class="daylight-bold-perf">{r.get('bronze_perf_(time_ht_dis)', '-')}</td>
                                    <td><span class="mini-house-badge house-{bh}">{bh}</span></td>
                                    <td class="bold-pts">+{r.get('bronze_points', 3)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                """

        # Read directly from persistent configuration file
        active_cfg = load_video_config()
        news_vid = clean_yt_id(active_cfg.get("yt_news_id", "xz-pqId7ym8"))
        live_vid = clean_yt_id(active_cfg.get("yt_live_channel_id", ""))
        is_live_on = "true" if active_cfg.get("is_live_active", False) else "false"

        # Load photos from Google Drive / Local Gallery Directory
        gallery_html = load_gallery_images(active_cfg.get("gallery_dir", "gallery"))
        combined_right_content = cards_html + gallery_html

        if scroll_speed > 0 and len(df) > 0:
            anim_css = f"animation: seamlessScrollUp {scroll_speed}s linear infinite;"
            scroll_content = combined_right_content + combined_right_content
        else:
            anim_css = "animation: none;"
            scroll_content = combined_right_content

        # Visitor Counter (Tracks seed from 253)
        total_visitors, live_visitors = track_visitors()

        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }}
    
    /* 100vh FULL VIEWPORT ENCLOSURE (NO WINDOW-LEVEL OVERFLOW) */
    html, body {{
        background-color: #cbd5e1;
        width: 100vw;
        height: 100vh;
        max-height: 100vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        padding: 2px 4px;
    }}

    /* ---------------- THREE-PART PROFESSIONAL BALANCED HEADER ---------------- */
    .top-banner {{
        background: linear-gradient(90deg, #001730 0%, #002b54 50%, #001730 100%);
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 6px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 3.5px solid #ffcc00;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        flex-shrink: 0;
    }}

    /* LEFT WING: DATE & TIME FLIP CLOCK */
    .header-left-wing {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        min-width: 180px;
        gap: 3px;
    }}
    .flip-clock {{
        display: flex;
        align-items: center;
        gap: 2px;
        background: #000000;
        border: 1.5px solid #ffd700;
        border-radius: 6px;
        padding: 3px 6px;
    }}
    .flap-card {{
        background: #18181b;
        color: #ffd700;
        font-family: monospace;
        font-size: 16px;
        font-weight: 900;
        padding: 2px 4px;
        border-radius: 3px;
    }}
    .flap-colon {{ color: #ffffff; font-weight: 900; font-size: 15px; }}
    .date-badge-pill {{
        background: rgba(2, 43, 84, 0.9);
        color: #ffd700;
        border: 1px solid #38bdf8;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11.5px;
        font-weight: 900;
        letter-spacing: 0.5px;
    }}

    /* CENTER MAIN STAGE: SCHOOL NAME, TITLE & MOTTO */
    .banner-center {{
        text-align: center;
        flex-grow: 1;
        padding: 0 10px;
    }}
    .top-banner .title {{
        font-size: clamp(19px, 2.5vw, 28px);
        font-weight: 900;
        text-transform: uppercase;
        color: #ffffff;
        line-height: 1.1;
        letter-spacing: 0.8px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    }}
    .top-banner .school-name {{
        font-size: clamp(15px, 2vw, 21px);
        font-weight: 900;
        color: #ffd700;
        text-transform: uppercase;
        margin-top: 3px;
        letter-spacing: 0.8px;
    }}
    .motto-pill {{
        display: inline-block;
        background: linear-gradient(90deg, #d97706, #f59e0b);
        color: #000000;
        font-size: clamp(11.5px, 1.3vw, 14px);
        font-weight: 900;
        letter-spacing: 1.5px;
        padding: 2px 14px;
        border-radius: 20px;
        margin-top: 4px;
        text-transform: uppercase;
        box-shadow: 0 2px 6px rgba(0,0,0,0.5);
    }}

    /* RIGHT WING: WEATHER & AQI */
    .header-right-wing {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        min-width: 180px;
        gap: 3px;
    }}
    .weather-aqi-card {{
        background: rgba(0, 0, 0, 0.45);
        border: 1.5px solid #38bdf8;
        border-radius: 6px;
        padding: 4px 8px;
        text-align: right;
        font-size: 11.5px;
        font-weight: 800;
        color: #fff;
    }}
    .aqi-pill {{
        background: #ea580c;
        padding: 1px 5px;
        border-radius: 4px;
        font-weight: 900;
        font-size: 11px;
    }}
    .date-bracket-top {{
        font-size: 11px;
        font-weight: 800;
        color: #93c5fd;
    }}

    /* ---------------- COMPACT TICKER ---------------- */
    .top-ticker {{
        width: 100%;
        background-color: {marquee_bg_color};
        color: {marquee_text_color};
        padding: 4px 0;
        font-size: {marquee_font_size}px;
        font-weight: 900;
        overflow: hidden;
        white-space: nowrap;
        border-bottom: 2.5px solid #f59e0b;
        border-radius: 0 0 6px 6px;
        margin-bottom: 4px;
        flex-shrink: 0;
    }}
    #tickerWrapper {{ display: inline-block; white-space: nowrap; }}

    /* ---------------- DYNAMIC FIT MAIN STAGE ---------------- */
    .dashboard-grid {{
        display: grid;
        grid-template-columns: 3.8fr 6.2fr;
        gap: 8px;
        width: 100%;
        flex: 1 1 0;
        min-height: 0; /* Critical for inner scrolling */
    }}

    @media (max-width: 860px) {{
        .top-banner {{ flex-direction: column; text-align: center; gap: 6px; }}
        .header-left-wing, .header-right-wing {{ width: 100%; align-items: center; justify-content: center; }}
        .dashboard-grid {{ grid-template-columns: 1fr !important; overflow-y: auto; }}
        html, body {{ overflow-y: auto; height: auto; }}
    }}

    .main-panel {{
        background: #ffffff;
        border: 2px solid #002244;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        height: 100%;
        min-height: 0;
    }}
    .panel-top-header {{
        background: #002244;
        color: #ffffff;
        padding: 5px 10px;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }}
    .panel-top-title {{
        font-size: 14.5px;
        font-weight: 900;
        text-transform: uppercase;
        color: #ffd700;
    }}
    .panel-top-sub {{
        font-size: 11px;
        color: #dbeafe;
        font-weight: 700;
    }}

    /* ---------------- TALLY TABLE (COMPACT) ---------------- */
    .tally-container {{
        padding: 4px 4px;
        background: #f8fafc;
        overflow-x: auto;
        flex-shrink: 0;
    }}
    .medal-icon-row {{
        display: grid;
        grid-template-columns: 0.8fr 2fr 0.8fr 0.8fr 0.8fr 0.8fr 0.8fr 1.1fr;
        text-align: center;
        margin-bottom: 4px;
        font-size: 11.5px;
        font-weight: 900;
        color: #0f172a;
    }}
    .medal-header-col {{
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    .medal-coin {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        font-weight: 900;
        font-size: 10.5px;
    }}
    .coin-gold {{ background: #f59e0b; color: #fff; }}
    .coin-silver {{ background: #94a3b8; color: #fff; }}
    .coin-bronze {{ background: #ea580c; color: #fff; }}

    .house-tally-row {{
        display: grid;
        grid-template-columns: 0.8fr 2fr 0.8fr 0.8fr 0.8fr 0.8fr 0.8fr 1.1fr;
        align-items: center;
        text-align: center;
        background: #ffffff;
        border: 1.5px solid #94a3b8;
        border-radius: 5px;
        margin-bottom: 3px;
        padding: 3px 2px;
    }}
    .house-box-label {{
        display: inline-block;
        padding: 2px 2px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 900;
        width: 95%;
        text-transform: uppercase;
    }}
    .house-MANEKSHAW {{ background: #E60000 !important; color: #ffffff !important; }}
    .house-CARIAPPA {{ background: #008800 !important; color: #ffffff !important; }}
    .house-SUNDARJI {{ background: #0044CC !important; color: #ffffff !important; }}
    .house-VAIDYA {{ background: #FFB800 !important; color: #000000 !important; }}

    .tally-num {{ font-size: 13.5px; font-weight: 900; }}
    .gold-text {{ color: #d97706; }}
    .silver-text {{ color: #475569; }}
    .bronze-text {{ color: #c2410c; }}
    .total-col {{ color: #0284c7; }}
    .pp-col {{ color: #64748b; }}
    .tp-col {{
        background: #002244;
        color: #ffdd00 !important;
        border-radius: 3px;
        padding: 2px 4px;
        display: inline-block;
    }}

    /* ---------------- DUAL VIDEO SWITCHER ---------------- */
    .video-tab-bar {{
        background: #011326;
        display: flex;
        border-top: 2px solid #002244;
        border-bottom: 1.5px solid #0284c7;
        flex-shrink: 0;
    }}
    .video-tab-btn {{
        flex: 1;
        padding: 6px 4px;
        background: #011326;
        color: #94a3b8;
        border: none;
        cursor: pointer;
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }}
    .video-tab-btn.active {{
        background: #002b54;
        color: #ffd700;
        border-bottom: 2.5px solid #ffd700;
    }}
    .live-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #dc2626;
        display: inline-block;
        animation: liveBlink 1.2s infinite;
    }}
    @keyframes liveBlink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.2; }}
    }}

    .sub-video-stage {{
        position: relative;
        width: 100%;
        flex: 1 1 0;
        min-height: 160px;
        background: #000000;
        overflow: hidden;
    }}
    .sub-video-frame {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
    }}
    .no-live-placeholder {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, #021a38, #000814);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 12px;
        text-align: center;
        color: #ffffff;
    }}
    .no-live-icon {{ font-size: 28px; margin-bottom: 4px; }}
    .no-live-title {{ font-size: 13px; font-weight: 900; color: #f59e0b; text-transform: uppercase; margin-bottom: 2px; }}
    .no-live-sub {{ font-size: 11px; color: #94a3b8; }}

    /* ---------------- RESULTS SCROLLER (FIT TO WINDOW) ---------------- */
    .winner-scroll-box {{
        flex: 1 1 0;
        overflow-y: auto;
        overflow-x: hidden;
        position: relative;
        background: #f1f5f9;
        padding: 6px;
        scroll-behavior: smooth;
    }}
    .winner-scroll-box::-webkit-scrollbar {{
        width: 8px;
    }}
    .winner-scroll-box::-webkit-scrollbar-track {{
        background: #cbd5e1;
        border-radius: 4px;
    }}
    .winner-scroll-box::-webkit-scrollbar-thumb {{
        background: #002244;
        border-radius: 4px;
    }}

    .scroll-inner {{
        display: flex;
        flex-direction: column;
        will-change: transform;
        {anim_css}
    }}
    .winner-scroll-box:hover .scroll-inner,
    .winner-scroll-box:active .scroll-inner {{
        animation-play-state: paused !important;
    }}

    @keyframes seamlessScrollUp {{
        0% {{ transform: translateY(0); }}
        100% {{ transform: translateY(-50%); }}
    }}

    .event-doc-card {{
        background: #ffffff;
        border: 1.5px solid #64748b;
        border-radius: 6px;
        margin-bottom: 8px;
        overflow: hidden;
    }}
    .doc-card-header {{
        background: #002244;
        color: #ffffff;
        padding: 6px 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 900;
    }}
    .doc-badge-event {{ font-size: 15px; color: #ffd700; }}
    .doc-badge-cat {{ background: #ffffff; color: #002244; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-weight: 900; }}
    .doc-date-badge {{ font-size: 12px; color: #cbd5e1; }}

    .table-responsive-wrapper {{
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }}
    .doc-sub-table {{
        width: 100%;
        min-width: 460px;
        border-collapse: collapse;
        text-align: center;
        font-size: 13px;
    }}
    .doc-sub-table th {{
        background: #cbd5e1;
        color: #000;
        padding: 5px 3px;
        font-weight: 900;
    }}
    .doc-sub-table td {{
        padding: 5px 3px;
        border-bottom: 1px solid #cbd5e1;
    }}
    
    .daylight-name {{ font-weight: 900; color: #000; text-align: left; padding-left: 6px; font-size: 14px; }}
    .daylight-bold-class {{ font-weight: 900; color: #000; font-size: 13px; }}
    .daylight-bold-adm {{ font-family: monospace; font-weight: 900; color: #0f172a; font-size: 12.5px; }}
    .daylight-bold-perf {{ font-weight: 900; color: #b91c1c; font-family: monospace; font-size: 13.5px; }}
    .bold-pts {{ font-weight: 900; color: #008000; font-size: 13px; }}
    .place-badge {{ font-weight: 900; border-radius: 3px; font-size: 12.5px; }}
    .gold-bg {{ background: #fef08a; color: #854d0e; }}
    .silver-bg {{ background: #f1f5f9; color: #1e293b; }}
    .bronze-bg {{ background: #fed7aa; color: #9a3412; }}
    .mini-house-badge {{ display: inline-block; padding: 2px 4px; border-radius: 3px; font-size: 11px; font-weight: 900; }}

    /* GALLERY STYLES */
    .gallery-divider {{
        background: linear-gradient(90deg, #d97706, #002244);
        color: #ffd700;
        font-size: 13px;
        font-weight: 900;
        text-align: center;
        padding: 7px;
        margin: 12px 0 8px 0;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .gallery-photo-card {{
        position: relative;
        background: #001226;
        border: 2px solid #ffcc00;
        border-radius: 8px;
        margin-bottom: 10px;
        overflow: hidden;
    }}
    .gallery-tag-pill {{
        position: absolute;
        top: 6px;
        left: 6px;
        background: rgba(0, 24, 51, 0.88);
        color: #ffd700;
        font-size: 11.5px;
        font-weight: 900;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #ffd700;
        z-index: 2;
    }}
    .gallery-img {{
        width: 100%;
        height: 250px;
        object-fit: cover;
        object-position: center;
        display: block;
    }}

    /* ---------------- GROUNDED FOOTER (ALWAYS VISIBLE) ---------------- */
    .visitor-footer-bar {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 4px 10px;
        width: 100%;
        background: #cbd5e1;
        flex-shrink: 0;
    }}
    .visitor-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 24, 51, 0.95);
        border: 1.5px solid #ffd700;
        border-radius: 20px;
        padding: 3px 16px;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.35);
    }}
    .live-dot-green {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        display: inline-block;
        box-shadow: 0 0 8px #22c55e;
        animation: liveBlink 1.4s infinite;
    }}
    .visitor-label {{
        color: #93c5fd;
        font-size: 11.5px;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    .visitor-val {{
        color: #22c55e;
        font-family: monospace;
        font-size: 13.5px;
        font-weight: 900;
    }}
    .visitor-odometer {{
        background: #000000;
        color: #ffd700;
        font-family: "Courier New", Courier, monospace;
        font-size: 13.5px;
        font-weight: 900;
        letter-spacing: 2px;
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid #1e3a5f;
    }}
</style>
</head>
<body>

    <!-- THREE-COLUMN BALANCED PRO HEADER -->
    <div class="top-banner">
        <!-- LEFT: FLIP CLOCK & DATE -->
        <div class="header-left-wing">
            <div class="flip-clock">
                <div class="flap-card" id="flipH">00</div>
                <div class="flap-colon">:</div>
                <div class="flap-card" id="flipM">00</div>
                <div class="flap-colon">:</div>
                <div class="flap-card" id="flipS">00</div>
            </div>
            <div class="date-badge-pill" id="liveDate">29-OCT-2026</div>
        </div>

        <!-- CENTER: SCHOOL NAME, TITLE & MOTTO -->
        <div class="banner-center">
            <div class="school-name">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div><span class="motto-pill">⚡ RUN WITH COURAGE • RISE WITH PRIDE ⚡</span></div>
        </div>

        <!-- RIGHT: WEATHER & AQI -->
        <div class="header-right-wing">
            <div class="weather-aqi-card">
                <div>🌤️ <span id="meerutTemp">--°C</span> | 💧 <span id="meerutHumidity">--%</span></div>
                <div style="margin-top:2px;">AQI: <span class="aqi-pill" id="meerutAQI">--</span></div>
            </div>
            <div class="date-bracket-top">28th Oct – 5th Nov 2026</div>
        </div>
    </div>

    <!-- TICKER -->
    <div class="top-ticker" id="tickerBox">
        <div id="tickerWrapper">
            📢 <b>CHAMPIONSHIP UPDATES:</b> {marquee_msg} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 🏃 Standings refreshed live!
        </div>
    </div>

    <!-- MAIN BODY GRID (AUTO-CALCULATED FLEX HEIGHT) -->
    <div class="dashboard-grid">
        <!-- LEFT: TALLY & VIDEO PLAYER -->
        <div class="main-panel">
            <div class="panel-top-header">
                <span style="font-size:17px;">🏅</span>
                <div>
                    <div class="panel-top-title">HOUSE MEDAL TALLY (OVERALL)</div>
                    <div class="panel-top-sub">Rankings By Total Points (TP)</div>
                </div>
            </div>
            <div class="tally-container">
                <div class="medal-icon-row">
                    <div>POS</div>
                    <div>HOUSE</div>
                    <div class="medal-header-col"><div class="medal-coin coin-gold">1</div><div>G</div></div>
                    <div class="medal-header-col"><div class="medal-coin coin-silver">2</div><div>S</div></div>
                    <div class="medal-header-col"><div class="medal-coin coin-bronze">3</div><div>B</div></div>
                    <div>MED</div>
                    <div>PP</div>
                    <div style="color:#d97706;">TP</div>
                </div>
                {tally_html}
            </div>

            <!-- DUAL VIDEO SWITCHER TABS -->
            <div class="video-tab-bar">
                <button class="video-tab-btn active" id="tabHighlightsBtn" onclick="switchVideoMode('news')">
                    📹 Highlights & News
                </button>
                <button class="video-tab-btn" id="tabLiveBtn" onclick="switchVideoMode('live')">
                    <span class="live-dot"></span> Live Broadcast
                </button>
            </div>

            <!-- MEDIA PLAYER STAGE -->
            <div class="sub-video-stage">
                <iframe id="newsFrame" class="sub-video-frame"
                    src="https://www.youtube-nocookie.com/embed/{news_vid}?autoplay=0&mute=1&controls=1&modestbranding=1&rel=0" 
                    title="News Highlights" 
                    frameborder="0" 
                    referrerpolicy="strict-origin-when-cross-origin"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                    allowfullscreen>
                </iframe>

                <iframe id="liveFrame" class="sub-video-frame" style="display:none;"
                    src="https://www.youtube-nocookie.com/embed/{live_vid}?autoplay=0&mute=1&controls=1&modestbranding=1&rel=0" 
                    title="Live Stream" 
                    frameborder="0" 
                    referrerpolicy="strict-origin-when-cross-origin"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                    allowfullscreen>
                </iframe>

                <div id="noLiveCard" class="no-live-placeholder" style="display:none;">
                    <div class="no-live-icon">📡</div>
                    <div class="no-live-title">No Live Streaming Available Right Now</div>
                    <div class="no-live-sub">Trackside coverage will commence as soon as next event calls are scheduled. Please view Highlights in the left tab!</div>
                </div>
            </div>
        </div>

        <!-- RIGHT: EVENT-WISE RESULTS & PHOTOS -->
        <div class="main-panel">
            <div class="panel-top-header">
                <span style="font-size:17px;">🏃</span>
                <div>
                    <div class="panel-top-title">FINAL RESULTS & EVENT GALLERY</div>
                    <div class="panel-top-sub">Hover or Drag Scrollbar to Browse Results & Photos</div>
                </div>
            </div>
            <div class="winner-scroll-box" id="resultsScrollBox">
                <div class="scroll-inner">
                    {scroll_content}
                </div>
            </div>
        </div>
    </div>

    <!-- GROUNDED VISITOR FOOTER (LOCKED INSIDE VIEWPORT) -->
    <div class="visitor-footer-bar">
        <div class="visitor-badge">
            <span class="live-dot-green"></span>
            <span class="visitor-label">Active Users:</span>
            <span class="visitor-val">{live_visitors}</span>
            <span style="color:#64748b; margin: 0 4px;">|</span>
            <span style="font-size:13px;">🏆</span>
            <span class="visitor-label">Total Visits:</span>
            <span class="visitor-odometer">{total_visitors:06d}</span>
        </div>
    </div>

    <script>
        const isLiveActive = {is_live_on};
        const newsFrame = document.getElementById('newsFrame');
        const liveFrame = document.getElementById('liveFrame');
        const noLiveCard = document.getElementById('noLiveCard');
        const tabHighlightsBtn = document.getElementById('tabHighlightsBtn');
        const tabLiveBtn = document.getElementById('tabLiveBtn');

        function pauseIframe(iframe) {{
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.postMessage('{{"event":"command","func":"pauseVideo","args":""}}', '*');
            }}
        }}

        function switchVideoMode(mode) {{
            if (mode === 'news') {{
                tabHighlightsBtn.classList.add('active');
                tabLiveBtn.classList.remove('active');
                pauseIframe(liveFrame);
                liveFrame.style.display = 'none';
                noLiveCard.style.display = 'none';
                newsFrame.style.display = 'block';
            }} else {{
                tabLiveBtn.classList.add('active');
                tabHighlightsBtn.classList.remove('active');
                pauseIframe(newsFrame);
                newsFrame.style.display = 'none';

                if (isLiveActive) {{
                    noLiveCard.style.display = 'none';
                    liveFrame.style.display = 'block';
                }} else {{
                    liveFrame.style.display = 'none';
                    noLiveCard.style.display = 'flex';
                }}
            }}
        }}

        function updateFlipClock() {{
            const now = new Date();
            document.getElementById('flipH').textContent = String(now.getHours()).padStart(2, '0');
            document.getElementById('flipM').textContent = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('flipS').textContent = String(now.getSeconds()).padStart(2, '0');
            const opt = {{ day: '2-digit', month: 'short', year: 'numeric' }};
            document.getElementById('liveDate').textContent = now.toLocaleDateString('en-GB', opt).replace(/ /g, '-').toUpperCase();
        }}
        setInterval(updateFlipClock, 1000);
        updateFlipClock();

        async function fetchMeerutWeatherAQI() {{
            try {{
                const wRes = await fetch("https://api.open-meteo.com/v1/forecast?latitude=28.9845&longitude=77.7064&current=temperature_2m,relative_humidity_2m");
                const wData = await wRes.json();
                if (wData?.current) {{
                    document.getElementById('meerutTemp').textContent = Math.round(wData.current.temperature_2m) + "°C";
                    document.getElementById('meerutHumidity').textContent = wData.current.relative_humidity_2m + "%";
                }}
                const aqiRes = await fetch("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.9845&longitude=77.7064&current=pm2_5");
                const aqiData = await aqiRes.json();
                if (aqiData?.current) {{
                    const pm = Math.round(aqiData.current.pm2_5 || 120);
                    let label = "Moderate";
                    let bg = "#ea580c";
                    if (pm < 50) {{ label = "Good"; bg = "#16a34a"; }}
                    else if (pm > 150) {{ label = "Poor"; bg = "#dc2626"; }}
                    const pill = document.getElementById('meerutAQI');
                    pill.textContent = label + " (" + pm + ")";
                    pill.style.backgroundColor = bg;
                }}
            }} catch(e) {{}}
        }}
        fetchMeerutWeatherAQI();
        setInterval(fetchMeerutWeatherAQI, 300000);

        const tickerBox = document.getElementById('tickerBox');
        const tickerWrapper = document.getElementById('tickerWrapper');
        let pos = tickerBox.offsetWidth;
        const velocity = {marquee_velocity};
        let lastTime = performance.now();

        function moveTicker(now) {{
            const dt = (now - lastTime) / 1000;
            lastTime = now;
            pos -= velocity * dt;
            if (pos < -tickerWrapper.offsetWidth) {{
                pos = tickerBox.offsetWidth;
            }}
            tickerWrapper.style.transform = 'translateX(' + pos + 'px)';
            requestAnimationFrame(moveTicker);
        }}
        requestAnimationFrame(moveTicker);
    </script>
</body>
</html>
"""
        # Height is locked to 98vh so the entire app renders cleanly without window-level scrollbars
        components.html(full_html, height=730, scrolling=False)

    render_live_screen()
