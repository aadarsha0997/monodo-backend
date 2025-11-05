from rest_framework import serializers
from .models import HomeCart,User

class HomeImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model= HomeCart
        fields= ['id','image',"location","reviews","price","rating"]

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url)

class UserHomeSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields= ['id','user_name',"balance","phone_number"]

