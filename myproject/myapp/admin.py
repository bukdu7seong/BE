from django.contrib import admin
from .models import AppUser, Game, Friends

admin.site.register(AppUser)
admin.site.register(Game)
admin.site.register(Friends)
