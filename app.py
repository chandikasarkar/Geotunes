import streamlit as st
import requests
import pickle
import numpy as np
import pandas as pd
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import base64

# -------------------------------
# BACKGROUND IMAGE
# -------------------------------
def set_background_image(image_file: str, offset_y: str = "0px"):
    """
    Sets the background image with a vertical offset so that
    the logo inside the image can be visually aligned at the top.
    offset_y is like "0px", "-120px", "50px", etc.
    """
    try:
        with open(image_file, "rb") as img:
            encoded = base64.b64encode(img.read()).decode()

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-color: #fdf0d8;
                background-image: url("data:image/png;base64,{encoded}");
                background-repeat: no-repeat;
                background-size: cover;
                background-position: center {offset_y};
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"Background image error: {e}")

# -------------------------------
# LOAD MODEL
# -------------------------------
vibe_model = None
encoder = None
emoji_map = {}

try:
    with open('vibe_knn_model.pkl', "rb") as f:
        bundle = pickle.load(f)
        vibe_model = bundle.get("model", None)
        encoder = bundle.get("encoder", None)

    emoji_map = {
        "backwater": "Backwater ",
        "beach": "Beach ",
        "city": "City Tour ",
        "coastal": "Coastal Breeze ",
        "coastal-city": "Coastal City ",
        "cultural": "Cultural Heritage ",
        "desert": "Desert ",
        "forest": "Forest ",
        "heritage": "Heritage Site ",
        "hill-town": "Hill Town ",
        "industrial": "Industrial Zone ",
        "mountain": "Mountain ",
        "pilgrim-town": "Pilgrim Town ",
        "rural": "Rural Countryside ",
        "spiritual": "Spiritual Place ",
        "temple-town": "Temple Town ",
        "urban": "Urban City ",
    }
except Exception as e:
    print(f"Failed to load vibe_knn_model.pkl: {e}")
    vibe_model = None
    encoder = None
    emoji_map = {}

# -------------------------------
# VIBE PREDICTION
# -------------------------------
def predict_vibe(lat, lon):
    if vibe_model is None or encoder is None:
        st.error("KNN model or encoder could not be loaded.")
        return None
    try:
        coords = np.radians([[float(lat), float(lon)]])
        pred_numeric = vibe_model.predict(coords)[0]
        label_name = encoder.inverse_transform([pred_numeric])[0]
        vibe_display = emoji_map.get(label_name.lower(), label_name)
        return {"label": label_name, "display": vibe_display}
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# -------------------------------
# SPOTIFY
# -------------------------------
sp = None
try:
    sp = Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id="1d46738e78ad4e45b79208be4da1a018",
            client_secret="0639372d03e44e098f7f8f1a4249bbd7",
        )
    )
except Exception as e:
    print(f"Spotify init error: {e}")
    sp = None

def get_spotify_playlists(vibe_label, language=None, limit=5):
    playlists = []
    if sp is None:
        st.error("Spotify client not initialized.")
        return playlists

    query_pieces = []
    if vibe_label:
        query_pieces.append(vibe_label)
    if language and language.lower() != "all":
        query_pieces.append(language)
    query_pieces.append("music")
    query = " ".join(query_pieces).strip()

    try:
        results = sp.search(q=query, type="playlist", limit=limit)
        items = results.get("playlists", {}).get("items", []) if results else []

        for playlist in items:
            if not playlist:
                continue
            name = playlist.get("name", "No Name")
            url = playlist.get("external_urls", {}).get("spotify", "")
            image = None
            if playlist.get("images") and len(playlist["images"]) > 0:
                image = playlist["images"][0]["url"]

            playlists.append(
                {
                    "name": name,
                    "url": url,
                    "image": image,
                    "source_query": query,
                }
            )
    except Exception as e:
        st.error(f"Spotify API error for query '{query}': {e}")

    return playlists

# -------------------------------
# LOCATION
# -------------------------------
def get_current_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        lat, lon = data["loc"].split(",")
        return {
            "city": data.get("city", ""),
            "state": data.get("region", ""),
            "country": data.get("country", ""),
            "lat": lat,
            "lon": lon,
        }
    except Exception:
        return None

# -------------------------------
# LOGIN CHECK
# -------------------------------
def login(username, password):
    return username == "admin" and password == "123"

# -------------------------------
# CUSTOM CSS
# -------------------------------
def apply_custom_css(logged_in):
    if not logged_in:
        # LOGIN PAGE STYLES
        st.markdown(
            """
            <style>
            /* Disable scrolling on login page */
            .stApp {
                overflow: hidden;
            }

            /* Main login block: full width, left aligned, margin top */
            .main-block {
                width: 90%;
                max-width: 600px;
                display: flex;
                flex-direction: column;
                align-items: flex-start !important;
                justify-content: flex-start;
                margin-top: 150px;  /* controls gap below the logo in bg */
                margin-left: 0px !important;
            }

            /* Title left aligned, shifted more to the left */
            .login-title {
                width: 100%;
                text-align: left !important;
                font-size: 2.8rem;
                font-weight: 800;
                color: #222222;
                margin: 0 0 20px 0;
                white-space: nowrap;
                margin-left: -140px !important;  /* shift title further left */
            }

            /* Login card */
            .login-box {
                background: rgba(255, 255, 255, 0.92);
                padding: 24px 26px;
                border-radius: 16px;
                width: 100%;
                box-shadow: 0px 4px 18px rgba(0, 0, 0, 0.18);
                text-align: left;
                font-family: "Georgia", serif;
            }

            .stTextInput>div>div>input {
                border-radius: 10px !important;
                background: #ffffff !important;
            }

            .stButton>button {
                background: #d88a3d !important;
                color: #ffffff !important;
                font-weight: 700;
                width: 120px;
                border-radius: 10px;
                height: 45px;
                border: none;
                margin-top: 8px;
            }

            .stButton>button:hover {
                background: #c17228 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        # INSIDE PAGES STYLES + FLOATING SIDEBAR
        st.markdown(
            """
            <style>
            /* ---------- FLOATING SIDEBAR BOX (SOFT BEIGE) ---------- */
            [data-testid="stSidebar"] {
                background: rgba(255, 245, 235, 0.96) !important;
                border-radius: 20px !important;
                margin-top: 30px !important;
                margin-left: 20px !important;
                margin-bottom: 30px !important;
                padding: 20px 18px !important;
                width: 260px !important;
                height: auto !important;
                box-shadow: 0px 6px 30px rgba(110, 56, 11, 0.28) !important;
                border: 2px solid rgba(166, 90, 26, 0.35) !important;
                position: fixed !important;   /* floating effect */
                top: 60px !important;
                left: 15px !important;
                z-index: 999 !important;
            }

            /* Avoid sidebar content being cramped */
            [data-testid="stSidebar"] > div {
                padding: 0 !important;
            }

            /* Sidebar text + fonts */
            [data-testid="stSidebar"] * {
                color: #5a3213 !important;
                font-family: "Georgia", serif !important;
            }

            /* "Navigation" title */
            [data-testid="stSidebar"] h2 {
                font-weight: 800;
                font-size: 1.1rem;
                letter-spacing: 0.03em;
                margin-bottom: 0.75rem;
            }

            /* Radio group styling */
            [data-testid="stSidebar"] div[role="radiogroup"] label {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 8px 12px;
                border-radius: 999px;
                transition: background 0.25s ease, transform 0.1s ease;
            }

            [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
                background: rgba(255, 230, 200, 0.7);
                transform: translateX(4px);
            }

            /* Radio bullet accent */
            [data-testid="stSidebar"] input[type="radio"] {
                accent-color: #d98c47;
            }

            /* ---------- MAIN CARD / BUTTON STYLES ---------- */
            .card {
                background: rgba(255, 245, 235, 0.85);
                border-radius: 20px;
                padding: 30px;
                margin: 20px auto;
                max-width: 900px;
                box-shadow: 0 10px 30px rgba(110, 56, 11, 0.4);
                color: #5a3213;
                font-weight: bold;
                font-size: 1.1em;
                font-family: 'Georgia', serif;
            }

            a, a:hover {
                color: #a45c11 !important;
                text-decoration: none;
                font-weight: bold;
            }

            .stButton>button {
                background: linear-gradient(135deg, #d98c47, #bc6c4c);
                color: white;
                border:none;
                font-weight: bold;
                font-size: 1.2em;
                height: 48px;
                border-radius: 15px;
                box-shadow: 0 5px 18px rgba(135, 71, 15, 0.6);
                transition: all 0.3s ease;
            }

            .stButton>button:hover {
                background: linear-gradient(135deg, #bc6c4c, #d98c47);
                transform: translateY(-3px);
                box-shadow: 0 10px 30px rgba(135, 71, 15, 0.8);
            }

            .stTextInput>div>div>input {
                background: rgba(255, 245, 235, 0.9) !important;
                color: #5a3213 !important;
                border-radius: 15px !important;
                border: 2px solid #c88a40 !important;
                font-weight: bold;
                font-size: 1.05em;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

# -------------------------------
# MAIN APP
# -------------------------------
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "predicted_vibe" not in st.session_state:
        st.session_state.predicted_vibe = None

    logged_in = st.session_state.logged_in

    # --------- LOGIN PAGE ---------
    if not logged_in:
        # background + CSS for login
        set_background_image("login_page.png", offset_y="-120px")
        apply_custom_css(logged_in=False)

        st.markdown('<div class="main-block">', unsafe_allow_html=True)

        # Title (left aligned, one line)
        st.markdown(
            '<div class="login-title">🎶 Personalized Music Recommendation System</div>',
            unsafe_allow_html=True,
        )

        # Login box directly under title
        #st.markdown('<div class="login-box">', unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.markdown("</div>", unsafe_allow_html=True)  # close login-box
        st.markdown("</div>", unsafe_allow_html=True)  # close main-block

        return

    # --------- AFTER LOGIN (FULL WEBSITE) ---------
    set_background_image("inside_pages.png", offset_y="0px")
    apply_custom_css(logged_in=True)

    # SIDEBAR
    menu = st.sidebar.radio(
        "Navigation", ["Home", "Location", "Playlist", "Membership", "Logout"]
    )

    # CARD DECORATOR
    def card_wrap(func):
        def wrapped():
            #st.markdown('<div class="card">', unsafe_allow_html=True)
            func()
            st.markdown("</div>", unsafe_allow_html=True)
        return wrapped

    @card_wrap
    def page_home():
        st.markdown("### 🏠 Welcome to Your Music Journey!")
        st.write(
            "Discover music that matches your vibe based on your location. "
            "Use the sidebar to detect your location and generate personalized playlists."
        )
        st.image(
            "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f"
            "?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
            caption="Explore the world through music!",
            use_container_width=True,
        )
        st.markdown("*Features:*")
        st.markdown("- 🌍 Location-based vibe detection")
        st.markdown("- 🎵 Spotify playlist recommendations")
        st.markdown("- 🌐 Multi-language support")

    @card_wrap
    def page_location():
        st.markdown("### 🌍 Detect Your Location & Vibe")
        st.write("We'll use your IP to detect your location and predict the vibe around you.")

        col1, col2 = st.columns(2)
        with col1:
            st.image(
                "https://images.unsplash.com/photo-1524661135-423995f22d0b"
                "?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
                caption="Location Detection",
                use_container_width=True,
            )
        with col2:
            loc = get_current_location()
            if loc:
                st.success(f"📍 You are in {loc['city']}, {loc['state']}, {loc['country']}")
                vibe = predict_vibe(loc["lat"], loc["lon"])
                st.session_state.predicted_vibe = vibe
                if vibe:
                    st.info(f"🎵 Predicted Vibe: *{vibe['display']}*")
                    st.caption(f"(raw label: {vibe['label']})")
                else:
                    st.error("Couldn't predict vibe.")
            else:
                st.error("Could not detect location via IP. Enter coordinates below.")
                lat = st.text_input("Latitude")
                lon = st.text_input("Longitude")
                if st.button("Predict from Coordinates"):
                    if lat and lon:
                        vibe = predict_vibe(lat, lon)
                        st.session_state.predicted_vibe = vibe
                        if vibe:
                            st.info(f"🎵 Predicted Vibe: *{vibe['display']}*")
                            st.caption(f"(raw label: {vibe['label']})")
                        else:
                            st.error("Couldn't predict vibe from provided coordinates.")
                    else:
                        st.warning("Please enter both latitude & longitude.")

    @card_wrap
    def page_playlist():
        st.markdown("### 🎵 Generate Your Personalized Playlist")
        vibe = st.session_state.predicted_vibe

        if not vibe:
            st.warning("Please detect location first (go to Location).")
            return

        st.info(f"Using vibe: {vibe['display']} (raw: {vibe['label']})")

        lang_choice = st.radio(
            "Choose language filter:", ["All", "Hindi", "Bengali", "English"]
        )
        per_lang = st.slider("Playlists per language", 3, 12, 5)

        if st.button("Generate Playlist"):
            all_playlists = []
            langs = ["Hindi", "Bengali", "English"] if lang_choice == "All" else [lang_choice]

            for lang in langs:
                pl = get_spotify_playlists(
                    vibe_label=vibe["label"], language=lang, limit=per_lang
                )
                for item in pl:
                    item["language"] = lang
                all_playlists.extend(pl)

            if all_playlists:
                df = pd.DataFrame(all_playlists)
                for lang in df["language"].unique():
                    st.markdown(f"### {lang} Playlists 🎶")
                    subset = df[df["language"] == lang]
                    cols = st.columns(2)
                    for i, (_, row) in enumerate(subset.iterrows()):
                        with cols[i % 2]:
                            st.markdown(f"🔗 [{row['name']}]({row['url']})")
                            st.caption(f"Query: {row.get('source_query','')}")
                            if row.get("image"):
                                st.image(row["image"], width=250)
                            st.markdown("---")
            else:
                st.warning("No playlists found. Increase number or try different language.")

    @card_wrap
    def page_membership():
        st.markdown("### 👑 Premium Membership")
        st.markdown("Upgrade to unlock exclusive features and elevate your music experience!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### Basic Plan")
            st.markdown("- Access personalized playlists")
            st.markdown("- Normal speed recommendations")
            st.markdown("*Price: ₹99 / month*")
            if st.button("Choose Basic"):
                st.success("You selected: Basic Membership")

        with col2:
            st.markdown("#### Pro Plan")
            st.markdown("- Everything in Basic")
            st.markdown("- Faster Spotify search")
            st.markdown("- Multi-language recommendations")
            st.markdown("*Price: ₹199 / month*")
            if st.button("Choose Pro"):
                st.success("You selected: Pro Membership")

        with col3:
            st.markdown("#### Ultra Plan")
            st.markdown("- Everything in Pro")
            st.markdown("- Unlimited playlist fetch")
            st.markdown("- Priority support")
            st.markdown("- Custom vibe themes")
            st.markdown("*Price: ₹299 / month*")
            if st.button("Choose Ultra"):
                st.success("You selected: Ultra Membership")

        st.info("Membership purchase system coming soon!")

    # ROUTING
    if menu == "Home":
        page_home()
    elif menu == "Location":
        page_location()
    elif menu == "Playlist":
        page_playlist()
    elif menu == "Membership":
        page_membership()
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.predicted_vibe = None
        st.rerun()

if __name__ == "__main__":
    main()
