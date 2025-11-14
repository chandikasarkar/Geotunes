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

def get_spotify_playlists(vibe_label, language=None, limit=5):
    """
    Search Spotify playlists by vibe_label and language.
    - vibe_label: raw label (no emoji), e.g. "beach" or "heritage"
    - language: one of "Hindi", "Bengali", "English" or None for no specific language
    Returns a list of playlist dicts: {name, url, image, source_query}
    """
    playlists = []
    # Build query components
    # If a language is specified, include it; else just use vibe_label
    query_pieces = []
    if vibe_label:
        query_pieces.append(vibe_label)
    if language and language.lower() != "all":
        query_pieces.append(language)
    query_pieces.append("music")
    query = " ".join(query_pieces).strip()

    try:
        # Spotify search: type playlist
        results = sp.search(q=query, type="playlist", limit=limit)
        items = results.get('playlists', {}).get('items', [])

        for playlist in items:
            if not playlist:
                continue

            name = playlist.get('name', 'No Name')
            url = playlist.get('external_urls', {}).get('spotify', '')
            image = None
            if playlist.get('images') and len(playlist['images']) > 0:
                image = playlist['images'][0]['url']

            playlists.append({
                'name': name,
                'url': url,
                'image': image,
                'source_query': query
            })

    except Exception as e:
        st.error(f"❌ Spotify API error for query '{query}': {e}")

    return playlists

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
    st.title("🎶 Personalized Music Recommendation System")

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
    menu = st.sidebar.radio("Navigation", ["Home", "Location", "Playlist", "Logout"])

    if menu == "Home":
        st.write("Welcome! Use the sidebar to detect location and generate playlists.")

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

    elif menu == "Playlist":
        vibe = st.session_state.predicted_vibe

        if not vibe:
            st.warning("Please detect location first (go to Location).")
        else:
            st.info(f"Using vibe: {vibe['display']} (raw: {vibe['label']})")

            # Language selection: Hindi / Bengali / English / All
            lang_choice = st.radio("Choose language filter:", ["All", "Hindi", "Bengali", "English"])

            # Number of playlists per language (if All chosen, we'll fetch for each and aggregate)
            per_lang = st.slider("Playlists per language", min_value=3, max_value=12, value=5)

            if st.button("Generate Playlist"):
                all_playlists = []

                if lang_choice == "All":
                    for lang in ["Hindi", "Bengali", "English"]:
                        pl = get_spotify_playlists(vibe_label=vibe['label'], language=lang, limit=per_lang)
                        # tag with language
                        for item in pl:
                            item['language'] = lang
                        all_playlists.extend(pl)
                else:
                    pl = get_spotify_playlists(vibe_label=vibe['label'], language=lang_choice, limit=per_lang)
                    for item in pl:
                        item['language'] = lang_choice
                    all_playlists = pl

                if not all_playlists:
                    st.warning("No playlists found for that combination. Try increasing the number of playlists or try a different language.")
                else:
                    # Show results grouped by language for clarity
                    df = pd.DataFrame(all_playlists)
                    # group
                    for lang in df['language'].unique():
                        st.markdown(f"### {lang} playlists")
                        subset = df[df['language'] == lang]
                        for _, row in subset.iterrows():
                            st.write(f"🔗 [{row['name']}]({row['url']}) — (query: {row.get('source_query','')})")
                            if row.get('image'):
                                st.image(row['image'], width=280)

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.predicted_vibe = None
        st.success("Logged out!")
        st.rerun()

if __name__ == "__main__":
    main()
