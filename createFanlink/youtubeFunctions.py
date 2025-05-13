import requests
from django.conf import settings
import difflib
from difflib import SequenceMatcher
import re







def get_youtube_video_link(artist_name, track_name, release_date, isrc=None): 
    api_key = settings.YOUTUBE_API_KEY
    #Convert release_date from DD/MM/YYYY to YYYY-MM-DD
    try:
        day, month, year = release_date.split("/")
        release_date_formatted = f"{year}-{month}-{day}"
        print("valid date:",release_date_formatted)

    except ValueError:
        print("Invalid release date format. Please use DD/MM/YYYY.")
        release_date_formatted = ""

    query = f"{artist_name} {track_name}"
    
    # Step 1: Search videos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 20,
        "key": api_key,
    }

    search_response = requests.get(search_url, params=search_params)
    search_data = search_response.json()

    best_match_video = None
    best_match_score = 0

    try:
        video_ids = [item['id']['videoId'] for item in search_data.get('items', []) if 'videoId' in item['id']]

        if not video_ids:
            print("No video IDs found in search results")
            return None

        # Step 2: Get full details for all found videos
        videos_url = "https://www.googleapis.com/youtube/v3/videos"
        videos_params = {
            "part": "snippet",
            "id": ",".join(video_ids),
            "key": api_key,
        }

        videos_response = requests.get(videos_url, params=videos_params)
        videos_data = videos_response.json()

        for item in videos_data.get('items', []):
            video_id = item.get('id')
            snippet = item.get('snippet', {})
            title = snippet.get('title', '')
            description = snippet.get('description', '')

            # Check for release date pattern in description
            match = re.search(r"Released on:\s*(\d{4}-\d{2}-\d{2})", description)
            description_release_date = match.group(1) if match else ""
            print("description_release_date:",description_release_date)
            # Check ISRC match
            isrc_match = isrc in title or isrc in description if isrc else True

            if description_release_date == release_date_formatted or isrc_match:
                print("Exact match found based on description release date or ISRC youtube")
                return f"https://www.youtube.com/watch?v={video_id}"

            # Fallback: check title similarity
            similarity = SequenceMatcher(None, f"{artist_name} {track_name}".lower(), title.lower()).ratio()
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_video = video_id

        if best_match_video:
            print(f"No exact match found for youtube, returning best match with score {best_match_score}")
            return f"https://www.youtube.com/watch?v={best_match_video}"

        print("No suitable video found")
        return None


    except Exception as e:
        print(f"Error occurred: {e}")
        return None



# def get_youtube_video_link(artist_name, track_name, release_date, isrc=None): 
#     api_key = settings.YOUTUBE_API_KEY
#     search_url = "https://www.googleapis.com/youtube/v3/search"
    
#     # Convert input release_date from DD/MM/YYYY to YYYY-MM-DD
#     try:
#         day, month, year = release_date.split("/")
#         release_date_formatted = f"{year}-{month}-{day}"
#     except ValueError:
#         print("Invalid release date format. Please use DD/MM/YYYY.")
#         release_date_formatted = ""
    
#     query = f"{artist_name} {track_name}"
    
#     params = {
#         "part": "snippet",
#         "q": query,
#         "type": "video",
#         "maxResults": 10,
#         "key": api_key,
#     }
    
#     response = requests.get(search_url, params=params)
#     response_data = response.json()
    
#     best_match_video = None
#     best_match_score = 0

#     try:
#         for item in response_data.get('items', []):
#             video_id = item.get('id', {}).get('videoId')
#             snippet = item.get('snippet')

#             if not video_id or not snippet:
#                 continue  # Skip items with missing data

#             video_title = snippet.get('title', '')
#             published_at = snippet.get('publishedAt', '')[:10]
#             video_description = snippet.get('description', '')

#             isrc_match = isrc in video_title or isrc in video_description if isrc else True

#             if published_at == release_date_formatted or isrc_match:
#                 print("Exact match found based on release date and ISRC")
#                 return f"https://www.youtube.com/watch?v={video_id}"
            
#             target_string = f"{artist_name} {track_name}".lower()
#             current_title = video_title.lower()
#             similarity = SequenceMatcher(None, target_string, current_title).ratio()

#             if similarity > best_match_score:
#                 best_match_score = similarity
#                 best_match_video = video_id
        
#         if best_match_video:
#             print(f"No exact match found, returning best matched title with similarity {best_match_score}")
#             return f"https://www.youtube.com/watch?v={best_match_video}"
        
#         print("No videos found")
#         return None
#     except Exception as e:
#         print(f"Error occurred: {e}")
#         return None
    
#     except (KeyError, IndexError) as e:
#         print(f"Error while processing the response: {e}")
#         return None



def get_deezer_track_link(artist_name, track_name, release_date=None, isrc=None):
    search_url = "https://api.deezer.com/search"
    
    query = f"artist:'{artist_name}' track:'{track_name}'"
    params = {
        "q": query,
        "limit": 10,
    }

    response = requests.get(search_url, params=params)
    response_data = response.json()

    try:
        best_match = None
        highest_score = 0

        for track in response_data.get('data', []):
            track_isrc = track.get('isrc')
            album = track.get('album', {})
            track_release_date = album.get('release_date')

            # Exact match
            date_match = release_date is None or release_date == track_release_date
            isrc_match = isrc is None or isrc == track_isrc

            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (Deezer)")
                return track.get('link')

            # Fuzzy match fallback
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{track.get('artist', {}).get('name', '').lower()} {track.get('title', '').lower()}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = track.get('link')

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (Deezer)")
            return best_match

        print("❌ No tracks found")
        return None

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error while processing the response: {e}")
        return None




def get_apple_music_link(artist_name, track_name, release_date=None, isrc=None):
    search_url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist_name} {track_name}",
        "media": "music",
        "limit": 10,
        "entity": "song"
    }

    response = requests.get(search_url, params=params)
    response_data = response.json()

    try:
        best_match = None
        highest_score = 0

        for result in response_data.get('results', []):
            track_release_date = result.get('releaseDate', '')[:10]
            track_isrc = result.get('isrc', '')

            date_match = release_date is None or release_date == track_release_date
            isrc_match = isrc is None or isrc == track_isrc

            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (Apple Music)")
                return result['trackViewUrl']

            # Fuzzy best match fallback
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{result.get('artistName', '').lower()} {result.get('trackName', '').lower()}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = result['trackViewUrl']

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (Apple Music)")
            return best_match

        print("❌ No tracks found")
        return None

    except (IndexError, KeyError, TypeError) as e:
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
        best_match = None
        highest_score = 0

        for item in response_data.get('items', []):
            link = item.get('link', '')
            snippet = item.get('snippet', '').lower()
            title = item.get('title', '').lower()
            
            # Check for metadata match
            date_match = release_date is None or release_date in snippet or release_date in title
            isrc_match = isrc is None or isrc.lower() in snippet or isrc.lower() in title
            
            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (Amazon Music)")
                return link

            # Fuzzy match fallback
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{title}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = link

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (Amazon Music)")
            return best_match

        print("❌ No tracks found")
        return None

    except (IndexError, KeyError, TypeError) as e:
        print(f"Error while processing the response: {e}")
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
        best_match = None
        highest_score = 0

        for item in response_data.get('items', []):
            link = item.get('link', '')
            snippet = item.get('snippet', '').lower()
            title = item.get('title', '').lower()
            
            # Match metadata if provided
            date_match = release_date is None or release_date in snippet or release_date in title
            isrc_match = isrc is None or isrc.lower() in snippet or isrc.lower() in title
            
            if date_match and isrc_match:
                print("✅ Exact match found based on release date and ISRC (TIDAL)")
                return link

            # Fallback: fuzzy matching with title
            input_combo = f"{artist_name.lower()} {track_name.lower()}"
            result_combo = f"{title}"
            score = difflib.SequenceMatcher(None, input_combo, result_combo).ratio()

            if score > highest_score:
                highest_score = score
                best_match = link

        if best_match:
            print(f"🔍 Best fuzzy match found with score {highest_score:.2f} (TIDAL)")
            return best_match

        print("❌ No tracks found")
        return None
    
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error while processing the response: {e}")
        return None
