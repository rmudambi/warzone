from datetime import datetime

from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView

from . import api, import_games
from .models import Ladder
from .forms import ImportLadderGamesForm

GAME_ANALYSIS = 'game_analysis'

def home(request, message=None):
    return render(
        request,
        GAME_ANALYSIS + '/home.html',
        {
            'date': datetime.now(),
            'message': message
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
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            ladder_id = form.cleaned_data['ladder_id']
            max_results = form.cleaned_data['max_results']
            offset = form.cleaned_data['offset']
            halt_if_exists = form.cleaned_data['halt_if_exists']

            # Get api token
            api_token = api.get_api_token(email, password)

            start_time = datetime.now()

            # Import games
            count = import_games.import_ladder_games(email, api_token, ladder_id, max_results, offset, 50, 
                    halt_if_exists)

            end_time = datetime.now()

            message = f'Imported {str(count)} games out of {max_results}. Execution duration was {str(end_time - start_time)}'

            return home(request, message)
    else:
        form = ImportLadderGamesForm()
    
    return render(request, GAME_ANALYSIS + '/import_ladder_games.html', {'form': form})