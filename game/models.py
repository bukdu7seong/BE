from django.db import models
from django.contrib.auth import get_user_model

AppUser = get_user_model()

class Game(models.Model):
    GAME_MODE_CHOICES = (
        ('normal', 'Normal'),
        ('speed', 'Speed'),
        ('object', 'Object'),
    )
    winner = models.ForeignKey(AppUser, related_name='games_won', on_delete=models.CASCADE)
    loser = models.ForeignKey(AppUser, related_name='games_lost', on_delete=models.CASCADE)
    game_mode = models.CharField(max_length=100, choices=GAME_MODE_CHOICES, default='normal')
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game'
        