import requests
import base64
from django.conf import settings



def get_spotify_access_token():
    client_id = settings.SPOTIFY_CLIENT_ID
    client_secret = settings.SPOTIFY_CLIENT_SECRET
    auth_url = "https://accounts.spotify.com/api/token"
    
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(auth_url, headers=headers, data=data)
    response_data = response.json()
    
    return response_data.get("access_token")


def get_spotify_track_link(artist_name, track_name):
    access_token = get_spotify_access_token()
    search_url = "https://api.spotify.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": f"artist:{artist_name} track:{track_name}",
        "type": "track",
        "limit": 1
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    response_data = response.json()
    
    # Extract the first track's Spotify link
    try:
        track_link = response_data['tracks']['items'][0]['external_urls']['spotify']
        return track_link
    except (IndexError, KeyError):
        return None


def replace_spaces_with_underscore(text):
    return text.replace(" ", "_").replace("-", "_")



def search_boomplay_with_google(artist_name, track_name):
    api_key = settings.GOOGLE_API_KEY
    cse_id = settings.GOOGLE_CSE_ID
    search_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": f"{artist_name} {track_name} site:boomplay.com",
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        # Get the first result link if available
        boomplay_link = response_data['items'][0]['link']
        return boomplay_link
    except (IndexError, KeyError):
        return None


def search_audiomack_with_google(artist_name, track_name):
    api_key = settings.GOOGLE_API_KEY
    cse_id = settings.GOOGLE_CSE_ID
    search_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": f"{artist_name} {track_name} site:audiomack.com",
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    # Extract the first result link if available
    try:
        audiomack_link = response_data['items'][0]['link']
        return audiomack_link
    except (IndexError, KeyError):
        return None

def get_itunes_track_link(artist_name, track_name):
    search_url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist_name} {track_name}",
        "media": "music",
        "limit": 1,
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        # Get the URL for the track if found
        track_link = response_data['results'][0]['trackViewUrl']
        return track_link
    except (IndexError, KeyError):
        return None