from django.contrib import admin
from .models import Friends  # 모델 파일에서 Friends 모델을 임포트합니다.

admin.site.register(Friends)  # Friends 모델을 관리자 페이지에 등록합니다.