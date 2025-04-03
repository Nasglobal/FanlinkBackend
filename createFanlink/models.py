from django.db import models
from django.utils import timezone

# Create your models here.

class MediaFiles(models.Model):
  Arranger = models.CharField(max_length=255, null=True, blank=True)
  Artist = models.CharField(max_length=255,blank=True,null=True )
  ArtistURL = models.CharField(max_length=255, blank=True ,null=True)
  BPM = models.CharField(max_length=255, blank=True ,null=True)
  C_Line = models.CharField(max_length=255, blank=True ,null=True)
  Keyz = models.CharField(max_length=255, blank=True ,null=True)
  Mood = models.CharField(max_length=255, blank=True ,null=True)
  DataType = models.CharField(max_length=255,blank=True ,null=True) 
  Deleted = models.CharField(max_length=255,blank=True ,null=True)
  DisplayUPC = models.CharField(max_length=255,blank=True ,null=True)
  Download = models.CharField(max_length=255, blank=True ,null=True)
  Error = models.CharField(max_length=255, blank=True ,null=True)
  Exclusive = models.CharField(max_length=255, blank=True ,null=True)
  Genre = models.CharField(max_length=255, blank=True,null=True)
  GenreAlt = models.CharField(max_length=255, blank=True,null=True)
  GenreSub = models.CharField(max_length=255, blank=True,null=True)
  GenreSubAlt = models.CharField(max_length=255, blank=True,null=True)
  HiddenTrack = models.CharField(max_length=255, blank=True,null=True)
  ISRC = models.CharField(max_length=255, unique=False, blank=True,null=True)
  ItunesLink = models.CharField(max_length=255, blank=True,null=True)
  LabelCatalogNo = models.CharField(max_length=255, blank=True,null=True)
  LabelName = models.CharField(max_length=255, blank=True,null=True)
  Language = models.CharField(max_length=255, blank=True,null=True)
  ManufacturerUPC = models.CharField(max_length=255, blank=True,null=True)
  MasterCarveouts = models.TextField(blank=True,null=True)
  P_Line = models.CharField(max_length=255, blank=True,null=True)
  ParentalAdvisory = models.CharField(max_length=255, blank=True,null=True)
  PreviewClipDuration = models.CharField(max_length=255, blank=True,null=True)
  PreviewClipStartTime = models.CharField(max_length=255, blank=True,null=True)
  PriceBand = models.CharField(max_length=255, blank=True,null=True)
  Producer = models.CharField(max_length=255, blank=True,null=True)
  Publisher = models.CharField(max_length=255, blank=True,null=True)
  RecordingArtist = models.CharField(max_length=255, blank=True,null=True)
  ReleaseDate = models.CharField(max_length=255, blank=True,null=True)
  ReleaseName = models.CharField(max_length=255, blank=True,null=True)
  RoyaltyRate = models.CharField(max_length=255, blank=True,null=True)
  SalesEndDate = models.CharField(max_length=255, blank=True,null=True)
  SalesStartDate = models.CharField(max_length=255, blank=True,null=True)
  SongVersion = models.CharField(max_length=255, blank=True,null=True)
  Territories = models.TextField(blank=True,null=True)
  TerritoriesCarveouts = models.TextField(blank=True,null=True)
  Title = models.CharField(max_length=255,blank=True,null=True)
  TotalTracks = models.CharField(max_length=255, blank=True,null=True)
  TotalVolumes = models.CharField(max_length=255, blank=True,null=True)
  TrackDuration = models.CharField(max_length=255, blank=True,null=True)
  TrackNo = models.CharField(max_length=255, blank=True,null=True)
  VendorName = models.CharField(max_length=255, blank=True,null=True)
  VolumeNo = models.CharField(max_length=255, blank=True,null=True)
  WholesalePrice = models.CharField(max_length=255, blank=True,null=True)
  Writer = models.CharField(max_length=255, blank=True,null=True)
  zIDKey_UPCISRC = models.CharField(max_length=255, blank=True,null=True)

  class Meta:
        ordering = ['id']



class FanLinks(models.Model):
  ArtistName = models.CharField(max_length=255, null=True, blank=True)
  TrackName = models.CharField(max_length=255,blank=True,null=True )
  SpotifyLink = models.CharField(max_length=255,blank=True,null=True )
  AppleLink = models.CharField(max_length=255,blank=True,null=True )
  AmazonLink = models.CharField(max_length=255,blank=True,null=True )
  YoutubeLink = models.CharField(max_length=255,blank=True,null=True )
  ItunesLink = models.CharField(max_length=255,blank=True,null=True )
  AudiomackLink = models.CharField(max_length=255,blank=True,null=True )
  DeezerLink = models.CharField(max_length=255,blank=True,null=True )
  TidalLink = models.CharField(max_length=255,blank=True,null=True )
  Boomplay = models.CharField(max_length=255,blank=True,null=True )
  Description = models.CharField(max_length=255,blank=True,null=True )
  UPC = models.CharField(max_length=255,blank=True,null=True )
  ReleaseDate = models.CharField(max_length=255,blank=True,null=True )
  Source = models.CharField(max_length=255,blank=True,null=True )

  
  class Meta:
        ordering = ['id']



class Releases(models.Model):
  Label = models.CharField(max_length=255, null=True, blank=True)
  Artists = models.CharField(max_length=255,blank=True,null=True )
  Title = models.CharField(max_length=255,blank=True,null=True )
  UPC = models.CharField(max_length=255,blank=True,null=True )
  ReleaseDate = models.CharField(max_length=255,blank=True,null=True )
  FanlinkSent = models.CharField(max_length=255,blank=True,null=True )
  Status = models.CharField(max_length=255,blank=True,null=True )
  Y = models.CharField(max_length=255,blank=True,null=True )
  MissingLinks = models.CharField(max_length=255,blank=True,null=True )
  

  class Meta:
        ordering = ['id']

class Video(models.Model):
    file = models.FileField(upload_to="videos/")
    #processed_file = models.FileField(upload_to="processed_videos/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    splitted = models.CharField(max_length=255, blank=True,null=True,default="NO")

    class Meta:
        ordering = ['id']