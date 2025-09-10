from django.urls import path
from . import views

urlpatterns = [
    path('api/users/', views.users_list, name='users_list'),
    path('api/users/<int:user_id>/', views.user_delete, name='user_delete'),
    path('', views.index, name='index'),
]
