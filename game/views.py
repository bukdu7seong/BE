# game/views.py
from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from user.models import AppUser
from game.models import Game
from django.utils import timezone

class GameResultView(View):
    def post(self, request):
        logged_in_user_id = '1'  # 인증과정 구현 이후에 메소드를 호출하여 로그인한 사용자의 user_id를 가져옵니다.
        return self.save(request, logged_in_user_id)
    def save(self, request, logged_in_user_id):
        try:
            player1 = AppUser.objects.get(user_id=logged_in_user_id)
            player2_nickname = request.POST.get('player2')
            player2 = AppUser.objects.get(nickname=player2_nickname) if player2_nickname else None
            winner = request.POST.get('winner')
            options = request.POST.get('options')
            game = Game(player1=player1, player2=player2, winner=winner, options=options, created_at=timezone.now())
            
            game.save()

            return JsonResponse({'message': 'Game result saved successfully'}, status=201)

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

class GameHistoryView(View):
    def get(self, request):
        logged_in_user_id = '1'  # 인증과정 구현 이후에 메소드를 호출하여 로그인한 사용자의 user_id를 가져옵니다.
        page_size = request.GET.get('pageSize', 10)
        page = request.GET.get('page', 1)

        try:
            logged_in_user = AppUser.objects.get(user_id=logged_in_user_id)
            games = Game.objects.filter(
                (Q(player1=logged_in_user) | Q(player2=logged_in_user))  # 'user1'과 'user2' 대신 'player1'과 'player2'를 사용합니다.
            ).order_by('-created_at')

            paginator = Paginator(games, page_size)
            games_page = paginator.get_page(page)

            game_list = []
            for game in games_page:
                game_info = game.player2 if game.player1 == logged_in_user else game.player1
                game_list.append({
                    'user_id': game_info.user_id,
                    'image' : game_info.image,
                    'nickname': game_info.nickname,
                    'winner': game.winner,
                    'options': game.options,
                    'created_at': game.created_at
                })

            return JsonResponse({'games': game_list}, status=200)

        except AppUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)