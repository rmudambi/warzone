from django.urls import path
from game_analysis import views

urlpatterns = [
    path("", views.home, name="home"),
    path("ladders", views.ladders, name="ladders"),
]
