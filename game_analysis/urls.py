from django.urls import path

from . import views
from .models import Ladder

GAME_ANALYSIS = 'game_analysis'

ladders_list_view = views.LaddersListView.as_view(
    queryset=Ladder.objects.all(),
    context_object_name='ladders',
    template_name=GAME_ANALYSIS + '/ladders.html',
)

urlpatterns = [
    path('', views.home, name='home'),
    path('about', views.about, name='about'),
    path('ladders', ladders_list_view, name='ladders'),
    path('games/ladder/import', views.import_ladder_games, name='import_ladder_games'),
    path('sandbox', views.sandbox, name='sandbox')
]
