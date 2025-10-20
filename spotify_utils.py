# spotify_utils.py
# Utilities for interacting with the Spotify API

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Spotify API Setup
sp = Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def get_spotify_playlists(search_type, limit=5):
    """
    Search Spotify playlists by search_type/keyword (can be genre or location-based).
    
    Args:
        search_type (str): Keyword for search (e.g., "pop" or "beach vibes").
        limit (int): Number of playlists to fetch.
    
    Returns:
        list: List of dicts with {'name', 'url', 'image'}.
    """
    try:
        results = sp.search(q=f"{search_type} music", type="playlist", limit=limit)
        playlists = []
        items = results.get('playlists', {}).get('items', [])

        for playlist in items:
            if playlist:  # Ensure playlist is not None
                playlists.append({
                    'name': playlist.get('name', 'No Name'),
                    'url': playlist.get('external_urls', {}).get('spotify', ''),
                    'image': playlist['images'][0]['url'] if playlist.get('images') else None
                })
        return playlists
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return []