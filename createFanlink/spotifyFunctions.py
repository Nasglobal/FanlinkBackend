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



def get_spotify_track_link(artist_name, track_name, release_date, isrc=None):
    access_token = get_spotify_access_token()
    search_url = "https://api.spotify.com/v1/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    
    # Convert input release_date from DD/MM/YYYY to YYYY-MM-DD
    try:
        day, month, year = release_date.split("/")
        release_date_formatted = f"{year}-{month}-{day}"  # Convert to YYYY-MM-DD
    except ValueError:
        print("Invalid release date format. Please use DD/MM/YYYY.")
        release_date_formatted = ""
    
    query = f"artist:{artist_name} track:{track_name}"
    params = {
        "q": query,
        "type": "track",
        "limit": 10  # Retrieve multiple results for filtering
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    response_data = response.json()
    print("spotify response",response_data)
    try:
        for track in response_data['tracks']['items']:
            track_release_date = track['album']['release_date']
            track_isrc = track.get('external_ids', {}).get('isrc').lower()
            
            # Compare release dates and ISRC if provided
            if track_release_date == release_date_formatted and (not isrc or track_isrc == isrc.lower()):
                print("Exact match found based on release date and ISRC spotify")
                return track['external_urls']['spotify']
        
        # No exact match, return the first result as fallback
        if response_data['tracks']['items']:
            print("No Exact match found based on release date and ISRC spotify")
            first_track = response_data['tracks']['items'][0]
            return first_track['external_urls']['spotify']
        
        print("No tracks found")
        return None
    
    except (KeyError, IndexError) as e:
        print(f"Error while processing the response: {e}")
        return None



def replace_spaces_with_underscore(text):
    return text.replace(" ", "_").replace("-", "_")



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
        for item in response_data.get('items', []):
            link = item['link']
            
            # Check for release_date and isrc in the snippet or title
            snippet = item.get('snippet', '').lower()
            title = item.get('title', '').lower()
            
            date_match = release_date is None or release_date in snippet or release_date in title
            isrc_match = isrc is None or isrc.lower() in snippet or isrc.lower() in title
            
            if date_match and isrc_match:
                print("Exact match found based on release date and ISRC boomplay")
                return link
        
        # No exact match, return the first result as fallback
        if response_data.get('items'):
            print("No exact match found, returning first result boomplay")
            return response_data['items'][0]['link']
        
        print("No links found")
        return None
    
    except (IndexError, KeyError) as e:
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
        for item in response_data.get('items', []):
            link = item['link']
            
            # Attempt to validate release_date and ISRC in the description or snippet
            snippet = item.get('snippet', '').lower()
            
            date_match = release_date is None or release_date in snippet
            isrc_match = isrc is None or isrc.lower() in snippet
            
            if date_match or isrc_match:
                print("Exact match found based on release date and ISRC audiomack")
                return link
        
        # No exact match, return the first result as fallback
        if response_data.get('items'):
            print("No exact match found, returning first result audiomack")
            return response_data['items'][0]['link']
        
        print("No links found")
        return None
    
    except (IndexError, KeyError) as e:
        print(f"Error while processing the response: {e}")
        return None


def get_itunes_track_link(artist_name, track_name, release_date=None, isrc=None):
    search_url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist_name} {track_name}",
        "media": "music",
        "limit": 10,  # Fetch multiple results for filtering
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        for track in response_data.get('results', []):
            track_release_date = track.get('releaseDate', '')[:10]  # Extract only the date part (YYYY-MM-DD)
            track_isrc = track.get('isrc', '')  # iTunes includes ISRC if available
            
            # Check for release_date and isrc match
            date_match = release_date is None or release_date == track_release_date
            isrc_match = isrc is None or isrc == track_isrc
            
            if date_match or isrc_match:
                print("Exact match found based on release date and ISRC itunes")
                return track['trackViewUrl']
        
        # No exact match, return the first result as fallback
        if response_data.get('results'):
            print("No exact match found, returning first result itunes")
            return response_data['results'][0]['trackViewUrl']
        
        print("No tracks found")
        return None
    
    except (IndexError, KeyError) as e:
        print(f"Error while processing the response: {e}")
        return None
