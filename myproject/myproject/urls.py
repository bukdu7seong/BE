from django.urls import path
from myapp.views import verify_token, update_user_image, user_profile, add_new_user, get_user_by_nickname, add_friend, get_friend_pending_list

urlpatterns = [
    path('verify_token', verify_token, name='verify_token'),
    path('update_image', update_user_image, name='update_user_image'),
    path('profile', user_profile, name='user_profile'),
    path('add_new_user', add_new_user, name='add_new_user'),
    path('get_user_by_nickname', get_user_by_nickname, name='get_user_by_nickname'),
    path('add_friend', add_friend, name='add_friend'),
    path('get_friend_pending_list', get_friend_pending_list, name='get_friend_pending_list'),
]
