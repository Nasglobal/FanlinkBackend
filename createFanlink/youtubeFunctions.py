import requests
from django.conf import settings


def get_youtube_video_link(artist_name, track_name, release_date, isrc=None):
    api_key = settings.YOUTUBE_API_KEY
    search_url = "https://www.googleapis.com/youtube/v3/search"
    
    # Convert input release_date from DD/MM/YYYY to YYYY-MM-DD
    try:
        day, month, year = release_date.split("/")
        release_date_formatted = f"{year}-{month}-{day}"  # Convert to YYYY-MM-DD
    except ValueError:
        print("Invalid release date format. Please use DD/MM/YYYY.")
        release_date_formatted = ""
    
    # Build search query
    query = f"{artist_name} {track_name}"
    
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 10,
        "key": api_key,
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        for item in response_data['items']:
            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            published_at = item['snippet']['publishedAt'][:10]  # Extract YYYY-MM-DD from publishedAt
            
            # Assume the ISRC is included in the title or description (requires proper matching logic)
            video_description = item['snippet'].get('description', "")
            isrc_match = isrc in video_title or isrc in video_description if isrc else True
            
            # Compare release dates and ISRC if provided
            if published_at == release_date_formatted or isrc_match:
                print("Exact match found based on release date and ISRC youtube")
                return f"https://www.youtube.com/watch?v={video_id}"
        

        # No exact match, return the first result as fallback
        if response_data['items']:
            first_video_id = response_data['items'][0]['id']['videoId']
            print("No exact match found, returning first result youtube")
            return f"https://www.youtube.com/watch?v={first_video_id}"  
        
        print("No videos found")
        return None
    
    except (KeyError, IndexError) as e:
        print(f"Error while processing the response: {e}")
        return None


def get_deezer_track_link(artist_name, track_name, release_date=None, isrc=None):
    search_url = "https://api.deezer.com/search"
    
    # Construct the search query
    query = f"artist:'{artist_name}' track:'{track_name}'"
   
    params = {
        "q": query,
        "limit": 10,  # Fetch multiple results for filtering
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        for track in response_data.get('data', []):
            track_isrc = track.get('isrc')
            album = track.get('album', {})
            track_release_date = album.get('release_date')

            # Check for release_date and ISRC
            date_match = release_date is None or release_date == track_release_date
            isrc_match = isrc is None or isrc == track_isrc
            
            if date_match and isrc_match:
                print("Exact match found based on release date and ISRC deexer")
                return track.get('link')
        
        # No exact match, return the first result as fallback
        if response_data.get('data'):
            print("No exact match found, returning the first result deezer")
            return response_data['data'][0].get('link')
        
        print("No tracks found")
        return None
    
    except (KeyError, IndexError) as e:
        print(f"Error while processing the response: {e}")
        return None


def get_apple_music_link(artist_name, track_name, release_date=None, isrc=None):
    search_url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist_name} {track_name}",
        "media": "music",
        "limit": 10,  # Retrieve multiple results for filtering
        "entity": "song"
    }
    
    response = requests.get(search_url, params=params)
    response_data = response.json()
    
    try:
        for result in response_data['results']:
            track_release_date = result.get('releaseDate', '')[:10]  # Extract YYYY-MM-DD
            track_isrc = result.get('isrc', '')  # Retrieve ISRC
            
            # Check release_date and isrc if provided
            date_match = release_date is None or release_date in track_release_date
            isrc_match = isrc is None or isrc == track_isrc
            
            if date_match or isrc_match:
                print("Exact match found based on release date and ISRC apple music")
                return result['trackViewUrl']
        
        # No exact match, return the first result as fallback
        if response_data['results']:
            print("No exact match found, returning first result apple music")
            return response_data['results'][0]['trackViewUrl']
        
        print("No tracks found")
        return None
    
    except (IndexError, KeyError) as e:
        print(f"Error while processing the response: {e}")
        return None



def search_amazon_music_with_google(artist_name, track_name, release_date=None, isrc=None):
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
        for item in response_data.get('items', []):
            # Extract metadata from the search result snippet
            snippet = item.get('snippet', '').lower()
            link = item.get('link', '')
            
            # Check for release_date and ISRC in snippet (if provided)
            date_match = release_date is None or release_date in snippet
            isrc_match = isrc is None or isrc in snippet
            
            if date_match and isrc_match:
                print("Exact match found based on release date and ISRC")
                return link
        
        # No exact match, return the first result as fallback
        if response_data.get('items'):
            print("No exact match found, returning first result")
            return response_data['items'][0]['link']
        
        print("No tracks found")
        return None
    
    except (IndexError, KeyError) as e:
        print(f"Error while processing the response: {e}")
        return None



def search_tidal_with_google(artist_name, track_name, release_date=None, isrc=None): 
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
        for item in response_data.get('items', []):
            # Extract metadata from the search result snippet
            snippet = item.get('snippet', '').lower()
            link = item.get('link', '')
            
            # Check for release_date and ISRC in snippet (if provided)
            date_match = release_date is None or release_date in snippet
            isrc_match = isrc is None or isrc in snippet
            
            if date_match or isrc_match:
                print("Exact match found based on release date and ISRC tidal")
                return link
        
        # No exact match, return the first result as fallback
        if response_data.get('items'):
            print("No exact match found, returning first result tidal")
            return response_data['items'][0]['link']
        
        print("No tracks found")
        return None
    
    except (IndexError, KeyError) as e:
        print(f"Error while processing the response: {e}")
        return None
