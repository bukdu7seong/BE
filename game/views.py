from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Game
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

AppUser = get_user_model()

class GameResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        winner_username = request.data.get('winner')
        loser_username = request.data.get('loser')
        game_mode = request.data.get('game_mode')

        try:
            winner = AppUser.objects.get(username=winner_username)
            loser = AppUser.objects.get(username=loser_username)

            if game_mode not in [choice[0] for choice in Game.GAME_MODE_CHOICES]:
                return Response({"error": "Invalid game mode."}, status=status.HTTP_400_BAD_REQUEST)

            game = Game.objects.create(
                winner=winner,
                loser=loser,
                game_mode=game_mode
            )
            game.save()

            return Response({"message": "Game result saved successfully."}, status=status.HTTP_201_CREATED)
        except AppUser.DoesNotExist:
            return Response({"error": "One of the players does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Game
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

AppUser = get_user_model()

class GameHistoryView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        games = Game.objects.filter(models.Q(winner=user) | models.Q(loser=user)).order_by('-played_at')
        result_page = self.paginate_queryset(games, request, view=self)
        games_data = [{
            "id": game.id,
            "winner": game.winner.username,
            "loser": game.loser.username,
            "game_mode": game.game_mode,
            "played_at": game.played_at
        } for game in result_page]
        return self.get_paginated_response(games_data)