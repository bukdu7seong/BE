from django.core.management.base import BaseCommand
from myapp.models import AppUser, Game, Friends
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Adds demo data to the database'

    def handle(self, *args, **kwargs):
        # 데모 데이터 정의
        demo_users = [
            {
                'access_token': 'token123',
                'email': 'user1@example.com',
                'provider': 'provider1',
                'provider_id': 'prov1',
                'image': 'https://picsum.photos/id/237/200/300',
                'two_fact': False,
                'nickname': 'nick1',
                'language': 'English',
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            },
            # 추가적인 데모 사용자 데이터...
        ]

        # 데이터베이스에 데모 데이터 삽입
        for user_data in demo_users:
            user, created = AppUser.objects.get_or_create(
                email=user_data['email'], 
                defaults={**user_data, 'created_at': timezone.now()}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully added user {user.email}'))
            else:
                self.stdout.write(self.style.WARNING(f'User {user.email} already exists'))

        # Game 모델에 대한 데모 데이터 추가
        Game.objects.get_or_create(
            player1_id=1,
            player2_id=2,
            created_at=datetime.date(2023, 3, 1),
            winner='nick1',
            options='NORMAL'
        )
        Game.objects.get_or_create(
            player1_id=2,
            player2_id=1,
            created_at=datetime.date(2023, 3, 2),
            winner='nick2',
            options='SPEED'
        )

        # Friends 모델에 대한 데모 데이터 추가
        Friends.objects.get_or_create(
            user1_id=1,
            user2_id=2,
            status='PENDING'
        )
        Friends.objects.get_or_create(
            user1_id=2,
            user2_id=1,
            status='APPROVE'
        )

        self.stdout.write(self.style.SUCCESS('Successfully added demo data'))