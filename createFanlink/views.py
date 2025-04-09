from django.shortcuts import render,get_object_or_404
from django.forms.models import model_to_dict
from django.db.models import Q,Sum
from django.utils import timezone
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import subprocess
from django.db.models.functions import Trim
from PIL import Image
from django.core.files.storage import default_storage
from django.http import JsonResponse,StreamingHttpResponse,HttpResponse,FileResponse,Http404
from .models import MediaFiles,FanLinks,Releases,Video
from rest_framework import viewsets, mixins, status,pagination
from rest_framework.decorators import action,api_view,parser_classes
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
from sendfile import sendfile
from django.urls import reverse
import os
import sys
import shutil
import ffmpeg
import pandas as pd
import io
import random
import string
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
        isrc = request.data.get("isrc")
        source = request.data.get("source")
        label_name = request.data.get("label")

        artist = replace_spaces_with_underscore(artist_name)
        track = replace_spaces_with_underscore(track_name)
        
        if not artist_name or not track_name:
            return JsonResponse({"error": "Artist name and track name are required."}, status=400)
        
        track_link = get_spotify_track_link(artist_name, track_name, release_date,isrc)
        video_link = get_youtube_video_link(artist_name, track_name, release_date,isrc)
        boomplay_link = search_boomplay_with_google(artist_name, track_name, release_date,isrc)
        audiomack_link = search_audiomack_with_google(artist_name, track_name, release_date,isrc)
        itunes_link = get_itunes_track_link(artist_name, track_name, release_date,isrc)
        deezer_link = get_deezer_track_link(artist_name, track_name, release_date,isrc)
        apple_music_link = get_apple_music_link(artist_name, track_name, release_date,isrc)
        amazon_music_link = search_amazon_music_with_google(artist_name, track_name, release_date,isrc)
        tidal_link = search_tidal_with_google(artist_name, track_name, release_date,isrc)


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
                
                FanLinks(ArtistName=artist,TrackName=track,SpotifyLink=track_link,AppleLink=apple_music_link,AmazonLink=amazon_music_link,YoutubeLink=video_link,ItunesLink=itunes_link,AudiomackLink=audiomack_link,DeezerLink=deezer_link,TidalLink=tidal_link,Boomplay=boomplay_link,Description=description,UPC=isrc,ReleaseDate=release_date,Source=source).save()
            try:
                releasesList = Releases.objects.filter(Artists=artist_name,Title=track_name).first()
                if releasesList is not None:
                    releasesList.FanlinkSent = fanlink
                    releasesList.save()
                else:
                   Releases(Label=label_name,Artists=artist_name,Title=track_name,UPC=isrc,ReleaseDate="TBC",FanlinkSent=fanlink,Status="",Y="",MissingLinks="").save() 
            except Releases.DoesNotExist:
                Releases(Label=label_name,Artists=artist_name,Title=track_name,UPC=isrc,ReleaseDate="TBC",FanlinkSent=fanlink,Status="",Y="",MissingLinks="").save()
            
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
        return JsonResponse({"error": "Artist name or track name does not exist."}, status=400)


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
                            auto_generate_fanlink(row[1],row[2],row[0],row[6 ],row[4])
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
                            auto_generate_fanlink(row[1],row[2],row[0],row[6],row[4])

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

def auto_generate_fanlink(artist_name,track_name,label_name,isrc,release_date): 
    artist = replace_spaces_with_underscore(artist_name)
    track = replace_spaces_with_underscore(track_name)
    if not artist_name or not track_name:
        print("Artist name and track name are required.")
    else:   
        track_link = get_spotify_track_link(artist_name, track_name, release_date,isrc)
        video_link = get_youtube_video_link(artist_name, track_name, release_date,isrc)
        boomplay_link = search_boomplay_with_google(artist_name, track_name, release_date,isrc)
        audiomack_link = search_audiomack_with_google(artist_name, track_name, release_date,isrc)
        itunes_link = get_itunes_track_link(artist_name, track_name, release_date,isrc)
        deezer_link = get_deezer_track_link(artist_name, track_name, release_date,isrc)
        apple_music_link = get_apple_music_link(artist_name, track_name, release_date,isrc)
        amazon_music_link = search_amazon_music_with_google(artist_name, track_name, release_date,isrc)
        tidal_link = search_tidal_with_google(artist_name, track_name, release_date,isrc)

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
                FanLinks(ArtistName=artist,TrackName=track,SpotifyLink=track_link,AppleLink=apple_music_link,AmazonLink=amazon_music_link,YoutubeLink=video_link,ItunesLink=itunes_link,AudiomackLink=audiomack_link,DeezerLink=deezer_link,TidalLink=tidal_link,Boomplay=boomplay_link,Description="auto generated",UPC=isrc,ReleaseDate=release_date,Source="youtube").save()
            fanlink = f"/{artist}-{track}"
            Releases(Label=label_name,Artists=artist_name,Title=track_name,UPC=isrc,ReleaseDate="TBC",FanlinkSent=fanlink,Status="",Y="",MissingLinks="").save()




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



class UploadVideoView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES['file']
        video = Video.objects.create(file=file_obj)

        # Extract just the filename (without "videos/")
        filename = os.path.basename(video.file.name)
        #folder_name = os.path.splitext(filename)[0]

        # Generate the correct streaming URL
        video_url = request.build_absolute_uri(
            reverse("stream_video", kwargs={"filename": filename})
        )

        return Response({
            "message": "Upload successful",
            "video_id": video.id,  # Include video_id in the response
            "video_url": video_url
        })



def serve_video(request, filename):
    """Serve video with proper headers for seeking support."""
    file_path = os.path.join(settings.MEDIA_ROOT, "videos", filename)  # Adjusted path

    if not os.path.exists(file_path):
        return HttpResponse(status=404)

    # Serve the file with support for byte-range requests
    response = FileResponse(open(file_path, "rb"), content_type="video/mp4")
    response["Accept-Ranges"] = "bytes"
    
    return response


def add_watermark_to_video(input_video, output_video, watermark_image):
    """
    Adds a watermark to the given video using FFmpeg.
    """
    try:
        command = [
            "ffmpeg",
            "-i", input_video,  # Input video
            "-i", watermark_image,  # Watermark image
            "-filter_complex", "overlay=W-w-10:H-h-10",  # Position watermark at bottom-right
            "-codec:a", "copy",  # Keep original audio
            output_video
        ]
        subprocess.run(command, check=True)  # Run FFmpeg command
        return output_video  # Return watermarked video path
    except subprocess.CalledProcessError as e:
        print(f"Error adding watermark: {e}")
        return None  # Return None if an error occurs




@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser])
def trim_video(request):
    try:
        video_id = request.data.get("video_id")
        start_time = float(request.data.get("start_time", 0))
        end_time = float(request.data.get("end_time", 0))
        watermark_file = request.FILES.get("watermark_image")
        watermark_temp_path = None
        

        if not video_id or start_time < 0 or end_time <= start_time:
            return JsonResponse({"error": "Invalid input data"}, status=400)

        # Get video from DB
        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return JsonResponse({"error": "Video not found"}, status=404)

        input_video = os.path.join(settings.MEDIA_ROOT, str(video.file))
        video_name = os.path.splitext(os.path.basename(input_video))[0]
        trimmed_filename = f"{video_name}_trimmed.mp4"
        trimmed_path = os.path.join(settings.MEDIA_ROOT, "trimmed", trimmed_filename)
        watermarked_path = os.path.join(settings.MEDIA_ROOT, "trimmed", f"watermarked_{trimmed_filename}")
        

        # Remove old versions if they exist
        if os.path.exists(trimmed_path):
            os.remove(trimmed_path)
        if os.path.exists(watermarked_path):
            os.remove(watermarked_path)

        # Trim the video using FFmpeg
        subprocess.run([
            "ffmpeg", "-i", input_video, "-ss", str(start_time), "-to", str(end_time),
            "-c", "copy", trimmed_path
        ], check=True)

        # Handle uploaded watermark image
        if watermark_file:
            filename_base = os.path.splitext(watermark_file.name)[0]
            watermark_temp_path = os.path.join(settings.MEDIA_ROOT, f"resized_{filename_base}.jpg")
            img = Image.open(watermark_file)
            if img.mode in ("RGBA", "P"):
               img = img.convert("RGB")  # Convert to RGB to remove alpha

            img = img.resize((120, 80))
            img.save(watermark_temp_path, "JPEG")

            # Watermark the trimmed video
            subprocess.run([
                "ffmpeg", "-i", trimmed_path, "-i", watermark_temp_path,
                "-filter_complex", "overlay=W-w-10:H-h-10", "-codec:a", "copy", watermarked_path
            ], check=True)

            os.remove(trimmed_path)  # Delete the trimmed version
            os.remove(watermark_temp_path)  # Delete temp watermark image
        else:
            watermark_image = os.path.join(settings.MEDIA_ROOT, "Africha_Entertainment.png")
            watermarked_video = add_watermark_to_video(trimmed_path, watermarked_path, watermark_image)
            if watermarked_video:
               os.remove(trimmed_path)  # Remove original trimmed video

        # Return final video URL
        trimmed_video_url = request.build_absolute_uri(settings.MEDIA_URL + "trimmed/" + os.path.basename(watermarked_path))

        return JsonResponse({
            "message": "Video trimmed and watermarked successfully",
            "trimmed_video_url": trimmed_video_url
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def download_trimmed_video(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, "trimmed", filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), content_type="video/mp4")
    else:
        raise Http404("Video not found")

@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser])
def split_video(request):
    video_id = request.data.get("video_id")
    duration = int(request.data.get("duration", 15))
    watermark_file = request.FILES.get("watermark_image")
    watermark_temp_path = ""
    
        

    try:
        video = Video.objects.get(id=video_id)
        video_path = os.path.join(settings.MEDIA_ROOT, str(video.file))
       
        if watermark_file: 
            # Save watermark temporarily
            filename_base = os.path.splitext(watermark_file.name)[0]
            watermark_temp_path = os.path.join(settings.MEDIA_ROOT, f"resized_{filename_base}.jpg")
            img = Image.open(watermark_file)
            if img.mode in ("RGBA", "P"):
               img = img.convert("RGB")  # Convert to RGB to remove alpha

            img = img.resize((120, 80))
            img.save(watermark_temp_path, "JPEG")

        # Create output folder
        folder_name = os.path.splitext(os.path.basename(video_path))[0]
        output_folder = os.path.join(settings.MEDIA_ROOT, "splitted_videos", folder_name)
        if os.path.exists(output_folder):
            random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=3))
            folder_name += random_chars
            output_folder = os.path.join(settings.MEDIA_ROOT, "splitted_videos", folder_name)

        os.makedirs(output_folder, exist_ok=True)

        # Get total duration
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        total_duration = float(result.stdout.strip())

        # Split and watermark
        part = 1
        start_time = 0
        while start_time < total_duration:
            temp_file = os.path.join(output_folder, f"temp_part{part}.mp4")
            output_file = os.path.join(output_folder, f"{folder_name}_part{part}.mp4")

            # Split the video
            subprocess.run([
                "ffmpeg", "-i", video_path, "-ss", str(start_time), "-t", str(duration),
                "-c", "copy", temp_file
            ], check=True)
            
            if watermark_file :
                # Add watermark if uploaded
                subprocess.run([
                    "ffmpeg", "-i", temp_file, "-i", watermark_temp_path,
                    "-filter_complex", "overlay=W-w-10:H-h-10", "-codec:a", "copy", output_file
                ], check=True)
                os.remove(temp_file)
            else : 
                # add water mark if not uploaded
                watermark_image = os.path.join(settings.MEDIA_ROOT, "Africha_Entertainment.png")
                watermarked_video = add_watermark_to_video(temp_file, output_file, watermark_image)
                if watermarked_video:
                  os.remove(temp_file)  # Delete temp file after watermarking

            start_time += duration
            part += 1

        # Clean up watermark image
        if watermark_file :
            if os.path.exists(watermark_temp_path):
                os.remove(watermark_temp_path)

        video.splitted = "Yes"
        video.save()

        return JsonResponse({
            "message": "Video split and watermarked successfully",
            "download_url": folder_name
        })

    except Video.DoesNotExist:
        return JsonResponse({"error": f"Video not found: id = {video_id}"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def download_split_folder(request, folder_name):
    folder_path = os.path.join(settings.MEDIA_ROOT, "splitted_videos", folder_name)
    zip_path = f"{folder_path}.zip"
    
    if not os.path.exists(folder_path):
        return JsonResponse({"error": "Folder not found"}, status=404)
    
    # Zip the folder
    shutil.make_archive(folder_path, 'zip', folder_path)
    return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=f"{folder_name}.zip")


@csrf_exempt
def get_uploaded_videos(request):
    videos = Video.objects.all()
    video_list = [
        {
            "id": video.id,
            "name": os.path.basename(video.file.name),  # Extracts video file name
            "file_url": request.build_absolute_uri(settings.MEDIA_URL + str(video.file)),
            "uploaded_at": video.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "splitted": video.splitted
        }
        for video in videos
    ]
    return JsonResponse({"videos": video_list}, safe=False)



@csrf_exempt
def delete_video(request, video_id):
    if request.method == "DELETE":
        video = get_object_or_404(Video, id=video_id)

        # Delete the video file from storage
        if video.file:
            trimmed_filename = f"{video_id}_trimmed.mp4"
            splitted_folder = os.path.splitext(os.path.basename(video.file.name))[0]
            zipfile = f"{splitted_folder}.zip"
            split_folder_path = os.path.join(settings.MEDIA_ROOT, "splitted_videos", splitted_folder)
            zipfile_path = os.path.join(settings.MEDIA_ROOT, "splitted_videos", zipfile)
            trim_video_path = os.path.join(settings.MEDIA_ROOT, "trimmed", trimmed_filename)
            video_path = video.file.path  # Absolute path of the video file
            if os.path.exists(video_path):
                os.remove(video_path)  
            if os.path.exists(zipfile_path):
                os.remove(zipfile_path)
            if os.path.exists(trim_video_path):
                os.remove(trim_video_path)  
            if os.path.exists(split_folder_path):
                shutil.rmtree(split_folder_path)
                 

        # Delete from database
        video.delete()
        
        return JsonResponse({"message": "Video deleted successfully"}, status=200)

    return JsonResponse({"error": "Invalid request"}, status=400)
