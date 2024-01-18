# from django.test import Client, TestCase
# from django.urls import reverse
# from user.models import AppUser
# from friend.models import Friends, FriendStatus
# from game.models import Game

# class GetApprovedListTestCase(TestCase):
#     def setUp(self):
#         # 데이터베이스 초기화
#         Game.objects.all().delete()
#         Friends.objects.all().delete()
#         AppUser.objects.all().delete()

#         self.client = Client()
#         self.create_users()
#         self.friend_url = reverse('friend')

#     def tearDown(self):
#         # 데이터베이스 정리
#         Game.objects.all().delete()
#         Friends.objects.all().delete()
#         AppUser.objects.all().delete()

#     def create_users(self):
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

#     def test_get_approved_friends(self):
#         Friends.objects.create(user1=self.user1, user2=self.user2, status=FriendStatus.ACCEPTED)
#         Friends.objects.create(user1=self.user1, user2=self.user3, status=FriendStatus.PENDING)
#         Friends.objects.create(user1=self.user1, user2=self.user4, status=FriendStatus.ACCEPTED)
#         response = self.client.get(self.friend_url, HTTP_AUTHORIZATION=self.user1.access_token)
#         print(response.json())
#         print("Response: ", response.content)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.json()['friends']), 2)
