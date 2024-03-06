# Makefile

DC = docker-compose

all:
	$(DC) up -d

# 이미지만 빌드
build:
	$(DC) build

# 이미지 빌드하고 컨테이너 실행
up:
	$(DC) up --build -d

# 실행 중인 컨테이너 멈추기
down:
	$(DC) down

# 실행 중인 컨테이너와 사용하지 않는 도커 리소스 정리
clean: down
	docker system prune --force

# 실행 중인 컨테이너에 명령어 실행 (예: bash)
exec:
	$(DC) exec web bash

# 애플리케이션 테스트 실행
test:
	$(DC) exec web npm test

# 컨테이너와 이미지를 완전히 정리. (컨테이너, 네트워크, 볼륨, 이미지)
fclean: down
	docker system prune -a --volumes --force

# 컨테이너를 정리하고 다시 빌드
re: fclean up

.PHONY: build up down clean exec test fclean re