from django.urls import path
from .views import FriendView, DenyFriendView, ApproveFriendView

urlpatterns = [
    path('', FriendView.as_view(), name='friend'),
    path('request/<int:user_id>/', FriendView.as_view(), name='add_friend'),
    path('deny/<int:user_id>/', DenyFriendView.as_view(), name='deny_friend'),
    path('accept/<int:user_id>/', ApproveFriendView.as_view(), name='approve_friend'),
]