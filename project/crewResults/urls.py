from django.urls import path
from . import views

urlpatterns = [
    path('crewResults/', views.crewResults, name='crewResults'),
]