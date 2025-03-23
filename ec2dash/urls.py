from django.urls import path
from . import views

urlpatterns = [
    path('', views.ec2_list, name='ec2_list'),
]
