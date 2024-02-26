from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Game
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

AppUser = get_user_model()

class GameResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        player1 = request.data.get('player1')
        winner = request.data.get('winner')
        loser = request.data.get('loser')
        game_mode = request.data.get('game_mode')

        try:
            if winner is None and loser is None:
                return Response({"error": "Winner and loser are required."}, status=status.HTTP_400_BAD_REQUEST)
            if game_mode not in [choice[0] for choice in Game.GAME_MODE_CHOICES]:
                return Response({"error": "Invalid game mode."}, status=status.HTTP_400_BAD_REQUEST)

            game = Game.objects.create(
                player1=player1,
                player2=None,
                winner=winner,
                loser=loser,
                game_mode=game_mode
            )
            game.save()
            game_id = game.id
            return Response({"message": "Game created successfully", "gameId": game_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class GameHistoryView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 5  # 페이지 당 항목 수를 설정합니다. 필요에 따라 조정하세요.

    def get(self, request):
        user = request.user
        games = Game.objects.filter(Q(winner=user) | Q(loser=user)).order_by('-played_at')
        result_page = self.paginate_queryset(games, request, view=self)
        if result_page is not None:
            games_data = [{
                "id": game.id,
                "winner": game.winner.username,
                "loser": game.loser.username,
                "game_mode": game.game_mode,
                "played_at": game.played_at.strftime('%Y-%m-%d %H:%M:%S')  # 날짜 형식을 문자열로 변환
            } for game in result_page]
            return self.get_paginated_response(games_data)
        else:
            return Response([], status=status.HTTP_200_OK)