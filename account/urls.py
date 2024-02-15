from typing import Any

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


app_name = 'account'

urlpatterns = [
    path('', views.name, name="index"),
    path('login/42', views.get_42authorization, name="42login"),
    path('third_token/', views.login_with_42oauth, name=""),
    path('signup/', views.signup, name="signup"),
    path('jwt_token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('jwt_token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]
