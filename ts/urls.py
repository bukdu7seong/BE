from django.urls import path, include

urlpatterns = [
    path('friend/', include('friend.urls')),
]
