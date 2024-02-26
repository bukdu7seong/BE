from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email, password, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=email,
            username=username,
            password=password,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        superuser = self.create_user(
            username=username,
            email=email,
            password=password,
        )
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save(using=self._db)
        return superuser


LANGUAGE_CHOICES = (
    ('EN', 'English'),
    ('FR', 'French'),
    ('KR', 'Korean'),
)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        verbose_name='username',
        max_length=20,
        unique=True)
    intraId = models.CharField(
        max_length=20,
        blank=True,
    )
    email = models.EmailField(
        verbose_name='email',
        max_length=30,
        unique=True,
    )
    password = models.CharField(
        verbose_name='password',
        max_length=255,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    twoFactor = models.BooleanField(default=True)

    language = models.CharField(choices=LANGUAGE_CHOICES, max_length=4, default='KR')

    image = models.ImageField(upload_to='images/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
