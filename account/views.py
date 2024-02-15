import json

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from .models import User
import requests
from .serializer import CustomTokenObtainPairSerializer


# Create your views here.

def check_signup(user_info):
    return False


def create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        user = User(title=title, content=content)
        user.save()
        return redirect('articles:index')
    else:
        return render(request, 'articles/create.html')


def get_42_access_token(code):
    data = {
        "grant_type": "authorization_code",
        "client_id": "u-s4t2ud-33518bf1e037b1706036053f6530503148e5995f22e2a5dca937497ee382c944",
        "client_secret": "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",
        "code": code,
        "redirect_uri": "http://127.0.0.1:8000/account",
    }
    try:
        return requests.post("https://api.intra.42.fr/oauth/token", data=data)
    except requests.exceptions.RequestException as e:
        return HttpResponse(str(e), status=500)


def login_with_42oauth(request):
    code = request.GET.get('code', None)
    if code is not None:
        response = get_42_access_token(code)
        if response.status_code == 200:
            email = get_42_email(response)
            try:
                user = User.objects.get(email=email)
                token = CustomTokenObtainPairSerializer.get_token(user)
                return HttpResponse(token, status=200)
            except User.DoesNotExist:
                return HttpResponse('have to redirect to sign up', status=404)
        else:
            return HttpResponse('fail to get 42 access token', status=400)
    else:
        return HttpResponse('fail to get code', status=400)


def get_42_email(response):
    js = response.json();
    token = js.get('access_token')
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={'Authorization': 'Bearer ' + token})
    if user_info.status_code == 200:
        return user_info.json()['email']
    else:
        return None


def get_42authorization(request):
    url = "https://api.intra.42.fr/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": "u-s4t2ud-33518bf1e037b1706036053f6530503148e5995f22e2a5dca937497ee382c944",
        "client_secret": "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",
        "scope": "public"
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return redirect("https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud"
                            "-33518bf1e037b1706036053f6530503148e5995f22e2a5dca937497ee382c944&redirect_uri=http%3A"
                            "%2F%2F127.0.0.1%3A8000%2Faccount&response_type=code")
        else:
            return HttpResponse(response.content, status=response.status_code)
    except requests.exceptions.RequestException as e:
        return HttpResponse(str(e), status=50)


def name(request):
    return HttpResponse("Hello, world. You're at the", status=200)


def signup(request):
    data = json.loads(request.body)
    user = User.objects.create_user(
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
    )
    user.save()
    return HttpResponse("ok")
