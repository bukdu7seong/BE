# from django.test import Client, TestCase
# from django.urls import reverse
# from user.models import AppUser
# from friend.models import Friends, FriendStatus
# from game.models import Game
# from unittest.mock import patch

# def mock_get_user_info(self, request):
#     return '1'

# class GetPendingFriendsTestCase(TestCase):
#     def setUp(self):
#         # 데이터베이스 초기화
#         Game.objects.all().delete()
#         Friends.objects.all().delete()
#         AppUser.objects.all().delete()

#         self.client = Client()

#         self.user1 = AppUser.objects.create(
#             email='user1@test.com', 
#             nickname='user1', 
#             access_token='mockToken_1', 
#             provider='google', 
#             provider_id='provider1'
#         )
#         self.user2 = AppUser.objects.create(
#             email='user2@test.com', 
#             nickname='user2', 
#             access_token='mockToken_2', 
#             provider='google', 
#             provider_id='provider2'
#         )
#         self.user3 = AppUser.objects.create(
#             email='user3@test.com', 
#             nickname='user3', 
#             access_token='mockToken_3', 
#             provider='google', 
#             provider_id='provider3'
#         )
#         self.user4 = AppUser.objects.create(
#             email='user4@test.com', 
#             nickname='user4', 
#             access_token='mockToken_4', 
#             provider='google', 
#             provider_id='provider4'
#         )
#         self.user5 = AppUser.objects.create(
#             email='user5@test.com', 
#             nickname='user5', 
#             access_token='mockToken_5', 
#             provider='google', 
#             provider_id='provider5'
#         )
#         self.user6 = AppUser.objects.create(
#             email='user6@test.com', 
#             nickname='user6', 
#             access_token='mockToken_6', 
#             provider='google', 
#             provider_id='provider6'
#         )
#         self.friend_url = reverse('friend')
        
#     def tearDown(self):
#         # 데이터베이스 정리
#         Game.objects.all().delete()
#         Friends.objects.all().delete()
#         AppUser.objects.all().delete()

    
#     @patch('friend.views.FriendView._get_logged_in_user_id', mock_get_user_info)
#     def test_get_pending_friends(self):
#         Friends.objects.create(user1=self.user2, user2=self.user1, status='PENDING')
#         Friends.objects.create(user1=self.user3, user2=self.user1, status='PENDING')
#         Friends.objects.create(user1=self.user4, user2=self.user1, status=FriendStatus.ACCEPTED)
#         request_url = self.friend_url + 'request?pending=true&pageSize=3&page=1'
#         print("Request URL: ", request_url)
#         response = self.client.get(request_url, HTTP_AUTHORIZATION=self.user1.access_token)
#         print("Response: ", response.content)
#         if response.status_code == 200:
#             print("Response: ", response.json())
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.json()['friends']), 2)
    