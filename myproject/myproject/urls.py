from django.urls import path
from myapp.views import verify_token, update_user_image, user_profile, add_new_user

urlpatterns = [
    path('verify_token', verify_token, name='verify_token'),
    path('update_image/', update_user_image, name='update_user_image'),
    path('profile', user_profile, name='user_profile'),
    path('add_new_user', add_new_user, name='add_new_user'),
]
