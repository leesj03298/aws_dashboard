# urls.py
from django.urls import path
from .views import route_table_list

urlpatterns = [
    path('', route_table_list, name='route_list'),
]
