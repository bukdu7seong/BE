from django.db import models

from myapp.models.appuser import AppUser
from myapp.models.game import Game
from myapp.models.friends import Friends

__all__ = [
    'AppUser',
    'Game',
    'Friends'
]