from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MediaFileViewset,FanLinksViewSet,ReleasesViewSet,get_fanlink,RegisterView, LoginView,ProfileView,drive_webhook,search_tracks


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
]



