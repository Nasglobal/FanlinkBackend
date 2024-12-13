from rest_framework import serializers
from .models import MediaFiles,FanLinks,Releases


class MediaFilesSerializers(serializers.ModelSerializer):
  class Meta:
    model = MediaFiles
    fields = '__all__'

class FanlinksSerializers(serializers.ModelSerializer):
  class Meta:
    model = FanLinks
    fields = '__all__'

class ReleasesSerializers(serializers.ModelSerializer):
  class Meta:
    model = Releases
    fields = '__all__'