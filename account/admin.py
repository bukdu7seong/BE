from django.contrib import admin
from .models import User


# Register your models here.

@admin.register(User)
class accountAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'password', 'email', 'language', 'image']
    list_display_links = ['username']
    list_filter = ['created_at', 'is_active']
