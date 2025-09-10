from django.urls import path
from .views import UserListCreateView, UserDeleteView, index

urlpatterns = [
    path('', index, name='index'),
    path('api/users/', UserListCreateView.as_view(), name='user-list-create'),
    path('api/users/<int:pk>/', UserDeleteView.as_view(), name='user-delete'),
]