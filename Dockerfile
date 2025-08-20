FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        build-essential \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 정적 파일 디렉토리 생성
RUN mkdir -p /app/staticfiles

# 포트 노출
EXPOSE 8000

# 기본 명령어
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "AI_service.wsgi:application"]