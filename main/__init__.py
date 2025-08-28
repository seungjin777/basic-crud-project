# __init__ 파일이 실행되면 초기세팅이 이루어지는 공간
# 패키지가 초기화 되는 파일
from flask import Flask
from flask import request
from flask import render_template  # 템플릿 렌더링 함수?
from flask_pymongo import PyMongo
import datetime  # 시간관련 라이브러리
from datetime import timedelta  # 세션 유효시간 지정하기 위해 필요한 라이브러리
from bson.objectid import ObjectId  # id타입 변경을 위한 라이브러리
from flask import abort  # 오류 발생시 리턴할 함수
from flask import redirect  # 리다이렉트 함수
from flask import url_for  # 리다이렉트 주소 찾는 함수
from flask import flash  # 리다이렉트시 같이 넘길 메시지 함수?, 시크릿키 설정 해야함!!
from flask import session  # 세션 라이브러리

import time  # 시간을 가공하기 위한 라이브러리
import math


app = Flask(__name__)  # 플라스크 인스턴스 생성
app.config["MONGO_URI"] = "mongodb://localhost:27017/myweb"  # DB연결
# 세션 전달을 위해 필요한 암호키임 보통은 감추는게 맞다
app.config["SECRET_KEY"] = "abcd"  # 원래는 깃허브에 올라가지 않게 처리해야함
# 세션 유효시간 설정 환경변수 30분
app.config["PERMANET_SESSION_LIFETIME"] = timedelta(minutes=30)
mongo = PyMongo(app)  # 모든 코드에서 mongo 인스턴스로 DB접근 가능


from .common import login_required
from .filter import format_datetime
from . import board
from . import member

# 블루프린터가 동작 되기 위한 설정
app.register_blueprint(board.blueprint)
app.register_blueprint(member.blueprint)
