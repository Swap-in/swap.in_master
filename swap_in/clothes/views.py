# Django
from django.shortcuts import render

# Django REST Framework
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from rest_framework.renderers import JSONRenderer

# Models
from swap_in.clothes.models import (
    like,
    Clothes,
    notification,
    Match,
    category
)
from swap_in.users.models import User

from swap_in.clothes.serializers import (
    CategorySerializer)

# Utilities
import datetime

def count_likes(clothes_id):
    """Count number of like for type"""
    
    likes = like.objects.filter(clothes_id =clothes_id, type_like = 'LIKE').count()
    superlikes = like.objects.filter(clothes_id =clothes_id, type_like = 'SUPERLIKE').count()
    dislikes = like.objects.filter(clothes_id =clothes_id, type_like = 'DISLIKE').count()

    data=[{
        "clothes_id":clothes_id,
        "LIKE":likes,
        "SUPERLIKE":superlikes,
        "DISLIKE":dislikes
    }]

    return data

@api_view(['POST'])
def create_like(request):

    new_like = like()
    new_like.clothe_id = Clothes.objects.get(id = request.data['clothe_id']) 
    new_like.user_id = User.objects.get(id = request.data['user_id']) 
    new_like.type_like = request.data['type_like']
    new_like.save()
    data=[]
    if request.data['type_like'] == 'LIKE' or request.data['type_like'] == 'SUPERLIKE':
        create_notification(new_like)
        if request.data['type_like'] == 'SUPERLIKE':
            item = search_match(new_like.user_id.id,new_like.clothe_id.user_id.id,new_like.type_like,new_like.clothe_id.id)
        else:
            item = {
                "match":False
            }
    else:        
        item = {
            "match":False
        }
        
    data.append(item)
    return Response(data,status=status.HTTP_200_OK)


def create_notification(like):
    new_notification = notification()
    new_notification.date = datetime.date.today()
    new_notification.like_id = like
    new_notification.read = False
    new_notification.send = False
    new_notification.status = 'ACTIVE'
    new_notification.save()
    

@api_view(['GET'])
def num_notification(user_id):
    num_not = notification.objects.filter(like_id__clothe_id__user_id = user_id).count()

    return Response(num_not,status=status.HTTP_200_OK)

@api_view(['GET'])
def list_notifications_by_user(self,id):
    clothes_filter = Clothes.objects.filter(user_id__id=id)
    notification_filter = notification.objects.filter(like_id__clothe_id__in = [clothes.id for clothes in clothes_filter],read = False).order_by('-date')
    data = []
    for item in notification_filter:
        item_data = {
            "user_id":item.like_id.user_id.id,
            "user_name":item.like_id.user_id.first_name + ' ' + item.like_id.user_id.last_name,
            "picture": item.like_id.user_id.picture,
            "type_like": item.like_id.type_like,
            "clothe_id": item.like_id.clothe_id.id,
            "notification_id": item.id
        }
        
        match = match_notification(item.like_id.user_id.id,id),

        item_data['is_match'] = match[0]
        if match[0]==True:
            item_data['phone_number'] =item.like_id.user_id.phone_number


        data.append(item_data)

    return Response(data,status=status.HTTP_200_OK)

def match_notification(user_id_like,user_id_clothe):
    count_like = Match.objects.filter(user_like_id = user_id_like, user_clothe_id = user_id_clothe).count()
    if count_like > 0:
        return True
    else:
        return False

@api_view(['POST'])
def notification_read(request):
    read_notification = notification.objects.get(id=request.data['notification_id'])
    read_notification.read=True
    read_notification.save()
    return Response(read_notification.id,status=status.HTTP_201_CREATED)


def search_match(like_user):
    user_id_like = like_user.user_id    # usuario que dio el like
    
    user_id_clothe = like_user.clothe_id.user_id # usuario al que se le dio like
    
    clothes_filter = Clothes.objects.filter(user_id__id=user_id_like.id) # prendas del usuario que le dio like

    likes = like.objects.filter(clothe_id__in = [clothes.id for clothes in clothes_filter],type_like='SUPERLIKE',user_id = user_id_clothe).count()
    

    if likes > 0:
        count_like = Match.objects.filter(user_like_id = user_id_like, user_clothe_id = user_id_clothe).count()
        count_clothe = Match.objects.filter(user_like_id = user_id_clothe, user_clothe_id = user_id_like).count()
        if count_like > 0 or count_clothe > 0:
            item = {
            "match" : False
            }
        else:
            new_Match = Match()
            new_Match.user_like = user_id_like
            new_Match.user_clothe = user_id_clothe
            new_Match.save()
            
            item = {
                "match" : True,
                "user_id": user_id_clothe.id,
                "picture": user_id_clothe.picture,
                "phone_number": user_id_clothe.phone_number,
                "type_like": like_user.type_like,
                "clothe_id": like_user.clothe_id.id

            }
    else:
        item = {
            "match" : False
        }

    return (item)




@api_view(['GET'])
def list_notifications_by_clothe(self,id):

    clothes_filter = Clothes.objects.get(id=id)
    like_filter = notification.objects.filter(like_id__clothe_id = clothes_filter).order_by('-date')
    data =[]
    for item in like_filter:
        item_data = {
            "user_id":item.like_id.user_id.id,
            "user_name":item.like_id.user_id.first_name + ' ' + item.like_id.user_id.last_name,
            "picture": item.like_id.user_id.picture,
            "type_like": item.like_id.type_like,
            "clothe_id": item.like_id.clothe_id.id,
            "notification_id": item.id
        }

        data.append(item_data)

    return Response(data,status=status.HTTP_200_OK)

@api_view(['GET'])
def get_categories(requests):
        list_categories = category.objects.all()
        categories = CategorySerializer(list_categories,many=True)
        return Response(categories.data,status=status.HTTP_200_OK)


@api_view(['GET'])
def search_clothes_by_category(self,id_category,id_user):
    user = User.objects.get(id = id_user)
    category_search = category.objects.get(id = id_category)
    result = Clothes.objects.filter(category_id = category_search ).exclude(user_id = user)
    data = []
    for clothes_result in result:
        item_clothe= {
            'id': clothes_result.id,
            'title': clothes_result.title,
            'description' : clothes_result.description,
            'category_id' : clothes_result.category_id.id,
            'category_description' : clothes_result.category_id.description,
            'size' : clothes_result.size,
            'gender' : clothes_result.gender,            
            'picture_1' : clothes_result.picture_1,
            'picture_2' : clothes_result.picture_2,
            'picture_3' : clothes_result.picture_3,
            'picture_4' : clothes_result.picture_4,
            'picture_5' : clothes_result.picture_5,
            'user_id' : clothes_result.user_id.id,
            'username' : clothes_result.user_id.username,
            'first_name' : clothes_result.user_id.first_name,
            'last_name' : clothes_result.user_id.last_name,
            'email' : clothes_result.user_id.email,
            'phone_number' : clothes_result.user_id.phone_number,
            'picture' : clothes_result.user_id.picture
        }

        data.append(item_clothe)
    return Response(data,status=status.HTTP_200_OK)



        


