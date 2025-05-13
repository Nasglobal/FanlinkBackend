import requests
import base64
from django.conf import settings
import difflib



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



def get_spotify_track_link(artist_name, track_name, release_date, isrc=None):
    access_token = get_spotify_access_token()
    search_url = "https://api.spotify.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Convert input release_date from DD/MM/YYYY to YYYY-MM-DD
    try:
        day, month, year = release_date.split("/")
        release_date_formatted = f"{year}-{month}-{day}"
    except ValueError:
        print("Invalid release date format. Please use DD/MM/YYYY.")
        release_date_formatted = ""
    
    query = f"artist:{artist_name} track:{track_name}"
    params = {
        "q": query,
        "type": "track",
        "limit": 10
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    response_data = response.json()
    
    try:
        tracks = response_data['tracks']['items']
        
        # First, try to find exact match
        for track in tracks:
            track_release_date = track['album']['release_date']
            track_isrc = track.get('external_ids', {}).get('isrc', '').lower()
            
            if track_release_date == release_date_formatted and (not isrc or track_isrc == isrc.lower()):
                print("✅ Exact match found based on release date and ISRC (Spotify)")
                return track['external_urls']['spotify']
        
        # No exact match, find the best fuzzy match
        best_match = None
        highest_score = 0

        for track in tracks:
            title = track['name']
            artist = track['artists'][0]['name']
            
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{artist.lower()} {title.lower()}"
            
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()
            if score > highest_score:
                highest_score = score
                best_match = track

        if best_match:
            print(f" Best fuzzy match found with score {highest_score:.2f} (Spotify)")
            return best_match['external_urls']['spotify']
        
        print(" No suitable tracks found.")
        return None
    
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error while processing Spotify response: {e}")
        return None



def replace_spaces_with_underscore(text):
    cleaned_text = text.strip()
    return cleaned_text.replace(" ", "_").replace("-", "_")



def search_boomplay_with_google(artist_name, track_name, release_date=None, isrc=None):
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
        best_match = None
        highest_score = 0

        for item in response_data.get('items', []):
            link = item['link']
            snippet = item.get('snippet', '').lower()
            title = item.get('title', '').lower()

            # Check for exact match based on release date and ISRC
            date_match = release_date is None or release_date in snippet or release_date in title
            isrc_match = isrc is None or isrc.lower() in snippet or isrc.lower() in title

            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (Boomplay)")
                return link
            
            # Compute similarity for fallback matching
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{title} {snippet}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = link

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (Boomplay)")
            return best_match
        
        print("❌ No Boomplay links found.")
        return None
    
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error while processing the response: {e}")
        return None



def search_audiomack_with_google(artist_name, track_name, release_date=None, isrc=None):
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
    
    try:
        best_match = None
        highest_score = 0

        for item in response_data.get('items', []):
            link = item['link']
            snippet = item.get('snippet', '').lower()
            title = item.get('title', '').lower()

            # Exact match check
            date_match = release_date is None or release_date in snippet or release_date in title
            isrc_match = isrc is None or isrc.lower() in snippet or isrc.lower() in title

            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (Audiomack)")
                return link
            
            # Best match fallback using similarity
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{title} {snippet}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = link

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (Audiomack)")
            return best_match

        print("❌ No Audiomack links found.")
        return None
    
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error while processing the response: {e}")
        return None



def get_itunes_track_link(artist_name, track_name, release_date=None, isrc=None):
    search_url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist_name} {track_name}",
        "media": "music",
        "limit": 20,  # Fetch multiple results for filtering
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        best_match = None
        highest_score = 0

        for track in response_data.get('results', []):
            track_release_date = track.get('releaseDate', '')[:10]  # YYYY-MM-DD
            track_isrc = track.get('isrc', '')

            # Exact match
            date_match = release_date is None or release_date == track_release_date
            isrc_match = isrc is None or isrc == track_isrc

            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (iTunes)")
                return track['trackViewUrl']

            # Best fuzzy match fallback
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{track.get('artistName', '').lower()} {track.get('trackName', '').lower()}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = track['trackViewUrl']

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (iTunes)")
            return best_match

        print("❌ No tracks found")
        return None

    except (IndexError, KeyError, TypeError) as e:
        print(f"Error while processing the response: {e}")
        return None
