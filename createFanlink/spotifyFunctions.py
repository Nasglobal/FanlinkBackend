import requests
import base64
from django.conf import settings
import difflib
from rapidfuzz import fuzz
from difflib import get_close_matches,SequenceMatcher
from bs4 import BeautifulSoup



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



def is_match(track, name, artist, isrc=None, release_date=None):

    # Clean and compare track name using fuzzy matching
    track_name_clean = track['name'].strip().lower()

    name_clean = name.strip().lower()
    name_score = fuzz.ratio(track_name_clean, name_clean)

    if name_score < 90:  # Acceptable similarity threshold
        return False

    for a in track['artists']:
        print("artists to match",a['name'].strip().lower())


    # Clean and compare artist names
    artist_clean = artist.strip().lower()
    artist_match = any(
        fuzz.ratio(a['name'].strip().lower(), artist_clean) >= 85
        for a in track['artists']
    )


    if not artist_match:
        return False



    # if isrc:
    #     isrc_match = track.get('external_ids', {}).get('isrc', '').upper() == isrc.upper()
    #     if not isrc_match:
    #         return False


    # if release_date:
    #     track_release = track.get('album', {}).get('release_date', '')
    #     if track_release and track_release != release_date:
    #         return False

    return True

def get_spotify_track_link(artist_name, track_name, release_date=None, isrc=None):
    
    token = get_spotify_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    search_url = "https://api.spotify.com/v1/search"

    # --- First search by ISRC ---
    if isrc:
        print("🔄 Trying ISRC search...")
        params_isrc = {
            "q": f'isrc:{isrc}',
            "type": "track",
            "limit": 1
        }
        res_isrc = requests.get(search_url, headers=headers, params=params_isrc).json()
        isrc_track = res_isrc.get('tracks', {}).get('items', [])
        if isrc_track :
            for track in isrc_track:
                return track['external_urls']['spotify']
        else:
            print("ISRC seaech not found..")

    #--- Optional Search: Use search endpoint with track + artist ---
    params = {
        "q": f'track:"{track_name}" artist:"{artist_name}"',
        "type": "track,album",
        "limit": 50
    }


    res = requests.get(search_url, headers=headers, params=params).json()

    if not res:
        print("❌ no search response found")
        return None

    for track in res.get('tracks', {}).get('items', []):
        print("direct search:", track['name'])
        
        if is_match(track, track_name, artist_name, isrc, release_date):
            print("✅ Found via direct search")
            return track['external_urls']['spotify']



    # print("🔄 pagination search...")
    # for page in range(20):  # max 1000 results (20 * 50)
    #     params = {
    #         "q": f"{track_name} artist:{artist_name}",
    #         "type": "track,album",
    #         "limit": 50,
    #         "offset": page * 50
    #     }
    #     res = requests.get(search_url, headers=headers, params=params)
    #     data = res.json()
    #     tracks = data.get("tracks", {}).get("items", [])

    #     if not tracks:
    #         print("Pagination search not found..")
    #         break

    #     for track in tracks:
    #         print("direct search:", track['name'])
    #         full_track = requests.get(f"https://api.spotify.com/v1/tracks/{track['id']}", headers=headers).json()
    #         if is_match(full_track, track_name, artist_name, isrc, release_date):
    #             print("✅ Found via paginated direct search")
    #             return full_track['external_urls']['spotify']


    # --- Fallback: Search artist, list albums, and check tracks --- 
    print("🔄 Searching artist and their albums as fallback...")
    artist_search = requests.get(search_url, headers=headers, params={
        "q": artist_name,
        "type": "artist",
        "limit": 50
    }).json()

    if not artist_search:
        print("❌ no arsits search found")
        return None 

    artists = artist_search.get('artists', {}).get('items', [])
    matched_artist = next((a for a in artists if a['name'].strip().lower() == artist_name.strip().lower()), None)

    if not matched_artist and artists:
        close = get_close_matches(artist_name, [a['name'] for a in artists], n=1, cutoff=0.6)
        if close:
            matched_artist = next((a for a in artists if a['name'] == close[0]), None)
            print("⚠️ Using fuzzy match artist:", close[0])


    if not matched_artist:
        print("❌ Artist not found")
        return None

    artist_id = matched_artist['id']
    album_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    all_albums = []
    while album_url:
        res = requests.get(album_url, headers=headers, params={"limit": 50}).json()
        all_albums.extend(res.get('items', []))
        album_url = res.get('next')

    for album in all_albums:
        album_id = album['id']
        album_release = album.get('release_date', '')
        track_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        while track_url:
            track_res = requests.get(track_url, headers=headers).json()
            for track in track_res.get('items', []):
                track_details = requests.get(f"https://api.spotify.com/v1/tracks/{track['id']}", headers=headers).json()
                if is_match(track_details, track_name, artist_name, isrc, release_date or album_release):
                    print("✅ Found via artist album fallback")
                    return track_details['external_urls']['spotify']
            track_url = track_res.get('next')

    print("❌ No match found sportify")
    return None




def replace_spaces_with_underscore(text):
    cleaned_text = text.strip()
    return cleaned_text.replace(" ", "_").replace("-", "_")



def is_boomplay_match(title, artist_name, track_name):
    title_clean = title.strip().lower()
    artist_clean = artist_name.strip().lower()
    track_clean = track_name.strip().lower()

    return (
        fuzz.partial_ratio(artist_clean, title_clean) >= 85 and
        fuzz.partial_ratio(track_clean, title_clean) >= 85
    )

def extract_isrc_and_release_date(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)


    # Search for ISRC pattern (e.g., USUM71705397)
    isrc_match = re.search(r'\b[A-Z]{2}[A-Z0-9]{3}\d{7}\b', text)
    isrc = isrc_match.group(0) if isrc_match else None

    # Search for release date (common format yyyy-mm-dd or yyyy/mm/dd)
    date_match = re.search(r'\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b', text)
    release_date = date_match.group(0).replace('/', '-') if date_match else None

    return isrc, release_date

def search_boomplay_with_google(artist_name, track_name, release_date=None, isrc=None):
    api_key = settings.GOOGLE_API_KEY
    cse_id = settings.GOOGLE_CSE_ID
    search_url = "https://www.googleapis.com/customsearch/v1"

    query = f"{artist_name} {track_name} site:boomplay.com"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 50
    }

    response = requests.get(search_url, params=params).json()
    results = response.get("items", [])

    for item in results:
        title = item.get("title", "")
        link = item.get("link", "")
        
        if is_boomplay_match(title, artist_name, track_name):
            print("🔎 Candidate found:", title)
            try:
                page = requests.get(link, timeout=5)
                page.raise_for_status()
                found_isrc, found_date = extract_isrc_and_release_date(page.text)

                # Validate ISRC if provided
                if isrc and found_isrc and found_isrc.upper() != isrc.upper():
                    print("❌ ISRC mismatch:", found_isrc, "!=", isrc)
                    continue

                # Validate release date if provided
                if release_date and found_date and found_date != release_date:
                    print("❌ Release date mismatch:", found_date, "!=", release_date)
                    continue

                print("✅ Boomplay match confirmed")
                return link
            except Exception as e:
                print("⚠️ Failed to load or parse:", link, "| Error:", str(e))
                continue

    print("❌ No valid Boomplay match found")
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

            if score > highest_score and score >= 0.75:
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
        "limit": 50,  # Fetch multiple results for filtering
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
            date_match = release_date == track_release_date 
            isrc_match =  isrc == track_isrc

            if isrc_match or date_match:
                print("✅ Exact match found based on release date and ISRC (iTunes)")
                return track['trackViewUrl']

            # Best fuzzy match fallback
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{track.get('artistName', '').lower()} {track.get('trackName', '').lower()}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score and score >= 0.75:
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



 

 