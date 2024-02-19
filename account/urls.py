from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

app_name = 'account'

router = DefaultRouter()
router.register(r'', views.MyLoginView, basename='account')

urlpatterns = [
    path('', include(router.urls)),
    path('42oauth', views.get_42authorization, name="42oauth"),
    path('signup', views.SignupView.as_view(), name="signup"),
    path('jwt_token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('jwt_token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('test', views.TestView.as_view(), name="test"),

]
