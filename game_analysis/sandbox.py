from django.db.models import Prefetch

from . import cache
from .models import *


def sandbox_method():
    map = cache.get_map(19785, True)

    return str(map)