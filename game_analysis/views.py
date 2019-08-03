from datetime import datetime

from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView

from .models import Ladder
from .forms import ImportLadderGamesForm

GAME_ANALYSIS = 'game_analysis'

def home(request):
    return render(
        request,
        GAME_ANALYSIS + '/home.html',
        {
            'date': datetime.now()
        }
    )


def about(request):
    return render(request, GAME_ANALYSIS + '/about.html')


class LaddersListView(ListView):
    model = Ladder

    def get_context_data(self, **kwargs):
        return super(LaddersListView, self).get_context_data(**kwargs)


def import_ladder_games(request):
    if request.method == 'POST':
        form = ImportLadderGamesForm(request.POST)
        if form.is_valid():
            # todo import games
            return home(request)
    else:
        form = ImportLadderGamesForm()
    
    return render(request, GAME_ANALYSIS + '/import_ladder_games.html', {'form': form})