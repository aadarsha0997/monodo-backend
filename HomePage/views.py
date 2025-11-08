# from django.shortcuts import render
# from rest_framework.decorators import api_view
# from rest_framework.response import Response


# # models

# from .models import User,HomeCart

# #serializer
# from .serializer import HomeImageSerializer,UserHomeSerializer

# # Create your views here.

# @api_view(['GET'])
# def HomePage(request):
#     # user_detail=User.objects.get(id=id)  
#     data = {
        
#         "Kathmandu": HomeImageSerializer(HomeCart.objects.filter(location="Kathmandu"), many=True, context={'request': request}).data,
#         "Pokhara": HomeImageSerializer(HomeCart.objects.filter(location="Pokhara"), many=True, context={'request': request}).data,
#         "Tokyo": HomeImageSerializer(HomeCart.objects.filter(location="Tokyo"), many=True, context={'request': request}).data,
#     }
#     return Response(data)
