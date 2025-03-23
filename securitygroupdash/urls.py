from django.urls import path
from .views import securitygroup_list

urlpatterns = [
    path('', securitygroup_list, name='securitygroup_list'),
]
