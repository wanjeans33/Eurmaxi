"""
URL configuration for solar_app
"""
from django.urls import path
from . import views

app_name = 'solar_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('simulate/', views.simulate, name='simulate'),
    path('api/simulate/', views.api_simulate, name='api_simulate'),
]


