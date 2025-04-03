from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MediaFileViewset,FanLinksViewSet,ReleasesViewSet,get_fanlink,RegisterView, LoginView,ProfileView,drive_webhook,search_tracks,UploadVideoView, trim_video, serve_video,download_split_folder,split_video,get_uploaded_videos,delete_video


router = DefaultRouter()
router.register('media-files', MediaFileViewset, basename = 'media-files')
router.register('fanlinks', FanLinksViewSet, basename = 'fanlinks')
router.register(r'create-fanlink', FanLinksViewSet, basename = 'create_fanlink')
router.register('releases', ReleasesViewSet, basename = 'releases')
router.register(r'releases', ReleasesViewSet, basename = 'upload_releases')


urlpatterns = [
    path('api/', include(router.urls)),
    path('get-fanlink/<str:track>/<str:artist>', get_fanlink, name='get_fanlink'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('webhook-endpoint', drive_webhook, name='drive_webhook'), 
    path("api/search-tracks/", search_tracks, name="search_tracks"), 
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('upload/', UploadVideoView.as_view(), name='upload_video'),
    path('trim-video/', trim_video, name='trim_video'),
    path("stream/videos/<str:filename>/", serve_video, name="stream_video"),
    path("split-video/", split_video, name="split_video"),  
    path("download-split-folder/<str:folder_name>/", download_split_folder, name="download_split_folder"), 
    path("videos/", get_uploaded_videos, name="uploaded-videos"),
    path('delete-video/<int:video_id>/', delete_video, name='delete_video'),
]



