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
    page_icon="🏅",
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
            key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", x)],
        )
    except Exception:
        files = []

    if not files:
        return ""

    cards = [
        """
        <div class="gallery-divider">
            EVENT PHOTO GALLERY • TRACK & FIELD HIGHLIGHTS
        </div>
    """
    ]
    for f in files:
        p = os.path.join(gallery_path, f)
        b64 = get_base64_image(p)
        if not b64:
            continue
        ev_label = os.path.splitext(f)[0].upper()
        cards.append(
            f"""
            <div class="gallery-photo-card">
                <div class="gallery-tag-pill">{ev_label}</div>
                <img src="data:image/jpeg;base64,{b64}" class="gallery-img" alt="{ev_label}" loading="lazy"/>
            </div>
        """
        )
    return "".join(cards)


# ----------------- Robust YouTube ID Extractor -----------------
def clean_yt_id(val):
    if not val:
        return ""
    val = str(val).strip()
    match = re.search(
        r"(?:v=|\/embed\/|\/live\/|youtu\.be\/|\/v\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})",
        val,
    )
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
        return {
            "incharge1": "apspass2026",
            "incharge2": "apspass2026",
            ADMIN_USER: ADMIN_PASSWORD,
        }


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
        border-radius: 14px !important;
        padding: 26px 22px !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75) !important;
        border: 1.5px solid rgba(255, 215, 0, 0.4) !important;
    }}
    .landing-title {{
        text-align: center;
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .motto-banner {{
        background: #ffd700;
        color: #001833;
        font-size: 12px;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 3px;
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
            <div class="landing-title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div style="color:#ffd700; font-weight:700; font-size:16px; margin-top: 5px;">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="motto-banner">RUN WITH COURAGE • RISE WITH PRIDE</div>
            <div style="color:#93c5fd; font-size:13.5px; font-weight:700; margin-bottom:15px;">Official Live Results Portal (28 Oct – 5 Nov 2026)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    role = st.radio(
        "Select Portal Mode:",
        ["Public Live Display", "In-Charge Console"],
    )

    if role == "Public Live Display":
        if st.button("Launch Dashboard Screen", type="primary", use_container_width=True):
            st.session_state.view_mode = "display"
            st.query_params["view"] = "display"
            st.rerun()
    else:
        with st.form("login_form"):
            st.markdown("##### In-Charge Authentication")
            u_name = st.text_input("Username").strip()
            p_word = st.text_input("Password", type="password").strip()
            submitted = st.form_submit_button(
                "Sign In", type="primary", use_container_width=True
            )
            if submitted:
                valid_creds = fetch_credentials()
                if u_name in valid_creds and valid_creds[u_name] == p_word:
                    st.session_state.view_mode = "admin"
                    st.session_state.logged_user = u_name
                    st.query_params["view"] = "admin"
                    st.success(f"Signed in as {u_name}")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# =========================================================================
# 2. SCORE IN-CHARGE PORTAL
# =========================================================================
elif st.session_state.view_mode == "admin":
    top_c1, top_c2, top_c3 = st.columns([5, 2.5, 2.5])
    top_c1.title("Control Desk")
    if top_c2.button("Open Live Screen", use_container_width=True):
        st.session_state.view_mode = "display"
        st.query_params["view"] = "display"
        st.rerun()
    if top_c3.button("Sign Out", use_container_width=True):
        st.session_state.view_mode = "login"
        st.session_state.pop("logged_user", None)
        st.query_params.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("Media & Photo Management")
    st.caption("Settings saved here are stored on the server and update all public monitors immediately.")

    current_cfg = load_video_config()

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("#### 1. News Highlights Video")
        input_news_link = st.text_input(
            "YouTube Video Link or ID:",
            value=current_cfg.get("yt_news_id", "xz-pqId7ym8"),
            help="Accepts any YouTube URL or 11-digit ID",
        )
        parsed_news = clean_yt_id(input_news_link)
        st.info(f"Active Highlights ID: **`{parsed_news}`**")

        st.markdown("#### 2. Trackside Live Broadcast")
        input_live_link = st.text_input(
            "Live Stream Link or Video ID:",
            value=current_cfg.get("yt_live_channel_id", ""),
            placeholder="e.g. YouTube Live video ID",
        )
        parsed_live = clean_yt_id(input_live_link)
        if parsed_live:
            st.info(f"Active Live Stream ID: **`{parsed_live}`**")

    with col_v2:
        st.markdown("#### 3. Live Broadcast Switch")
        live_switch = st.toggle(
            "Enable Live Broadcast Stream",
            value=current_cfg.get("is_live_active", False),
        )
        if live_switch:
            st.success("LIVE STREAM ACTIVE: Display board will show trackside live feed.")
        else:
            st.warning("LIVE STREAM OFF: Display board shows 'Coverage on Standby'.")

        st.markdown("#### 4. Event Photos Folder Path")
        input_gallery_path = st.text_input(
            "Folder path containing EV-1, EV-1-1 images:",
            value=current_cfg.get("gallery_dir", "gallery"),
            help="Local folder (e.g. gallery or G:\\My Drive\\Athletics_Photos)",
        )
        if os.path.exists(input_gallery_path):
            img_count = len(
                [
                    f
                    for f in os.listdir(input_gallery_path)
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                ]
            )
            st.caption(f"Folder connected: {img_count} event photo(s) available.")
        else:
            st.caption("Folder path not found yet. Defaulting to 'gallery'.")

        st.write("")
        if st.button("Save Configuration", type="primary", use_container_width=True):
            save_video_config(
                parsed_news, parsed_live, live_switch, input_gallery_path
            )
            st.success("Settings saved successfully!")
            st.rerun()

    st.markdown("---")
    st.markdown(
        f"**[Open Master Google Sheet for Results Entry](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)**"
    )
    res_df, _, _ = fetch_live_data()
    if not res_df.empty:
        st.dataframe(res_df, use_container_width=True)

# =========================================================================
# 3. LIVE DISPLAY (RESPONSIVE AUTO-OPTIMIZED VIEWPORT)
# =========================================================================
elif st.session_state.view_mode == "display":
    with st.sidebar:
        if st.button("Switch to In-Charge Login"):
            st.session_state.view_mode = "login"
            st.query_params["view"] = "login"
            st.rerun()

        st.markdown("### Display Controls")
        scroll_speed = st.slider(
            "Auto-Scroll Speed (seconds)", min_value=0, max_value=240, value=90, step=5
        )
        marquee_velocity = st.slider(
            "Ticker Speed (px/s)", min_value=25, max_value=250, value=85, step=5
        )
        marquee_font_size = st.slider(
            "Ticker Font (px)", min_value=12, max_value=24, value=15, step=1
        )
        marquee_bg_color = st.color_picker("Ticker Background", "#001833")
        marquee_text_color = st.color_picker("Ticker Text Color", "#FFE600")

    st.markdown(
        """
        <style>
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
            width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    @st.fragment(run_every=180)
    def render_live_screen():
        df, pp_df, ann_df = fetch_live_data()

        if not df.empty and "event_date" in df.columns:
            df["parsed_date"] = pd.to_datetime(
                df["event_date"], format="mixed", dayfirst=True, errors="coerce"
            )
            df = df.sort_values(by="parsed_date", ascending=False).reset_index(drop=True)
            df["display_date"] = df["parsed_date"].dt.strftime("%d-%m-%Y")
            df["display_date"] = df["display_date"].fillna(df["event_date"])
        elif not df.empty:
            df["display_date"] = ""

        pp_dict = {}
        if not pp_df.empty and "house" in pp_df.columns and "pp_points" in pp_df.columns:
            for _, r in pp_df.iterrows():
                pp_dict[normalize_house(r["house"])] = int(
                    r["pp_points"] if pd.notna(r["pp_points"]) else 0
                )

        tally = {
            h: {
                "Gold": 0,
                "Silver": 0,
                "Bronze": 0,
                "TotalMedals": 0,
                "PP": int(pp_dict.get(h, 0)),
                "EarnedPts": 0,
                "TP": 0,
            }
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
            tally[h]["TotalMedals"] = (
                tally[h]["Gold"] + tally[h]["Silver"] + tally[h]["Bronze"]
            )
            tally[h]["TP"] = tally[h]["PP"] + tally[h]["EarnedPts"]

        sorted_houses = sorted(
            houses,
            key=lambda h: (
                tally[h]["TP"],
                tally[h]["Gold"],
                tally[h]["Silver"],
                tally[h]["Bronze"],
                tally[h]["TotalMedals"],
            ),
            reverse=True,
        )

        tally_html = ""
        for rank, h in enumerate(sorted_houses, start=1):
            rank_suffix = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}.get(
                rank, f"#{rank}"
            )
            rank_badge_class = "rank-lead" if rank == 1 else "rank-sub"
            tally_html += f"""
            <div class="house-tally-row">
                <div class="{rank_badge_class}">{rank_suffix}</div>
                <div><span class="house-box-label house-{h}">{h}</span></div>
                <div class="tally-num gold-text">{tally[h]['Gold']}</div>
                <div class="tally-num silver-text">{tally[h]['Silver']}</div>
                <div class="tally-num bronze-text">{tally[h]['Bronze']}</div>
                <div class="tally-num total-col">{tally[h]['TotalMedals']}</div>
                <div class="tally-num pp-col">{tally[h]['PP']}</div>
                <div class="tally-num tp-col">{tally[h]['TP']}</div>
            </div>
            """

        marquee_msg = "Annual Athletics Championship 2026 is underway. Results and standings updated live from official records."
        if (
            not ann_df.empty
            and "type" in ann_df.columns
            and "content" in ann_df.columns
        ):
            m_row = ann_df[ann_df["type"].str.lower() == "marquee"]
            if not m_row.empty:
                marquee_msg = str(m_row.iloc[0]["content"])

        cards_html = ""
        if df.empty:
            cards_html = """
            <div style="text-align:center; padding: 40px 15px; color:#1e293b; font-weight:700; font-size:16px;">
                Events in progress. Results will appear as official score sheets are submitted.
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
                        <span class="doc-date-badge">{r.get('display_date', '')}</span>
                    </div>
                    <div class="table-responsive-wrapper">
                        <table class="doc-sub-table">
                            <thead>
                                <tr>
                                    <th>Place</th>
                                    <th>Athlete</th>
                                    <th>Class</th>
                                    <th>Adm No</th>
                                    <th>Record</th>
                                    <th>House</th>
                                    <th>Pts</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="row-gold">
                                    <td class="place-badge gold-bg">1st</td>
                                    <td class="daylight-name">{format_stacked(r.get('gold_student_name', ''))}</td>
                                    <td class="daylight-bold-class">{r.get('gold_class_sec', '-')}</td>
                                    <td class="daylight-bold-adm">{format_stacked(r.get('gold_adm_no', ''))}</td>
                                    <td class="daylight-bold-perf">{r.get('gold_perf_(time_ht_dis)', '-')}</td>
                                    <td><span class="mini-house-badge house-{gh}">{gh}</span></td>
                                    <td class="bold-pts">+{r.get('gold_points', 5)}</td>
                                </tr>
                                <tr class="row-silver">
                                    <td class="place-badge silver-bg">2nd</td>
                                    <td class="daylight-name">{format_stacked(r.get('silver_student_name', ''))}</td>
                                    <td class="daylight-bold-class">{r.get('silver_class_sec', '-')}</td>
                                    <td class="daylight-bold-adm">{format_stacked(r.get('silver_adm_no', ''))}</td>
                                    <td class="daylight-bold-perf">{r.get('silver_perf_(time_ht_dis)', '-')}</td>
                                    <td><span class="mini-house-badge house-{sh}">{sh}</span></td>
                                    <td class="bold-pts">+{r.get('silver_points', 4)}</td>
                                </tr>
                                <tr class="row-bronze">
                                    <td class="place-badge bronze-bg">3rd</td>
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

        active_cfg = load_video_config()
        news_vid = clean_yt_id(active_cfg.get("yt_news_id", "xz-pqId7ym8"))
        live_vid = clean_yt_id(active_cfg.get("yt_live_channel_id", ""))
        is_live_on = "true" if active_cfg.get("is_live_active", False) else "false"

        gallery_html = load_gallery_images(active_cfg.get("gallery_dir", "gallery"))
        combined_right_content = cards_html + gallery_html

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
    
    /* DESKTOP 100VH VIEWPORT FIT */
    html, body {{
        background-color: #cbd5e1;
        width: 100vw;
        height: 100vh;
        max-height: 100vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        padding: 2px 4px 6px 4px;
    }}

    /* ---------------- HEADER ---------------- */
    .top-banner {{
        background: linear-gradient(90deg, #001730 0%, #002b54 50%, #001730 100%);
        color: #ffffff;
        border-radius: 6px 6px 0 0;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 3.5px solid #ffcc00;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
        flex-shrink: 0;
        gap: 12px;
    }}

    .header-left-wing {{
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        min-width: 155px;
        gap: 4px;
    }}
    .clock-display {{
        display: flex;
        align-items: center;
        gap: 2px;
        background: #000000;
        border: 1.5px solid #ffd700;
        border-radius: 4px;
        padding: 2px 6px;
    }}
    .clock-digit {{
        background: #18181b;
        color: #ffd700;
        font-family: monospace;
        font-size: 16px;
        font-weight: 700;
        padding: 1px 3px;
        border-radius: 2px;
    }}
    .clock-sep {{ color: #ffffff; font-weight: 700; font-size: 15px; }}
    .date-badge-pill {{
        background: rgba(2, 43, 84, 0.95);
        color: #ffd700;
        border: 1px solid #38bdf8;
        border-radius: 3px;
        padding: 2px 8px;
        font-size: 11.5px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}

    .banner-center {{
        text-align: center;
        flex-grow: 1;
        padding: 0 6px;
    }}
    .top-banner .school-name {{
        font-size: clamp(15px, 2.1vw, 22px);
        font-weight: 900;
        color: #ffd700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    .top-banner .title {{
        font-size: clamp(22px, 3.2vw, 34px);
        font-weight: 900;
        text-transform: uppercase;
        color: #ffffff;
        line-height: 1.15;
        letter-spacing: 1px;
        margin-top: 2px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    }}
    .motto-pill {{
        display: inline-block;
        background: linear-gradient(90deg, #d97706, #f59e0b);
        color: #001833;
        font-size: clamp(11.5px, 1.3vw, 14px);
        font-weight: 900;
        letter-spacing: 1.5px;
        padding: 2px 14px;
        border-radius: 12px;
        margin-top: 3px;
        text-transform: uppercase;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
    }}

    .header-right-wing {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        min-width: 155px;
        gap: 4px;
    }}
    .weather-aqi-card {{
        background: rgba(0, 0, 0, 0.45);
        border: 1.5px solid #38bdf8;
        border-radius: 4px;
        padding: 3px 7px;
        text-align: right;
        font-size: 11.5px;
        font-weight: 800;
        color: #fff;
    }}
    .aqi-pill {{
        background: #ea580c;
        padding: 1px 5px;
        border-radius: 3px;
        font-weight: 900;
        font-size: 11px;
    }}
    .date-bracket-top {{
        font-size: 11.5px;
        font-weight: 800;
        color: #bfdbfe;
    }}

    /* ---------------- TICKER ---------------- */
    .top-ticker {{
        width: 100%;
        background-color: {marquee_bg_color};
        color: {marquee_text_color};
        padding: 4px 0;
        font-size: {marquee_font_size}px;
        font-weight: 800;
        overflow: hidden;
        white-space: nowrap;
        border-bottom: 2px solid #f59e0b;
        border-radius: 0 0 4px 4px;
        margin-bottom: 4px;
        flex-shrink: 0;
    }}
    #tickerWrapper {{ display: inline-block; white-space: nowrap; }}

    /* ---------------- MAIN GRID (AUTO-EXPANDING HEIGHT) ---------------- */
    .dashboard-grid {{
        display: grid;
        grid-template-columns: 4.1fr 5.9fr;
        gap: 6px;
        width: 100%;
        flex: 1 1 0;
        min-height: 0;
    }}

    .main-panel {{
        background: #ffffff;
        border: 1.5px solid #002244;
        border-radius: 6px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        height: 100%;
        min-height: 0;
    }}
    .panel-top-header {{
        background: #002244;
        color: #ffffff;
        padding: 6px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0;
    }}
    .panel-top-title {{
        font-size: 13.5px;
        font-weight: 800;
        text-transform: uppercase;
        color: #ffd700;
        letter-spacing: 0.5px;
    }}
    .panel-top-sub {{
        font-size: 11px;
        color: #bfdbfe;
        font-weight: 600;
    }}

    /* ---------------- VIDEO SECTION ---------------- */
    .video-tab-bar {{
        background: #011326;
        display: flex;
        border-bottom: 1.5px solid #0284c7;
        flex-shrink: 0;
    }}
    .video-tab-btn {{
        flex: 1;
        padding: 5px 4px;
        background: #011326;
        color: #94a3b8;
        border: none;
        cursor: pointer;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }}
    .video-tab-btn.active {{
        background: #002b54;
        color: #ffd700;
        border-bottom: 2px solid #ffd700;
    }}
    .live-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #ef4444;
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
        padding-top: 48%;
        background: #000000;
        overflow: hidden;
        flex-shrink: 0;
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
        padding: 10px;
        text-align: center;
        color: #ffffff;
    }}
    .no-live-title {{ font-size: 12.5px; font-weight: 800; color: #f59e0b; text-transform: uppercase; margin-bottom: 3px; }}
    .no-live-sub {{ font-size: 10.5px; color: #94a3b8; }}

    /* ---------------- MEDAL TALLY (STRETCHES SEAMLESSLY) ---------------- */
    .tally-panel-wrapper {{
        flex: 1 1 0;
        display: flex;
        flex-direction: column;
        min-height: 0;
        background: #f8fafc;
        border-top: 1.5px solid #cbd5e1;
        overflow: hidden;
    }}
    .tally-header-banner {{
        background: #0f172a;
        color: #e2e8f0;
        padding: 4px 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.5px;
        flex-shrink: 0;
    }}
    .tally-container {{
        padding: 3px 4px;
        overflow: hidden;
        flex: 1 1 0;
        display: flex;
        flex-direction: column;
        justify-content: space-around;
    }}
    .medal-icon-row {{
        display: grid;
        grid-template-columns: 0.9fr 2.2fr 0.8fr 0.8fr 0.8fr 0.9fr 0.9fr 1.1fr;
        text-align: center;
        margin-bottom: 2px;
        font-size: 11px;
        font-weight: 800;
        color: #334155;
        border-bottom: 1.5px solid #cbd5e1;
        padding-bottom: 2px;
    }}
    .house-tally-row {{
        display: grid;
        grid-template-columns: 0.9fr 2.2fr 0.8fr 0.8fr 0.8fr 0.9fr 0.9fr 1.1fr;
        align-items: center;
        text-align: center;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 3px 2px;
        margin-bottom: 2px;
    }}
    .rank-lead {{
        font-weight: 900;
        color: #d97706;
        font-size: 11.5px;
        background: #fef3c7;
        padding: 1px 3px;
        border-radius: 3px;
        display: inline-block;
    }}
    .rank-sub {{
        font-weight: 700;
        color: #475569;
        font-size: 11px;
    }}
    .house-box-label {{
        display: inline-block;
        padding: 2px 2px;
        border-radius: 3px;
        font-size: 10.5px;
        font-weight: 800;
        width: 95%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .house-MANEKSHAW {{ background: #dc2626 !important; color: #ffffff !important; }}
    .house-CARIAPPA {{ background: #16a34a !important; color: #ffffff !important; }}
    .house-SUNDARJI {{ background: #2563eb !important; color: #ffffff !important; }}
    .house-VAIDYA {{ background: #f59e0b !important; color: #000000 !important; }}

    .tally-num {{ font-size: 13px; font-weight: 800; }}
    .gold-text {{ color: #b45309; }}
    .silver-text {{ color: #475569; }}
    .bronze-text {{ color: #c2410c; }}
    .total-col {{ color: #0369a1; }}
    .pp-col {{ color: #64748b; font-size: 11.5px; }}
    .tp-col {{
        background: #002244;
        color: #ffdd00 !important;
        border-radius: 3px;
        padding: 2px 4px;
        display: inline-block;
    }}

    /* ---------------- RESULTS SCROLLER (STRETCHES TO BOTTOM & AUTO-SCROLL SAFE) ---------------- */
    .winner-scroll-box {{
        flex: 1 1 0;
        min-height: 250px;
        max-height: 100%;
        overflow-y: scroll !important;
        overflow-x: hidden;
        position: relative;
        background: #f1f5f9;
        padding: 6px;
        scroll-behavior: auto !important;
    }}
    .winner-scroll-box::-webkit-scrollbar {{
        width: 6px;
    }}
    .winner-scroll-box::-webkit-scrollbar-thumb {{
        background: #002244;
        border-radius: 3px;
    }}

    .event-doc-card {{
        background: #ffffff;
        border: 1.5px solid #94a3b8;
        border-radius: 5px;
        margin-bottom: 8px;
        overflow: hidden;
    }}
    .doc-card-header {{
        background: #002244;
        color: #ffffff;
        padding: 5px 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 800;
    }}
    .doc-badge-event {{ font-size: 14.5px; color: #ffd700; }}
    .doc-badge-cat {{ background: #ffffff; color: #002244; padding: 2px 6px; border-radius: 3px; font-size: 11.5px; font-weight: 800; }}
    .doc-date-badge {{ font-size: 11.5px; color: #cbd5e1; }}

    .table-responsive-wrapper {{
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }}
    .doc-sub-table {{
        width: 100%;
        min-width: 440px;
        border-collapse: collapse;
        text-align: center;
        font-size: 12.5px;
    }}
    .doc-sub-table th {{
        background: #e2e8f0;
        color: #0f172a;
        padding: 4px 2px;
        font-weight: 800;
    }}
    .doc-sub-table td {{
        padding: 4px 2px;
        border-bottom: 1px solid #e2e8f0;
    }}
    
    .daylight-name {{ font-weight: 800; color: #000; text-align: left; padding-left: 6px; font-size: 13.5px; }}
    .daylight-bold-class {{ font-weight: 700; color: #000; font-size: 12px; }}
    .daylight-bold-adm {{ font-family: monospace; font-weight: 700; color: #1e293b; font-size: 12px; }}
    .daylight-bold-perf {{ font-weight: 800; color: #b91c1c; font-family: monospace; font-size: 13px; }}
    .bold-pts {{ font-weight: 800; color: #15803d; font-size: 12.5px; }}
    .place-badge {{ font-weight: 800; border-radius: 2px; font-size: 11.5px; }}
    .gold-bg {{ background: #fef08a; color: #854d0e; }}
    .silver-bg {{ background: #f1f5f9; color: #334155; }}
    .bronze-bg {{ background: #fed7aa; color: #9a3412; }}
    .mini-house-badge {{ display: inline-block; padding: 2px 4px; border-radius: 3px; font-size: 10.5px; font-weight: 800; }}

    /* GALLERY */
    .gallery-divider {{
        background: linear-gradient(90deg, #d97706, #002244);
        color: #ffd700;
        font-size: 12px;
        font-weight: 800;
        text-align: center;
        padding: 6px;
        margin: 10px 0 6px 0;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }}
    .gallery-photo-card {{
        position: relative;
        background: #001226;
        border: 1.5px solid #ffcc00;
        border-radius: 6px;
        margin-bottom: 8px;
        overflow: hidden;
    }}
    .gallery-tag-pill {{
        position: absolute;
        top: 6px;
        left: 6px;
        background: rgba(0, 24, 51, 0.9);
        color: #ffd700;
        font-size: 11px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 3px;
        border: 1px solid #ffd700;
        z-index: 2;
    }}
    .gallery-img {{
        width: 100%;
        height: 240px;
        object-fit: cover;
        object-position: center;
        display: block;
    }}

    /* ---------------- FOOTER (GROUNDED AT THE VERY BOTTOM) ---------------- */
    .visitor-footer-bar {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 3px 8px;
        width: 100%;
        background: #cbd5e1;
        flex-shrink: 0;
    }}
    .visitor-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 24, 51, 0.95);
        border: 1px solid #ffd700;
        border-radius: 16px;
        padding: 2px 14px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    }}
    .live-dot-green {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #22c55e;
        display: inline-block;
        box-shadow: 0 0 6px #22c55e;
        animation: liveBlink 1.4s infinite;
    }}
    .visitor-label {{
        color: #93c5fd;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    .visitor-val {{
        color: #22c55e;
        font-family: monospace;
        font-size: 12.5px;
        font-weight: 800;
    }}
    .visitor-odometer {{
        background: #000000;
        color: #ffd700;
        font-family: "Courier New", Courier, monospace;
        font-size: 12.5px;
        font-weight: 800;
        letter-spacing: 1.5px;
        padding: 1px 5px;
        border-radius: 3px;
        border: 1px solid #1e3a5f;
    }}

    /* ---------------- ROBUST MOBILE OVERRIDES (<= 860px) ---------------- */
    @media (max-width: 860px) {{
        html, body {{
            height: auto !important;
            max-height: none !important;
            overflow-y: auto !important;
            padding: 2px 3px 15px 3px !important;
        }}
        .top-banner {{
            flex-direction: column !important;
            text-align: center !important;
            gap: 6px !important;
            padding: 8px 6px !important;
        }}
        .header-left-wing, .header-right-wing {{
            width: 100% !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: 0 !important;
            flex-direction: row !important;
            gap: 10px !important;
        }}
        .dashboard-grid {{
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
            gap: 10px !important;
            height: auto !important;
            flex: none !important;
        }}
        .main-panel {{
            width: 100% !important;
            height: auto !important;
            min-height: auto !important;
            display: block !important;
        }}
        .sub-video-stage {{
            width: 100% !important;
            padding-top: 56.25% !important;
        }}
        .tally-panel-wrapper {{
            display: block !important;
            width: 100% !important;
            height: auto !important;
            overflow: visible !important;
        }}
        .tally-container {{
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }}
        .winner-scroll-box {{
            height: 480px !important;
            width: 100% !important;
            flex: none !important;
        }}
    }}
</style>
</head>
<body>

    <!-- THREE-COLUMN HEADER -->
    <div class="top-banner">
        <div class="header-left-wing">
            <div class="clock-display">
                <span class="clock-digit" id="flipH">00</span>
                <span class="clock-sep">:</span>
                <span class="clock-digit" id="flipM">00</span>
                <span class="clock-sep">:</span>
                <span class="clock-digit" id="flipS">00</span>
            </div>
            <div class="date-badge-pill" id="liveDate">29-OCT-2026</div>
        </div>

        <div class="banner-center">
            <div class="school-name">ARMY PUBLIC SCHOOL, MEERUT CANTT</div>
            <div class="title">ANNUAL ATHLETICS CHAMPIONSHIP 2026</div>
            <div><span class="motto-pill">RUN WITH COURAGE • RISE WITH PRIDE</span></div>
        </div>

        <div class="header-right-wing">
            <div class="weather-aqi-card">
                <span id="meerutTemp">--°C</span> | Hum: <span id="meerutHumidity">--%</span> | AQI: <span class="aqi-pill" id="meerutAQI">--</span>
            </div>
            <div class="date-bracket-top">28 Oct – 5 Nov 2026</div>
        </div>
    </div>

    <!-- TICKER -->
    <div class="top-ticker" id="tickerBox">
        <div id="tickerWrapper">
            <b>UPDATES:</b> {marquee_msg} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Official standings updated automatically.
        </div>
    </div>

    <!-- MAIN BODY GRID (STRETCHES SEAMLESSLY TO FOOTER) -->
    <div class="dashboard-grid">
        <!-- LEFT: VIDEO (TOP) + FULLY VISIBLE MEDAL TALLY (BOTTOM) -->
        <div class="main-panel">
            <div class="panel-top-header">
                <span class="panel-top-title">Official Media Broadcast</span>
                <span class="panel-top-sub">Track & Ground Coverage</span>
            </div>

            <div class="video-tab-bar">
                <button class="video-tab-btn active" id="tabHighlightsBtn" onclick="switchVideoMode('news')">
                    Highlights & Bulletin
                </button>
                <button class="video-tab-btn" id="tabLiveBtn" onclick="switchVideoMode('live')">
                    <span class="live-dot"></span> Live Broadcast
                </button>
            </div>

            <div class="sub-video-stage">
                <iframe id="newsFrame" class="sub-video-frame"
                    src="https://www.youtube-nocookie.com/embed/{news_vid}?autoplay=0&mute=1&controls=1&modestbranding=1&rel=0" 
                    title="Highlights" 
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
                    <div class="no-live-title">Live Broadcast on Standby</div>
                    <div class="no-live-sub">Live trackside cameras connect during ongoing event calls. Please view highlights above.</div>
                </div>
            </div>

            <!-- OVERALL HOUSE STANDINGS -->
            <div class="tally-panel-wrapper">
                <div class="tally-header-banner">
                    <span>OVERALL HOUSE STANDINGS</span>
                    <span style="color:#ffd700;">Ranked by Total Points (TP)</span>
                </div>
                <div class="tally-container">
                    <div class="medal-icon-row">
                        <div>Pos</div>
                        <div>House</div>
                        <div>Gold</div>
                        <div>Silver</div>
                        <div>Bronze</div>
                        <div>Total</div>
                        <div>PP</div>
                        <div style="color:#d97706;">TP</div>
                    </div>
                    {tally_html}
                </div>
            </div>
        </div>

        <!-- RIGHT: EVENT RESULTS & GALLERY (STRETCHED TO MATCH LEFT PANEL) -->
        <div class="main-panel">
            <div class="panel-top-header">
                <span class="panel-top-title">Event Results & Gallery</span>
                <span class="panel-top-sub">Scroll or inspect verified finishes</span>
            </div>
            <div class="winner-scroll-box" id="resultsScrollBox">
                {combined_right_content}
            </div>
        </div>
    </div>

    <!-- GROUNDED VISITOR FOOTER -->
    <div class="visitor-footer-bar">
        <div class="visitor-badge">
            <span class="live-dot-green"></span>
            <span class="visitor-label">Active Now:</span>
            <span class="visitor-val">{live_visitors}</span>
            <span style="color:#64748b; margin: 0 4px;">|</span>
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

        function updateClock() {{
            const now = new Date();
            document.getElementById('flipH').textContent = String(now.getHours()).padStart(2, '0');
            document.getElementById('flipM').textContent = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('flipS').textContent = String(now.getSeconds()).padStart(2, '0');
            const opt = {{ day: '2-digit', month: 'short', year: 'numeric' }};
            document.getElementById('liveDate').textContent = now.toLocaleDateString('en-GB', opt).replace(/ /g, '-').toUpperCase();
        }}
        setInterval(updateClock, 1000);
        updateClock();

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
                    let label = "Mod";
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

        // Sub-pixel Precision Auto-Scroll Engine
        const scrollBox = document.getElementById('resultsScrollBox');
        let isUserInteracting = false;
        let isResetting = false;
        let resumeTimer = null;
        let scrollPos = 0;
        let lastFrameTime = performance.now();

        if (scrollBox) {{
            scrollBox.addEventListener('mouseenter', () => {{ isUserInteracting = true; }});
            scrollBox.addEventListener('mouseleave', () => {{ 
                isUserInteracting = false; 
                scrollPos = scrollBox.scrollTop;
            }});
            scrollBox.addEventListener('touchstart', () => {{ isUserInteracting = true; }}, {{ passive: true }});
            scrollBox.addEventListener('touchend', () => {{
                clearTimeout(resumeTimer);
                resumeTimer = setTimeout(() => {{ 
                    isUserInteracting = false; 
                    scrollPos = scrollBox.scrollTop;
                }}, 2000);
            }});
            scrollBox.addEventListener('wheel', () => {{
                isUserInteracting = true;
                scrollPos = scrollBox.scrollTop;
                clearTimeout(resumeTimer);
                resumeTimer = setTimeout(() => {{ 
                    isUserInteracting = false; 
                    scrollPos = scrollBox.scrollTop;
                }}, 2500);
            }}, {{ passive: true }});

            function stepScroll(now) {{
                const dt = (now - lastFrameTime) / 1000;
                lastFrameTime = now;

                if (!isUserInteracting && !isResetting && scrollBox) {{
                    const maxScroll = scrollBox.scrollHeight - scrollBox.clientHeight;

                    if (maxScroll > 10) {{
                        scrollPos += 35 * dt;

                        if (scrollPos >= maxScroll - 2) {{
                            isResetting = true;
                            scrollBox.scrollTop = maxScroll;
                            setTimeout(() => {{
                                scrollPos = 0;
                                scrollBox.scrollTop = 0;
                                setTimeout(() => {{
                                    lastFrameTime = performance.now();
                                    isResetting = false;
                                }}, 800);
                            }}, 1800);
                        }} else {{
                            scrollBox.scrollTop = scrollPos;
                        }}
                    }}
                }}
                requestAnimationFrame(stepScroll);
            }}
            requestAnimationFrame(stepScroll);
        }}

        const tickerBox = document.getElementById('tickerBox');
        const tickerWrapper = document.getElementById('tickerWrapper');
        if (tickerBox && tickerWrapper) {{
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
        }}
    </script>
</body>
</html>
"""
        components.html(full_html, height=750, scrolling=False)

    render_live_screen()
