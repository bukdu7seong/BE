from django.test import TestCase, Client
from django.urls import reverse
from user.models import AppUser
from friend.models import Friends
from unittest.mock import patch

def mock_get_user_info(self, request):
    return '1'

class ApproveFriendViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # 두 명의 사용자를 생성합니다.
        self.user1 = AppUser.objects.create(email='user1@test.com', provider_id='user1')
        self.user2 = AppUser.objects.create(email='user2@test.com', provider_id='user2')

        # 친구 요청을 생성합니다.
        self.friend_request = Friends.objects.create(user1=self.user1, user2=self.user2)

        # 승인 API의 URL을 가져옵니다.
        self.url = reverse('approve_friend', args=[self.user2.user_id])

    @patch('friend.views.ApproveFriendView._get_logged_in_user_id', mock_get_user_info)
    def test_approve_friend_request(self):
        print(self.url)
        # 승인 API를 호출합니다.
        response = self.client.post(self.url)
        print(response.content)
        # 응답 상태 코드가 200인지 확인합니다.
        self.assertEqual(response.status_code, 200)

        # 친구 요청이 승인 상태로 변경되었는지 확인합니다.
        self.friend_request.refresh_from_db()
        self.assertEqual(self.friend_request.status, 'APPROVED')