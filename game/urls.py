from django.urls import path
from . import views

urlpatterns = [
    path('results', views.GameResultView.as_view(), name='game_results'),
    path('result/<int:game_id>/', views.GameResultView.as_view(), name='game_result'),
    path('users/me/games/history', views.GameHistoryView.as_view(), name='game_history'),
]