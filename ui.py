# ui.py
# Contains all UI/frontend logic for the Personalized Music Recommendation System

import streamlit as st
from auth import login
from location_utils import get_location_based_search
from spotify_utils import get_spotify_playlists

# -------------------------------
# Main function to run the UI
# -------------------------------
def main():
    # Custom CSS for styling
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(to right, #1f1c2c, #928dab);
            color: white;
            font-family: 'Segoe UI', sans-serif;
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            border-radius: 12px;
            padding: 0.5em 1.5em;
            font-size: 16px;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #ff7676;
            color: white;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
        }
        .success-box {
            padding: 10px;
            border-radius: 8px;
            background-color: #2ecc71;
            color: white;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title
    st.markdown("<h1 style='text-align: center; color: white;'>🎶 Personalized Music Recommendation System 🎶</h1>", unsafe_allow_html=True)

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'location' not in st.session_state:
        st.session_state.location = None

    # -------------------------------
    # Login Page
    # -------------------------------
    if not st.session_state.logged_in:
        st.markdown("<h3 style='text-align: center;'>🔐 Admin Login</h3>", unsafe_allow_html=True)
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.success("✅ Welcome Admin!")
            else:
                st.error("❌ Invalid credentials. Please try again.")

    else:
        # -------------------------------
        # Sidebar Navigation
        # -------------------------------
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/727/727245.png", width=80)  
        st.sidebar.title("🎼 Navigation")
        options = ["🏠 Home", "📍 Location", "🎧 Generate Playlist", "⭐ Membership", "🚪 Log Out"]
        choice = st.sidebar.radio("Select an option", options)

        # -------------------------------
        # Pages
        # -------------------------------
        if choice == "🏠 Home":
            st.subheader("✨ Welcome to the Music Recommendation System")
            st.info("Discover the Best playlists personalized for your current location.")

        elif choice == "📍 Location":
            st.subheader("🌍 Enter Your Location")
            
            country = st.text_input("🏳 Enter Country")
            state = st.text_input("🗺 Enter State")
            city = st.text_input("🏙 Enter City")
            
            travelling = st.radio("✈ Are you travelling?", ("Yes", "No"))
            
            travel_place = None
            current_place = None
            
            if travelling == "Yes":
                travel_place = st.selectbox(
                    "🌄 Where are you travelling?",
                    ["Mountain ⛰", "Beach 🏖", "Forest 🌲", "Desert 🏜", "City Tour 🏙"]
                )
            else:
                current_place = st.selectbox(
                    "📌 Select the place you are now",
                    ["Cafe ☕", "Mall 🏬", "Fair 🎡", "Hospital 🏥", "Restaurant 🍽", "Park 🌳", "Other ✍"]
                )
                if current_place == "Other ✍":
                    current_place = st.text_input("✍ Enter your current place")
            
            if st.button("💾 Save Location"):
                if country and state and city:
                    st.session_state.location = {
                        'country': country,
                        'state': state,
                        'city': city,
                        'travelling': travelling == "Yes",
                        'travel_place': travel_place,
                        'current_place': current_place
                    }
                    if travelling == "Yes":
                        st.success(
                            f"📍 Location set to: {city}, {state}, {country} | Travelling to: {travel_place}"
                        )
                    else:
                        st.success(
                            f"📍 Location set to: {city}, {state}, {country} | Currently at: {current_place}"
                        )
                else:
                    st.error("⚠ Please fill Country, State, and City before saving.")

        elif choice == "🎧 Generate Playlist":
            st.subheader("🎵 Generate Your Playlist")
            
            if st.session_state.location:
                location = st.session_state.location
                location_search = get_location_based_search(location)
                st.info(f"📍 Location-based suggestion: {location_search} music")
                
                genres = ["Use Location-Based", "Pop", "Classical", "Retro", "Jazz", "Lofi"]
                selected = st.selectbox(
                    "🎼 Select your search type",
                    genres
                )
                
                if selected == "Use Location-Based":
                    search_type = location_search
                else:
                    search_type = selected
            else:
                st.warning("⚠ Please set your location first for personalized recommendations!")
                search_type = st.selectbox(
                    "🎼 Select your favorite genre",
                    ["Pop", "Classical", "Retro", "Jazz", "Lofi"]
                )
            
            if st.button("Generate Playlist"):
                spotify_playlists = get_spotify_playlists(search_type, limit=5)
                if spotify_playlists:
                    st.success("🎶 Here are some Spotify playlists for you:")
                    for i, pl in enumerate(spotify_playlists, start=1):
                        st.write(f"✅ {i}. [{pl['name']}]({pl['url']})")
                        if pl['image']:
                            st.image(pl['image'], width=300)
                else:
                    st.error("⚠ No playlists found for this search type.")

        elif choice == "⭐ Membership":
            st.subheader("💎 Membership Options")
            st.write("Upgrade to Premium Membership for:")
            st.markdown("""
            - 🚀 Unlimited Playlist Generation  
            - 🎤 AI-based Song Recommendations  
            - 🎶 Exclusive Access to Premium Songs  
            """)
            if st.button("✨ Sign Up for Premium"):
                st.balloons()
                st.success("🎉 Thank you for becoming a Premium Member!")

        elif choice == "🚪 Log Out":
            st.warning("👋 You have been logged out.")
            st.session_state.logged_in = False
            st.session_state.location = None  # Reset location on logout