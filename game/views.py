from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Game
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Q
from ts.exceptions import InvalidGameModeException, PlayerNotMatchedException

AppUser = get_user_model()

class GameResultView(APIView):
    """
    GameResultView는 게임 결과를 생성하고 업데이트하는 API 엔드포인트를 제공합니다.
    - POST 요청을 통해 새로운 게임 결과를 생성합니다. 게임의 참가자, 승자, 패자, 게임 모드를 데이터로 받아 게임 결과를 데이터베이스에 저장합니다.
    - PATCH 요청을 통해 기존 게임 결과를 업데이트합니다. 특정 게임 ID를 기반으로 게임의 두 번째 참가자를 추가하거나, 승자와 패자를 업데이트할 수 있습니다.
    - 인증된 사용자만이 게임 결과를 생성하거나 업데이트할 수 있습니다.
    - 게임 모드가 유효하지 않은 경우, InvalidGameModeException 예외를 발생시킵니다.
    - 게임 결과를 업데이트할 때, 요청자가 게임의 첫 번째 참가자와 일치하지 않으면 PlayerNotMatchedException 예외를 발생시킵니다.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        player1 = request.user
        winner_email = request.data.get('winner')
        loser_email = request.data.get('loser')
        game_mode = request.data.get('game_mode')

        try:
            # winner와 loser가 제공되었는지 확인하고, 제공된 경우 User 인스턴스를 조회
            winner = AppUser.objects.get(email=winner_email) if winner_email else None
            loser = AppUser.objects.get(email=loser_email) if loser_email else None

            if winner is None and loser is None:
                return Response({"error": "Both winner and loser are required."}, status=status.HTTP_400_BAD_REQUEST)

            if game_mode not in [choice[0] for choice in Game.GAME_MODE_CHOICES]:
                raise InvalidGameModeException()

            game = Game.objects.create(
                player1=player1,
                player2=None,  # 필요한 경우 수정
                winner=winner,
                loser=loser,
                game_mode=game_mode
            )
            game_id = game.game_id
            return Response({"message": "Game created successfully", "gameId": game_id}, status=status.HTTP_201_CREATED)
        except AppUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def patch(self, request, **kwargs):
        game_id = kwargs.get('game_id')
        player1 = request.user
        player2_email = request.data.get('player2')
        try:
            game = Game.objects.get(game_id=game_id)
            if player1 != game.player1:
                raise PlayerNotMatchedException()
            
            # player2_email을 사용하여 User 인스턴스를 조회
            player2 = None  # player2 초기화
            if player2_email:
                try:
                    player2 = AppUser.objects.get(email=player2_email)
                except AppUser.DoesNotExist:
                    return Response({"error": "Player2 is not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # player2 인스턴스를 game의 player2 필드에 할당
            game.player2 = player2

            # winner와 loser 중 null인 필드에 player2를 할당
            if game.winner is None and game.loser is not None:
                game.winner = player2
            elif game.loser is None and game.winner is not None:
                game.loser = player2

            game.save()
            return Response({"message": "Game updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class GameHistoryView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 5

    def get(self, request):
        user = request.user
        games = Game.objects.filter(Q(winner=user) | Q(loser=user)).order_by('-played_at')
        result_page = self.paginate_queryset(games, request, view=self)
        if result_page is not None:
            games_data = [{
                "id": game.game_id,
                "other": game.player2.username if game.player1 == user else game.player1.username,
                "other_img": game.player2.image.url if game.player1 == user else game.player1.image.url,
                "winner": True if game.winner == user else False,
                "game_mode": game.game_mode,
                "played_at": game.played_at.strftime('%Y-%m-%d %H:%M:%S')
            } for game in result_page]
            return self.get_paginated_response(games_data)
        else:
            return Response([], status=status.HTTP_200_OK)