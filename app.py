import streamlit as st
import requests
import pickle
import numpy as np
import pandas as pd
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

# -------------------------------
# LOAD THE NEW KNN HAVERSINE MODEL (.pkl YOU CREATED)
# -------------------------------
try:
    with open("vibe_knn_model.pkl", "rb") as f:
        bundle = pickle.load(f)
        vibe_model = bundle["model"]
        encoder = bundle["encoder"]   # label encoder included in pkl

    # Emoji mapping (label_name → prettified emoji text)
    emoji_map = {
        "backwater": "Backwater 🌊",
        "beach": "Beach 🏖",
        "city": "City Tour 🏙",
        "coastal": "Coastal Breeze 🌅",
        "coastal-city": "Coastal City 🌆",
        "cultural": "Cultural Heritage 🎭",
        "desert": "Desert 🏜",
        "forest": "Forest 🌲",
        "heritage": "Heritage Site 🏰",
        "hill-town": "Hill Town 🏞",
        "industrial": "Industrial Zone 🏗",
        "mountain": "Mountain ⛰",
        "pilgrim-town": "Pilgrim Town 🙏",
        "rural": "Rural Countryside 🚜",
        "spiritual": "Spiritual Place 🕉",
        "temple-town": "Temple Town 🛕",
        "urban": "Urban City 🏙"
    }

except Exception as e:
    st.error(f"❌ Failed to load vibe_knn_model.pkl : {e}")
    vibe_model = None
    encoder = None
    emoji_map = {}

# -------------------------------
# VIBE PREDICTION FUNCTION
# -------------------------------
def predict_vibe(lat, lon):
    """
    Returns a dict: {
      'label': raw label_name (e.g. "beach"),
      'display': pretty display (e.g. "Beach 🏖")
    }
    """
    if vibe_model is None or encoder is None:
        st.error("❌ KNN model or encoder could not be loaded.")
        return None

    try:
        # model was trained on radians → convert input
        coords = pd.DataFrame([[float(lat), float(lon)]], columns=['latitude','longitude'])
        coords_rad = np.radians(coords)

        pred_numeric = vibe_model.predict(coords_rad)[0]

        # decode numeric label → text label
        label_name = encoder.inverse_transform([pred_numeric])[0]

        # apply emoji if exists (presentational)
        vibe_display = emoji_map.get(label_name.lower(), label_name)

        return {"label": label_name, "display": vibe_display}

    except Exception as e:
        st.error(f"❌ Prediction error: {e}")
        return None

# -------------------------------
# SPOTIFY SETUP
# (Consider moving client_id & secret to Streamlit secrets for production)
# -------------------------------
sp = Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id='1d46738e78ad4e45b79208be4da1a018',
    client_secret='0639372d03e44e098f7f8f1a4249bbd7'
))

def get_spotify_tracks(vibe_label, language=None, limit=20):
    """
    Search Spotify tracks by vibe_label and language.
    - vibe_label: raw label (no emoji), e.g. "beach"
    - language: "Hindi", "Bengali", "English" or None/"All"
    - limit: number of tracks to request (max 50 typical)
    Returns list of tracks: {name, artists, url, preview_url, image, album, track_id, source_query}
    """
    tracks = []
    query_pieces = []
    if vibe_label:
        query_pieces.append(vibe_label)
    if language and language.lower() not in ["all", "none"]:
        # include language term to bias search
        query_pieces.append(language)
    # add generic music/track terms to guide search
    query_pieces.append("song")
    query = " ".join(query_pieces).strip()

    try:
        results = sp.search(q=query, type="track", limit=limit)
        items = results.get('tracks', {}).get('items', [])

        seen_ids = set()  # dedupe
        for t in items:
            if not t:
                continue
            tid = t.get('id')
            if not tid or tid in seen_ids:
                continue
            seen_ids.add(tid)

            name = t.get('name', 'Unknown Title')
            artists = ", ".join([a.get('name') for a in t.get('artists', []) if a.get('name')])
            url = t.get('external_urls', {}).get('spotify', '')
            preview = t.get('preview_url')  # may be None
            album = t.get('album', {}).get('name', '')
            image = None
            images = t.get('album', {}).get('images') or []
            if images:
                image = images[0]['url']  # largest available first

            tracks.append({
                "track_id": tid,
                "name": name,
                "artists": artists,
                "album": album,
                "url": url,
                "preview_url": preview,
                "image": image,
                "source_query": query
            })

    except Exception as e:
        st.error(f"❌ Spotify API error for query '{query}': {e}")

    return tracks

# -------------------------------
# IP LOCATION
# -------------------------------
def get_current_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()

        lat, lon = data['loc'].split(',')
        return {
            "city": data.get('city', ''),
            "state": data.get('region', ''),
            "country": data.get('country', ''),
            "lat": lat,
            "lon": lon
        }
    except Exception:
        return None

# -------------------------------
# LOGIN (STATIC)
# -------------------------------
def login(username, password):
    return username == "admin" and password == "123"

# -------------------------------
# STREAMLIT UI
# -------------------------------
def main():
    st.title("🎶 Personalized Music Recommendation System — Songs by Vibe + Language")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if 'predicted_vibe' not in st.session_state:
        st.session_state.predicted_vibe = None  # will hold dict {'label','display'}

    # Simple login
    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
        return  # stop further UI rendering until logged in

    # Logged in UI
    menu = st.sidebar.radio("Navigation", ["Home", "Location", "Songs", "Logout"])

    if menu == "Home":
        st.write("Welcome! Use the sidebar to detect location and generate songs by vibe & language.")

    elif menu == "Location":
        st.subheader("🌍 Detecting location...")

        loc = get_current_location()

        if loc:
            st.success(f"📍 You are in {loc['city']}, {loc['state']}, {loc['country']}")
            vibe = predict_vibe(loc["lat"], loc["lon"])
            st.session_state.predicted_vibe = vibe

            if vibe:
                st.info(f"🎵 Predicted Vibe: *{vibe['display']}*")
                st.caption(f"(raw label used for searching: {vibe['label']})")
            else:
                st.error("Couldn't predict vibe.")
        else:
            st.error("Could not detect location via IP. You can enter coordinates manually below.")
            lat = st.text_input("Latitude")
            lon = st.text_input("Longitude")
            if st.button("Predict vibe from coordinates"):
                if lat and lon:
                    vibe = predict_vibe(lat, lon)
                    st.session_state.predicted_vibe = vibe
                    if vibe:
                        st.info(f"🎵 Predicted Vibe: *{vibe['display']}*")
                        st.caption(f"(raw label used for searching: {vibe['label']})")
                    else:
                        st.error("Couldn't predict vibe from the provided coordinates.")
                else:
                    st.warning("Please enter both latitude and longitude.")

    elif menu == "Songs":
        vibe = st.session_state.predicted_vibe

        if not vibe:
            st.warning("Please detect location first (go to Location).")
        else:
            st.info(f"Using vibe: {vibe['display']} (raw: {vibe['label']})")

            # Language selection: Hindi / Bengali / English / All
            lang_choice = st.radio("Choose language filter:", ["All", "Hindi", "Bengali", "English"])

            # Number of tracks to fetch per language (if All chosen, we'll fetch per language and combine)
            per_lang = st.slider("Tracks per language (or total if single language chosen)", min_value=5, max_value=50, value=20)

            if st.button("Generate Songs"):
                all_tracks = []

                if lang_choice == "All":
                    # For All, fetch per language and combine with dedupe
                    for lang in ["Hindi", "Bengali", "English"]:
                        tlist = get_spotify_tracks(vibe_label=vibe['label'], language=lang, limit=per_lang)
                        for t in tlist:
                            t['language'] = lang
                        all_tracks.extend(tlist)
                else:
                    tlist = get_spotify_tracks(vibe_label=vibe['label'], language=lang_choice, limit=per_lang)
                    for t in tlist:
                        t['language'] = lang_choice
                    all_tracks = tlist

                if not all_tracks:
                    st.warning("No songs found for that combination. Try increasing the number of tracks or try a different language.")
                else:
                    # Deduplicate by track_id while preserving language tag (first occurrence kept)
                    dedup = {}
                    for t in all_tracks:
                        if t['track_id'] not in dedup:
                            dedup[t['track_id']] = t
                    final_tracks = list(dedup.values())

                    # Optionally sort/group by language
                    df = pd.DataFrame(final_tracks)
                    if 'language' in df.columns:
                        for lang in df['language'].unique():
                            st.markdown(f"### {lang} songs")
                            subset = df[df['language'] == lang]
                            for _, row in subset.iterrows():
                                st.write(f"{row['name']}** — {row['artists']} — {row['album']}")
                                if row.get('image'):
                                    st.image(row['image'], width=260)
                                if row.get('preview_url'):
                                    st.audio(row['preview_url'])
                                else:
                                    st.write(f"[Open in Spotify]({row['url']})")
                                st.caption(f"search query: {row.get('source_query','')}")
                    else:
                        # fallback: list all
                        for row in final_tracks:
                            st.write(f"{row['name']}** — {row['artists']} — {row['album']}")
                            if row.get('image'):
                                st.image(row['image'], width=260)
                            if row.get('preview_url'):
                                st.audio(row['preview_url'])
                            else:
                                st.write(f"[Open in Spotify]({row['url']})")
                            st.caption(f"search query: {row.get('source_query','')}")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.predicted_vibe = None
        st.success("Logged out!")
        st.rerun()

if _name_ == "_main_":
    main()
