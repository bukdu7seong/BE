import json

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from .models import User
import requests
from django.contrib.auth import get_user_model


# Create your views here.

def check_signup(user_info):
    return False


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


def get_42_user_info(response):
    js = response.json();
    ts = js.get('access_token')
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={'Authorization': 'Bearer ' + ts})
    if user_info.status_code == 200:
        return user_info.json()['email']
    else:
        return None


def login_42oauth(request):
    code = request.GET.get('code', None)
    if code is not None:
        response = get_42_access_token(code)
        if response.status_code == 200:
            email = get_42_user_info(response)
            try:
                user = User.objects.get(email=email)
                return HttpResponse('http://localhost:8000/account/', status=200)
            except User.DoesNotExist:
                return HttpResponse('have to redirect to sign up', status=404)
        else:
            return HttpResponse('fail to get 42 access token', status=400)
    else:
        return HttpResponse('fail to get code', status=400)


def create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        user = User(title=title, content=content)
        user.save()
        return redirect('articles:index')
    else:
        return render(request, 'articles/create.html')


def get_oauth_token(request):
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
            return redirect(
                "https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-33518bf1e037b1706036053f6530503148e5995f22e2a5dca937497ee382c944&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Faccount&response_type=code")
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
