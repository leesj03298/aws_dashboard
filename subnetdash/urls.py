from django.urls import path
from . import views

urlpatterns = [
    path('', views.subnet_list, name='subnet_list'),
]
