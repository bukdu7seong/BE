# from django.db import models
# from django.utils import timezone
#
# class Language(models.TextChoices):
#     ENGLISH = 'EN', 'English'
#     KOREAN = 'KO', 'Korean'
#     SPANISH = 'ES', 'Spanish'
#
# class AppUser(models.Model):
#     user_id = models.AutoField(primary_key=True)
#     access_token = models.CharField(max_length=100)
#     email = models.EmailField(unique=True)
#     provider = models.CharField(max_length=50, default='google')
#     provider_id = models.CharField(max_length=50, unique=True)
#     image = models.TextField(null=True)
#     two_fact = models.BooleanField(default=False)
#     nickname = models.CharField(max_length=50)
#     created_at = models.DateTimeField(default=timezone.now)
#     updated_at = models.DateTimeField(default=timezone.now)
#     language = models.CharField(
#         max_length=2,
#         choices=Language.choices,
#         default=Language.ENGLISH
#     )
#     class Meta:
#         db_table = 'app_user'