from django.db import models
from django.utils.translation import gettext_lazy as _
from myapp.models.appuser import AppUser

class FriendStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    ACCEPTED = 'ACCEPTED', _('Accepted')
    DECLINED = 'DECLINED', _('Declined')
    BLOCKED = 'BLOCKED', _('Blocked')

class Friends(models.Model):
    user1 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='friends_user1')
    user2 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='friends_user2')
    status = models.CharField(
        max_length=20,
        choices=FriendStatus.choices,
        default=FriendStatus.PENDING
    )