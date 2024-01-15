from django.urls import path
from .views import FriendView

urlpatterns = [
    path('', FriendView.as_view(), name='friend'),
]