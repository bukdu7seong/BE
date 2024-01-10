# myproject/myapp/models/__init__.py
from .appuser import AppUser
from .game import Game
from .friends import Friends

__all__ = ['AppUser', 'Game', 'Friends']