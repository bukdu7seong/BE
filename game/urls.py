from django.urls import path
from . import views

urlpatterns = [
    path('results', views.GameResultView.as_view(), name='game_results'),
    path('users/me/games/history', views.GameHistoryView.as_view(), name='game_history'),
]