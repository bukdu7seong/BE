from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class Custom42TokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        user = authenticate(email=email)
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        return issue(user)


class CustomTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        return issue(user)


def issue(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return {
        'refresh': str(refresh),
        'access': access_token,
        'id': user.id,
    }
