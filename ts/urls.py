from django.urls import path
from appuser.views import ProfileView, UserView, add_new_user, login
from friends.views import FriendView

urlpatterns = [
    path('login', login, name='login'),

    path('profile', ProfileView.as_view(), name='profile'),

    path('user/', UserView.as_view(), name='user'),
    path('user/<str:user_id>', UserView.as_view(), name='user'),

    path('add_new_user', add_new_user, name='add_new_user'),

    path('friend/', FriendView.as_view()),
    path('friend/request/', FriendView.as_view()),
    path('friend/accept/<str:user_id>/', FriendView.as_view()),
    path('friend/deny/<str:user_id>/', FriendView.as_view()),
    path('friend/request/<str:user_id>/', FriendView.as_view()),
]

