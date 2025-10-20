# location_utils.py
# Utilities for location-based playlist searches

def get_location_based_search(location):
    """
    Map location/place to a Spotify search keyword.
    
    Args:
        location (dict): Location data from session state.
    
    Returns:
        str: Search keyword for Spotify.
    """
    if location.get('travelling', False):
        place = location['travel_place']
    else:
        place = location['current_place']
    
    # Mapping of places to search keywords
    mapping = {
        "Mountain ⛰": "mountain adventure",
        "Beach 🏖": "beach vibes chill",
        "Forest 🌲": "forest ambient nature",
        "Desert 🏜": "desert folk",
        "City Tour 🏙": "city pop urban",
        "Cafe ☕": "lofi cafe chill",
        "Mall 🏬": "pop upbeat shopping",
        "Fair 🎡": "festival fun carnival",
        "Hospital 🏥": "calm relaxing healing",
        "Restaurant 🍽": "dinner jazz lounge",
        "Park 🌳": "acoustic folk park",
    }
    
    # If place is "Other" or custom input, use the input as base
    if place not in mapping:
        return f"{place} vibes"
    
    return mapping.get(place, f"{place} music")