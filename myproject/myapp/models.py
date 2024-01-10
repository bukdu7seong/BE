from django.db import models

# Create your models here.
from django.db import models

class AppUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    access_token = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    provider = models.CharField(max_length=50)
    provider_id = models.CharField(max_length=50)
    image = models.URLField()
    two_fact = models.BooleanField(default=False)
    nickname = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    language = models.CharField(max_length=30)

class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    player1 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='player1_games')
    player2 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='player2_games')
    created_at = models.DateTimeField()
    winner = models.CharField(max_length=50)
    options = models.CharField(max_length=20)

class Friends(models.Model):
    user1 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='friends_user1')
    user2 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='friends_user2')
    status = models.CharField(max_length=20)
