from django.urls import path
from .views import GameHistoryView, GameResultView

urlpatterns = [
    #/game?pageSize={size}&page={page}
    path('history/', GameHistoryView.as_view(), name='game_history'),  # 'history/'라는 URL 패턴을 사용합니다.
    path('result/', GameResultView.as_view(), name='game_result'),
]