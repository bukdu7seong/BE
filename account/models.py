from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)


class UserManager(BaseUserManager):
    use_in_migrations = True
    def create_user(self, email, username):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username):
        user = self.create_user(
            email,
            username=username,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(
        verbose_name='username',
        max_length=255,
        unique=True)
    email = models.EmailField(
        verbose_name='email',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    provider = models.CharField(max_length=100, blank=True)
    provider_url = models.URLField(blank=True)

    image = models.ImageField(upload_to='images/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'account'