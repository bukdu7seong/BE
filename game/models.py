from django.db import models
from django.contrib.auth import get_user_model

AppUser = get_user_model()
class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    player1 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='player1_games')
    player2 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='player2_games')
    created_at = models.DateTimeField()
    winner = models.CharField(max_length=50)
    options = models.CharField(max_length=20)
    class Meta:
        db_table = 'game'