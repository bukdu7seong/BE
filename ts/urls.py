from django.urls import path, include
from user.views import update_user_image, user_profile, add_new_user, get_user_by_nickname
from security.views import verify_token

urlpatterns = [
    path('verify_token', verify_token, name='verify_token'),
    path('update_image', update_user_image, name='update_user_image'),
    path('profile', user_profile, name='user_profile'),
    path('add_new_user', add_new_user, name='add_new_user'),
    path('get_user_by_nickname', get_user_by_nickname, name='get_user_by_nickname'),
    path('friend/', include('friend.urls')),
]
