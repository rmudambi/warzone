from django.db.models import Prefetch

from .models import *


def sandbox_method():
#     territories_and_connections = TerritoryConnection.objects.select_related('territory')
# #     bonuses_and_territories = Bonus.objects.prefetch_related('bonusterritory_set')
    
#     map = Map.objects.prefetch_related(
#         Prefetch('territory_set', queryset=territories_and_connections)
#     ).get(pk=19785)

    map = Map.objects.prefetch_related(
        'territory_set'
    ).get(pk=19785)


    return str(map)