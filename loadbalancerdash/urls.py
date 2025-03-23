from django.urls import path
from . import views

urlpatterns = [
    path('', views.loadbalancer_list, name='loadbalancer_list'),
]
