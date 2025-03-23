from django.urls import path
from . import views

urlpatterns = [
    path('', views.vpc_list, name='vpc_list'),
]
