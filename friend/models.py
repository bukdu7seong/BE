from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

AppUser = get_user_model()
class FriendStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    ACCEPTED = 'ACCEPTED', _('Accepted')

class Friends(models.Model):
    user1 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='friends_user1')
    user2 = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='friends_user2')
    status = models.CharField(
        max_length=20,
        choices=FriendStatus.choices,
        default=FriendStatus.PENDING
    )
    class Meta:
        unique_together = ('user1', 'user2')
        db_table = 'friends'
        ordering = ['id']
        