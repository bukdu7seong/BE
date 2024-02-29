from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from game.models import Game
from rest_framework_simplejwt.tokens import RefreshToken



User = get_user_model()


class UserSigninSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'password')

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise User.DoesNotExist("Not Found")
        return issue(user)


def issue(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return {
        'refresh': str(refresh),
        'access': access_token,
        'id': user.id,
    }


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'image')

class UserImageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['image']

class UserProfileStatsSerializer(serializers.ModelSerializer):
    win_rate = serializers.SerializerMethodField()
    wins = serializers.SerializerMethodField()
    losses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'image', 'win_rate', 'wins', 'losses')

    def get_win_rate(self, obj):
        # 승률 계산 로직
        games_won = Game.objects.filter(winner=obj, player2__isnull=False).count()
        games_lost = Game.objects.filter(loser=obj, player2__isnull=False).count()
        total_games = games_won + games_lost
        return (games_won / total_games * 100) if total_games > 0 else 0

    def get_wins(self, obj):
        return Game.objects.filter(winner=obj, player2__isnull=False).count()

    def get_losses(self, obj):
        return Game.objects.filter(loser=obj, player2__isnull=False).count()
    
class User2FASerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_2fa']

    def update(self, instance, validated_data):
        instance.is_2fa = validated_data.get('is_2fa', instance.is_2fa)
        instance.save()
        return instance

class UserLanguageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['language']

    def update(self, instance, validated_data):
        instance.language = validated_data.get('language', instance.language)
        instance.save()
        return instance