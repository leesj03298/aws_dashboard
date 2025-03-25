from django.urls import path
from . import views

urlpatterns = [
    path('', views.targetgroup_list, name='targetgroup_list'),
]
