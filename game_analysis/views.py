from django.http import HttpResponse
from django.db import models

def home(request):
    return HttpResponse("Warzone Game Analyzer")


def ladders(request):
    return HttpResponse("Warzone Ladders")
   