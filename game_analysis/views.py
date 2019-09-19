import logging

from datetime import datetime
from urllib.error import URLError

from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView

from .api import get_api_token
from .calculate_game_data import calculate_game_data
from .forms import CalculateGameDataForm, ImportGameForm, ImportLadderGamesForm
from .import_games import import_game, import_ladder_games
from .models import Ladder
from .sandbox import sandbox_method

GAME_ANALYSIS = 'game_analysis'


def home(request, message=None):
    return render(
        request,
        GAME_ANALYSIS + '/home.html',
        {'date': datetime.now(), 'message': message}
    )


def about(request):
    return render(request, GAME_ANALYSIS + '/about.html')


class LaddersListView(ListView):
    model = Ladder

    def get_context_data(self, **kwargs):
        return super(LaddersListView, self).get_context_data(**kwargs)


def import_game_view(request):
    if request.method == 'POST':
        try:
            form = ImportGameForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                game_id = form.cleaned_data['game_id']

                # Get api token
                try:
                    api_token = get_api_token(email, password)
                except URLError:
                    return home(request, 'Error getting API Token')

                start_time = datetime.now()

                # Import game
                game = import_game(email, api_token, game_id)

                end_time = datetime.now()

                message = (
                    f'Imported {game}. '
                    f'Execution duration was {end_time - start_time}.'
                )

                return home(request, message)
        except URLError as e:
            logging.exception(e.reason)
            return home(request, e.reason)
    else:
        form = ImportGameForm()
    
    return render(request, GAME_ANALYSIS + '/basic_post_form.html',
        {'form_title': 'Import Game', 'form': form})


def import_ladder_games_view(request):
    if request.method == 'POST':
        try:
            form = ImportLadderGamesForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                ladder_id = form.cleaned_data['ladder_id']
                max_results = form.cleaned_data['max_results']
                offset = form.cleaned_data['offset']

                # Get api token
                try:
                    api_token = get_api_token(email, password)
                except URLError:
                    return home(request, 'Error getting API Token')

                start_time = datetime.now()

                # Import games
                count = import_ladder_games(email, api_token, ladder_id, max_results,
                    offset, 50)

                end_time = datetime.now()

                message = (
                    f'Imported {count} games out of {max_results}. '
                    f'Execution duration was {end_time - start_time}.'
                )

                return home(
                    request, message)
        except URLError as e:
            logging.exception(e.reason)
            return home(request, e.reason)
    else:
        form = ImportLadderGamesForm()
    
    return render(request, GAME_ANALYSIS + '/basic_post_form.html',
        {'form_title': 'Import Ladder Games', 'form': form})


def calculate_game_data_view(request):
    if request.method == 'POST':
        form = CalculateGameDataForm(request.POST)
        if form.is_valid():
            games_to_process = form.cleaned_data['max_results']
            batch_size = form.cleaned_data['batch_size']

            start_time = datetime.now()

            # Import games
            count = calculate_game_data(games_to_process, batch_size)

            end_time = datetime.now()

            # All games must have been handled
            all_games_processed = count < games_to_process

            message = (
                f'Calculated game data for {count} games. '
                f'There are {"no " if all_games_processed else ""} more games '
                f'to be processed. '
                f'Execution duration was {end_time - start_time}'
            )

            return home(request, message)
    else:
        form = CalculateGameDataForm()
    
    return render(request, GAME_ANALYSIS + '/basic_post_form.html',
        {'form_title': 'Calculate Game Data', 'form': form})


def sandbox(request):
    return render(request, 
        GAME_ANALYSIS + '/sandbox.html',
        {'message': sandbox_method()}
    )
