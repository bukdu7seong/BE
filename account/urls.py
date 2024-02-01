from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('', views.name, name="index"),
    path('token/', views.get_oauth_token, name="token"),
    path('third_token/', views.login_42oauth, name=""),
    path('signup/', views.signup, name="signup")
]
