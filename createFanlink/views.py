from django.shortcuts import render,get_object_or_404
from django.forms.models import model_to_dict
from django.db.models import Q,Sum
from django.utils import timezone
from django.conf import settings
from django.db.models.functions import Trim
from django.core.files.storage import default_storage
from django.http import JsonResponse,StreamingHttpResponse,HttpResponse
from .models import MediaFiles,FanLinks,Releases
from rest_framework import viewsets, mixins, status,pagination
from rest_framework.decorators import action,api_view
from .serializers import MediaFilesSerializers,FanlinksSerializers,ReleasesSerializers
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import IsAuthenticated
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
from .utils import fetch_sheet_data,get_last_updated_row,get_google_credentials
import os
import sys
import shutil
import pandas as pd
import io
import requests
from datetime import datetime
from .spotifyFunctions import get_spotify_track_link,replace_spaces_with_underscore,search_boomplay_with_google,search_audiomack_with_google,get_itunes_track_link
from .youtubeFunctions import get_youtube_video_link,get_deezer_track_link,get_apple_music_link,search_amazon_music_with_google,search_tidal_with_google

# Global variable to store previously fetched rows
previous_rows = []

class CustomPagination(pagination.PageNumberPagination):
    page_size = 50  # Number of records per page
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_size(self, request):
        page_size = request.query_params.get('page_size') or self.page_size
        return min(int(page_size), self.max_page_size)

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        return Response({
            'total_items': total_items,
            'page_number': self.page.number,
            'page_size': self.page.paginator.per_page,
            'results': data
        })

# Create your views here.

class MediaFileViewset(viewsets.ModelViewSet):
  queryset = MediaFiles.objects.filter(DataType='Track').order_by('id')
  serializer_class = MediaFilesSerializers
  pagination_class = CustomPagination  # Use the custom pagination class 
 
  def get_queryset(self):
      min_id = self.request.query_params.get('min_id')
      max_id = self.request.query_params.get('max_id')

      queryset = MediaFiles.objects.filter(DataType='Track').order_by('id')

      if min_id:
          queryset = queryset.filter(id__gte=min_id)

      if max_id:
          queryset = queryset.filter(id__lte=max_id)
      
      return queryset

class FanLinksViewSet(viewsets.ModelViewSet):
    queryset = FanLinks.objects.all()
    serializer_class = FanlinksSerializers
    pagination_class = CustomPagination


    @action(detail=False, methods=["POST"]) #convert this to endpoint
    def create_fanlink(self, request, *args, **kwargs):
        artist_name = request.data.get("artist")
        track_name = request.data.get("track")
        description = request.data.get("description")
        release_date = request.data.get("releaseDate")
        upc = request.data.get("upc")
        source = request.data.get("source")
        label_name = request.data.get("label")

        artist = replace_spaces_with_underscore(artist_name)
        track = replace_spaces_with_underscore(track_name)
        
        if not artist_name or not track_name:
            return JsonResponse({"error": "Artist name and track name are required."}, status=400)
        
        track_link = get_spotify_track_link(artist_name, track_name)
        video_link = get_youtube_video_link(artist_name, track_name)
        boomplay_link = search_boomplay_with_google(artist_name, track_name)
        audiomack_link = search_audiomack_with_google(artist_name, track_name)
        itunes_link = get_itunes_track_link(artist_name, track_name)
        deezer_link = get_deezer_track_link(artist_name, track_name)
        apple_music_link = get_apple_music_link(artist_name, track_name)
        amazon_music_link = search_amazon_music_with_google(artist_name, track_name)
        tidal_link = search_tidal_with_google(artist_name, track_name)

        
        if track_link or video_link or boomplay_link or audiomack_link or itunes_link or deezer_link or apple_music_link or amazon_music_link or tidal_link:
            fanlink = f"/{artist}-{track}"
            try:
               check_fan_links = FanLinks.objects.get(ArtistName=artist,TrackName=track)
               check_fan_links.SpotifyLink = track_link
               check_fan_links.YoutubeLink = video_link
               check_fan_links.Boomplay = boomplay_link
               check_fan_links.AudiomackLink = audiomack_link
               check_fan_links.ItunesLink = itunes_link
               check_fan_links.DeezerLink = deezer_link
               check_fan_links.AppleLink = apple_music_link
               check_fan_links.AmazonLink = amazon_music_link
               check_fan_links.TidalLink = tidal_link
               check_fan_links.Source = source
               check_fan_links.save()
               
            except FanLinks.DoesNotExist:
                FanLinks(ArtistName=artist,TrackName=track,SpotifyLink=track_link,AppleLink=apple_music_link,AmazonLink=amazon_music_link,YoutubeLink=video_link,ItunesLink=itunes_link,AudiomackLink=audiomack_link,DeezerLink=deezer_link,TidalLink=tidal_link,Boomplay=boomplay_link,Description=description,UPC=upc,ReleaseDate=release_date,Source=source).save()
            try:
                releasesList = Releases.objects.filter(Artists=artist_name,Title=track_name).first()
                if releasesList is not None:
                    releasesList.FanlinkSent = fanlink
                    releasesList.save()
                else:
                   Releases(Label=label_name,Artists=artist_name,Title=track_name,UPC=upc,ReleaseDate="TBC",FanlinkSent=fanlink,Status="",Y="",MissingLinks="").save() 
            except Releases.DoesNotExist:
                Releases(Label=label_name,Artists=artist_name,Title=track_name,UPC=upc,ReleaseDate="TBC",FanlinkSent=fanlink,Status="",Y="",MissingLinks="").save()
            
            return JsonResponse({"link": fanlink})
        else:
            return JsonResponse({"error": "Track not found."}, status=404)


class ReleasesViewSet(viewsets.ModelViewSet):
    queryset = Releases.objects.all().order_by('id')
    serializer_class = ReleasesSerializers
    pagination_class = CustomPagination

    @action(detail=False, methods=["POST"]) #convert this to endpoint
    def upload_releases(self, request, *args, **kvargs):
        releases = request.FILES.get('releases')
        csv_data = releases.read()
        new_data_frame = pd.read_excel(csv_data)
        relevant_columns = [
            'Label', 'Artists', 'Title', 
            'UPC', 'ReleaseDate', 'FanlinkSent', 
            'Status', 'Y', 'MissingLinks'
        ]
        new_data_frame = new_data_frame[relevant_columns]
        for _, row in new_data_frame.iterrows():
          artist_name = row['Artists']
          track_name = row['Title']
          
          if Releases.objects.filter(Artists__iexact=artist_name,Title__iexact=track_name).exists():
              print("track name exist already : ", track_name)
              # Skip existing rows
              continue
          else:
              # Replace NaN with empty string
              cleaned_row = row.where(pd.notna(row), '')
              # Convert row to dictionary
              row_dict = cleaned_row.to_dict()
              # Create the new record
              Releases.objects.create(**row_dict)  

        return JsonResponse({'message': "Releases upload successful"})



class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Generate token for the user
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User created successfully",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            # Find the user by email
            user = User.objects.get(email=email)
            # Verify the hashed password
            if check_password(password, user.password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
        }, status=status.HTTP_200_OK)


@csrf_exempt
def get_fanlink(request,track,artist):
      try:
        all_fan_links = FanLinks.objects.get(ArtistName=artist,TrackName=track)
        if not all_fan_links:
          return JsonResponse({"error": "No fan link available."}, status=400)    
        else:
         res = {
          "spotifyLink" : all_fan_links.SpotifyLink,
          "appleLink" : all_fan_links.AppleLink,
          "amazonLink" : all_fan_links.AmazonLink,
          "youtubeLink" : all_fan_links.YoutubeLink,
          "itunesLink" : all_fan_links.ItunesLink,
          "audiomackLink" : all_fan_links.AudiomackLink,
          "deezerLink" : all_fan_links.DeezerLink,
          "tidalLink" : all_fan_links.TidalLink,
          "boomplay" : all_fan_links.Boomplay,
          "source" : all_fan_links.Source,
          "upc" : all_fan_links.UPC,
         }
        return JsonResponse({'data': res })
      except FanLinks.DoesNotExist:
        return JsonResponse({"error": "Artist name and track name are required."}, status=400)


@csrf_exempt
def drive_webhook(request):
    """Handle incoming webhook notifications from Google Drive."""
    global previous_rows
    spreadsheet_id = "16dMltfMyyl8WAEDy9ZRxu3kLpFYUNb7ktMB5SGSV8EY"
    range_name = "Sheet1!A1:Z1000"
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            try:
                # Parse the JSON body
                notification = json.loads(request.body)
                print("Webhook triggered with JSON body:", notification)
                current_rows = fetch_sheet_data(spreadsheet_id, range_name)

                # Detect newly added rows
                if not previous_rows:
                    previous_rows = current_rows  # Initialize if empty
                    print("Initialized previous rows.")
                else:
                    new_rows = current_rows[len(previous_rows):]
                    if new_rows:
                        print("Newly added rows:")
                        for row in new_rows:
                            print(row)
                            auto_generate_fanlink(row[1],row[2],row[0],row[3],row[4])
                    previous_rows = current_rows
                return JsonResponse({"message": "Notification received successfully."}, status=200)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON data"}, status=400)
        elif content_type == 'text/plain' and request.body == b'':
            try:
                current_rows = get_last_updated_row(spreadsheet_id, range_name)
                # Detect newly added rows
                if not previous_rows:
                    previous_rows = current_rows  # Initialize if empty
                else:
                    new_rows = current_rows[len(previous_rows):]
                    if new_rows:
                        for row in new_rows:
                            print(row)
                            auto_generate_fanlink(row[1],row[2],row[0],row[3],row[4])

                    # Update the stored rows
                    previous_rows = current_rows

                return JsonResponse(
                    {"message": "Notification processed", "last_row": current_rows},
                    status=200,
                )
            except Exception as e:
                print("Error querying Google Sheets API:", str(e))
                return JsonResponse({"error": str(e)}, status=500)
        
            return JsonResponse({"message": "Notification received with no body."}, status=200)

    return HttpResponse("Invalid request", status=400)

def auto_generate_fanlink(artist_name,track_name,label_name,upc,release_date): 
    artist = replace_spaces_with_underscore(artist_name)
    track = replace_spaces_with_underscore(track_name)
    if not artist_name or not track_name:
        print("Artist name and track name are required.")
    else:   
        track_link = get_spotify_track_link(artist_name, track_name)
        video_link = get_youtube_video_link(artist_name, track_name)
        boomplay_link = search_boomplay_with_google(artist_name, track_name)
        audiomack_link = search_audiomack_with_google(artist_name, track_name)
        itunes_link = get_itunes_track_link(artist_name, track_name)
        deezer_link = get_deezer_track_link(artist_name, track_name)
        apple_music_link = get_apple_music_link(artist_name, track_name)
        amazon_music_link = search_amazon_music_with_google(artist_name, track_name)
        tidal_link = search_tidal_with_google(artist_name, track_name)

        if track_link or video_link or boomplay_link or audiomack_link or itunes_link or deezer_link or apple_music_link or amazon_music_link or tidal_link:
            try:
               check_fan_links = FanLinks.objects.get(ArtistName=artist,TrackName=track)
               check_fan_links.SpotifyLink = track_link
               check_fan_links.YoutubeLink = video_link
               check_fan_links.Boomplay = boomplay_link
               check_fan_links.AudiomackLink = audiomack_link
               check_fan_links.ItunesLink = itunes_link
               check_fan_links.DeezerLink = deezer_link
               check_fan_links.AppleLink = apple_music_link
               check_fan_links.AmazonLink = amazon_music_link
               check_fan_links.TidalLink = tidal_link
               check_fan_links.save()
            except FanLinks.DoesNotExist:
                FanLinks(ArtistName=artist,TrackName=track,SpotifyLink=track_link,AppleLink=apple_music_link,AmazonLink=amazon_music_link,YoutubeLink=video_link,ItunesLink=itunes_link,AudiomackLink=audiomack_link,DeezerLink=deezer_link,TidalLink=tidal_link,Boomplay=boomplay_link,Description="auto generated",UPC=upc,ReleaseDate=release_date,Source="youtube").save()
            fanlink = f"/{artist}-{track}"
            Releases(Label=label_name,Artists=artist_name,Title=track_name,UPC=upc,ReleaseDate="TBC",FanlinkSent=fanlink,Status="",Y="",MissingLinks="").save()




@csrf_exempt
def search_tracks(request):
    query = request.GET.get("query", "")
    if not query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        #"q": f"{query} site:spotify.com",
        "q": f"{query} music artist",
        "key": settings.GOOGLE_API_KEY,  # Your Google API key
        "cx": settings.GOOGLE_CSE_ID,  # Your Custom Search Engine ID
        #"siteSearch": "youtube.com,spotify.com,boomplay.com,music.amazon.com,audiomack.com",
    }


    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract titles from the API response
        track_names = []
        if "items" in data:
            track_names = [item.get("title", "Unknown Track") for item in data["items"]]

        return JsonResponse({"tracks": track_names}, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)

# @csrf_exempt
# def search_tracks(request):
#     query = request.GET.get("query", "")
#     if not query:
#         return JsonResponse({"error": "Query parameter is required"}, status=400)

#     refined_query = f"{query} artist music"
#     url = "https://www.googleapis.com/customsearch/v1"
#     params = {
#         "q": refined_query,
#         "key": settings.GOOGLE_API_KEY,  # Your Google API key
#         "cx": settings.GOOGLE_CSE_ID,  # Your Custom Search Engine ID
#     }

#     try:
#         response = requests.get(url, params=params)
#         response.raise_for_status()
#         data = response.json()

#         # Extract artist names from search results
#         artist_names = []
#         if "items" in data:
#             for item in data["items"]:
#                 title = item.get("title", "")

#                 # Extract potential artist name using regex or keywords
#                 match = re.search(r"(?P<artist>.+?) - (?:Music|Song|Track|Artist|Album)", title, re.IGNORECASE)
#                 if match:
#                     artist_names.append(match.group("artist"))
#                 else:
#                     # Fallback: Take the full title if no pattern matches
#                     artist_names.append(title)

#         # Remove duplicates and return as a JSON response
#         artist_names = list(set(artist_names))  # Avoid duplicates
#         return JsonResponse({"artists": artist_names}, safe=False)

#     except requests.exceptions.RequestException as e:
#         return JsonResponse({"error": str(e)}, status=500)
