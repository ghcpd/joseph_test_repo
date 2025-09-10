from django.shortcuts import render
from rest_framework import generics, pagination
from .models import User
from .serializers import UserSerializer


def index(request):
    return render(request, 'index.html')


class UserPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    page_query_param = 'page'


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    pagination_class = UserPagination


class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
