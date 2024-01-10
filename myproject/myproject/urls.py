from django.urls import path
from myapp.views import verify_token, get_user_profile, update_user_image, user_profile

urlpatterns = [
    path('verify_token', verify_token, name='verify_token'),
    # path('profile', get_user_profile, name='get_user_profile'),
    path('update_image/', update_user_image, name='update_user_image'),
    path('profile', user_profile, name='user_profile'),
]
