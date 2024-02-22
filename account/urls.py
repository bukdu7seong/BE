from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

app_name = 'account'

router = DefaultRouter()
router.register(r'', views.MyLoginView, basename='account')

urlpatterns = [
    path('', include(router.urls)),
    path('42oauth', views.FtAuthView.as_view(), name="42oauth"),
    path('signup', views.SignupView.as_view(), name="signup"),
    path('test', views.TestView.as_view(), name="test"),

]
