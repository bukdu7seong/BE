from django.test import TestCase, Client
from django.urls import reverse
from user.models import AppUser
from game.models import Game
from django.utils import timezone

# game/tests.py
class GameResultViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # 테스트 유저 생성
        self.users = [
            AppUser.objects.create(
                user_id=i,
                access_token=f"test_token_{i}",
                email=f"test{i}@example.com",
                provider="google",
                provider_id=f"google_{i}",
                nickname=f"User{i}",
            )
            for i in range(1, 11)
        ]

    # game/tests.py
    def test_game_result(self):
        # 게임 결과 저장 요청
        response = self.client.post(reverse('game_result'), {
            'player2': self.users[1].nickname,
            'winner': self.users[1].nickname,
            'options': 'test'
        })

        # 응답 상태 코드 확인
        self.assertEqual(response.status_code, 201)

        # 응답 메시지 확인
        data = response.json()
        self.assertEqual(data['message'], 'Game result saved successfully')

        # 데이터베이스에 게임 결과가 저장되었는지 확인
        self.assertEqual(len(Game.objects.filter(player1=self.users[0])), 1)

# class GameViewTest(TestCase):
#     def setUp(self):
#         self.client = Client()

#         # 테스트 유저 생성
#         self.users = [
#             AppUser.objects.create(
#                 user_id=i,
#                 access_token=f"test_token_{i}",
#                 email=f"test{i}@example.com",
#                 provider="google",
#                 provider_id=f"google_{i}",
#                 nickname=f"User{i}",
#             )
#             for i in range(1, 11)
#         ]

#         # 테스트 게임 데이터 생성
#         self.games = [
#             Game.objects.create(
#                 game_id=i,
#                 player1=self.users[(i + 1) % 10],
#                 player2=self.users[0],
#                 winner=self.users[i % 10].nickname,
#                 created_at=timezone.now(),
#                 options="test",
#             ) 
#             for i in range(1, 11)
#         ]

#     def test_game_history(self):
#         response = self.client.get(reverse('game_history'), {'pageSize': 5, 'page': 1})
#         self.assertEqual(response.status_code, 200)

#         data = response.json()
#         self.assertEqual(len(data['games']), 5)