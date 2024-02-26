from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['game_id', 'winner', 'loser', 'game_mode', 'played_at']
    list_filter = ['game_mode', 'played_at']
    search_fields = ['winner__username', 'loser__username']

