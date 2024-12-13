import requests
from django.conf import settings


def get_youtube_video_link(artist_name, track_name):
    api_key = settings.YOUTUBE_API_KEY
    search_url = "https://www.googleapis.com/youtube/v3/search"
    
    params = {
        "part": "snippet",
        "q": f"{artist_name} {track_name}",
        "type": "video",
        "maxResults": 1,
        "key": api_key
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    # Extract the video URL from the response
    try:
        video_id = response_data['items'][0]['id']['videoId']
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        return video_link
    except (IndexError, KeyError):
        return None

def get_deezer_track_link(artist_name, track_name):
    search_url = "https://api.deezer.com/search"
    params = {
        "q": f"artist:'{artist_name}' track:'{track_name}'",
        "limit": 1,
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        # Get the link to the track page if found
        track_link = response_data['data'][0]['link']
        return track_link
    except (IndexError, KeyError):
        return None


def get_apple_music_link(artist_name, track_name):
    search_url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist_name} {track_name}",
        "media": "music",
        "limit": 1,
        "entity": "song"
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        # Get the URL for the track if found
        track_link = response_data['results'][0]['trackViewUrl']
        return track_link
    except (IndexError, KeyError):
        return None



def search_amazon_music_with_google(artist_name, track_name):
    api_key = settings.GOOGLE_API_KEY
    cse_id = settings.GOOGLE_CSE_ID
    search_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": f"{artist_name} {track_name} site:music.amazon.com",
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        amazon_music_link = response_data['items'][0]['link']
        return amazon_music_link
    except (IndexError, KeyError):
        return None



def search_tidal_with_google(artist_name, track_name):
    api_key = settings.GOOGLE_API_KEY
    cse_id = settings.GOOGLE_CSE_ID
    search_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": f"{artist_name} {track_name} site:tidal.com",
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        tidal_link = response_data['items'][0]['link']
        return tidal_link
    except (IndexError, KeyError):
        return None