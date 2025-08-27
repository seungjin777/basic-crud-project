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
from functools import wraps  # 데코레이터에 사용됨
import time  # 시간을 가공하기 위한 라이브러리
import math


app = Flask(__name__)  # 플라스크 인스턴스 생성
app.config["MONGO_URI"] = "mongodb://localhost:27017/myweb"  # DB연결

# 세션 전달을 위해 필요한 암호키임 보통은 감추는게 맞다
app.config["SECRET_KEY"] = "abcd"  # 원래는 깃허브에 올라가지 않게 처리해야함

# 세션 유효시간 설정 환경변수 30분
app.config["PERMANET_SESSION_LIFETIME"] = timedelta(minutes=30)
mongo = PyMongo(app)  # 모든 코드에서 mongo 인스턴스로 DB접근 가능


# 데코레이터 함수(로그인이 필요한 부분에다 함수처럼 사용가능)
def login_required(f):
    @wraps(f)
    def defcorated_function(*args, **kwargs):
        # 로그인 안돼있을 경우
        if session.get("id") is None or session.get("id") == "":
            # 로그인 페이지로
            return redirect(url_for("member_login", next_url=request.url))
        return f(*args, **kwargs)
    return defcorated_function


@app.template_filter("formatdatetime")  # html 페이지에서 사용할 수 있는 필터
def format_datetime(value):  # 필터를 통해 해당 함수가 실행 됨, utc 타임을 보기 좋게 가공해주는 함수
    if value is None:
        return ""

    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) \
        - datetime.datetime.utcfromtimestamp(now_timestamp)
    value = datetime.datetime.fromtimestamp((int(value) / 1000)) + offset
    return value.strftime('%Y-%m-%d %H:%M:%S')


@app.route("/list")
def lists():
    # 페이지 값 (값이 없는 경우 기본값은 1)
    page = request.args.get("page", 1, type=int)
    # 한페이지당 몇개의 게시물을 출력할지
    limit = request.args.get("limit", 6, type=int)

    # 넘어온 검색 조건
    search = request.args.get("search", -1, type=int)  # 검색 종류
    keyword = request.args.get("keyword", "", type=str)  # 검색어

    # 최종적으로 완성된 쿼리를 만들 변수
    query = {}
    # 검색어 상태를 추가할 리스트 변수
    search_list = []

    if search == 0:
        # sql문법의 like와 똑같은기능 -- $regex
        search_list.append({"title": {"$regex": keyword}})
    elif search == 1:
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 2:
        search_list.append({"title": {"$regex": keyword}})
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 3:
        search_list.append({"name": {"$regex": keyword}})

    # 검색 대상이 한개라도 존재할 경우 query 변수에 $or 리스트를 쿼리 합니다.
    if len(search_list) > 0:
        query = {"$or": search_list}  # search_list 중 하나라도 존재하면 ok

    board = mongo.db.board
    # board 컬렉션의 데이터 지정 페이지만큼 가져옴--> 이전 페이지 스킵, 가져올 개수
    datas = board.find(query).skip((page - 1) * limit).limit(limit)

    # 게시물의 총 갯수
    tot_count = board.count_documents(query)
    # 마지막 페이지의 수를 구함
    last_page_num = math.ceil(tot_count / limit)

    # 페이지 블록 5개씩 표시
    block_size = 5
    # 현재 블럭의 위치
    block_num = int((page - 1) / block_size)
    # 블럭의 시작 위치
    block_start = int((block_size * block_num) + 1)
    # 블럭의 끝 위치
    block_last = math.ceil(block_start + (block_size - 1))

    return render_template(
        "list.html",
        datas=list(datas),
        limit=limit,
        page=page,
        block_start=block_start,
        block_last=block_last,
        last_page_num=last_page_num,
        search=search,
        keyword=keyword)  # 모든 데이터 list.html로 넘김


@app.route("/view/<idx>")  # 상세보기 페이지
@login_required  # 데코레이터 함수 사용
def board_view(idx):  # 펜시방법으로 받는법 주소에 <idx>, 인자 idx (방법 2 : 펜시방식)
    # idx = request.args.get("idx")
    # /view?idx=쌀랐라라 --> GET방식으로 받아온 리다이렉트 idx값 받아오기 (방법 1 : 일반방식)

    if idx is not None:
        page = request.args.get("page")
        search = request.args.get("search")
        keyword = request.args.get("keyword")

        board = mongo.db.board  # board 컬렉션 접근
        # data = board.find_one({"_id": ObjectId(idx)})
        # find와 update를 동시에 할 수 있는 함수
        data = board.find_one_and_update(
            {"_id": ObjectId(idx)},
            {"$inc": {"view": 1}},  # view값을 1만큼 증가
            return_document=True)  # 업데이트 적용된 다음 리턴

        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "pubdate": data.get("pubdate"),
                "view": data.get("view"),
                "writer_id": data.get("writer_id", "")
            }

            return render_template(
                "view.html",
                result=result,
                page=page,
                search=search,
                keyword=keyword)
            # 받아온 데이터 result를 view.html로 넘김

    return abort(404)  # 404 오류 페이지 리턴


@app.route("/write", methods=["GET", "POST"])  # GET, POST를 둘 다 사용할 거다
@login_required  # 데코레이터 함수 사용
def board_write():
    if request.method == "POST":  # 데이터가 POST로 전송(요청)됐을 경우
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")

        current_utc_time = \
            round(datetime.datetime.now(datetime.UTC).timestamp() * 1000)
        # 국제협정시간, 가공하기 쉬운 데이터로

        board = mongo.db.board  # DB의 board 컬렉션(테이블)에 접근
        post = {
            "name": name,
            "title": title,
            "contents": contents,
            "pubdate": current_utc_time,
            "writer_id": session.get("id"),  # 본인이 작성한 글인지 판단하기 위한 값
            "view": 0,
        }

        x = board.insert_one(post)  # board 컬렉션에 post데이터 삽입
        print(x.inserted_id)  # post 값이 삽입되면서 자동으로 생성된 id값
        print(name, title, contents, current_utc_time)

        return redirect(url_for("board_view", idx=x.inserted_id))
        # board_view함수가 가리키는 url로 id값 리다이렉트

    else:  # GET으로 전송(요청)됐을 경우
        return render_template("write.html")  # 그냥 write페이지를 렌더링 시킴


@app.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":  # POST형식으로 요청했을때
        # join페이지에서 form 데이터 받아오기
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        pass1 = request.form.get("pass", type=str)
        pass2 = request.form.get("pass2", type=str)

        # 받아온 데이터 중 하나라도 None일 경우
        if name == "" or email == "" or pass1 == "" or pass2 == "":
            flash("입력되지 않은 값이 있습니다.")  # 리다이렉트시 같이 넘겨질 메시지
            return render_template("join.html")

        # 비밀번호와 비밀번호 확인이 일치하지 않을 경우
        if pass1 != pass2:
            flash("비밀번호가 일치하지 않습니다.")
            return render_template("join.html")

        # DB에서 중복된 이메일이 존재하는지 조회
        members = mongo.db.members
        cnt = members.count_documents({"email": email})
        if cnt > 0:
            flash("중복된 이메일 주소입니다.")
            return render_template("join.html")

        current_utc_time = \
            round(datetime.datetime.now(datetime.UTC).timestamp() * 1000)
        post = {
            "name": name,
            "email": email,
            "pass": pass1,
            "joindata": current_utc_time,
            "logintime": "",
            "logincount": 0,
        }

        members.insert_one(post)
        return ""
    else:
        # GET방식으로 날라올 경우 그냥 페이지 리턴
        return render_template("join.html")


@app.route("/login", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        # post로 요청된 form데이터 받아오기
        email = request.form.get("email")
        password = request.form.get("pass")
        next_url = request.form.get("next_url")

        members = mongo.db.members
        data = members.find_one({"email": email})

        if data is None:
            flash("회원 정보가 없습니다.")
            return redirect(url_for("member_login"))
        else:
            if data.get("pass") == password:  # 해당 이메일의 비밀번호가 일치 헸을 경우
                # 세션(서버쪽 저정)에 로그인한 회원의 정보 저장
                session["email"] = email
                session["name"] = data.get("name")
                session["id"] = data.get("_id")
                session.permanent = True  # 세션 유지시간을 할당하기 위해 on 시킴

                if next_url is not None:  # 기존 페이지 있었다면
                    return redirect(next_url)  # 그쪽으로
                else:
                    return redirect(url_for("lists"))
            else:  # 해당 이메일의 비밀번호가 일치하지 않을 경우
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for("member_login"))
        return ""
    else:
        next_url = request.args.get("next_url", type=str)
        if next_url is not None:
            # 재로그인시 기존페이지를 넘겨주기 위한 편의성 기능
            return render_template("login.html", next_url=next)
        else:
            return render_template("login.html")


@app.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):  # 글 수정
    if request.method == "GET":  # 수정 버튼으로 진입할 경우
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})  # 유저 존재하는지
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("list"))
        else:
            # 세션(현재 사용자)의 id와 받아온 idx값이 같아야 수정 가능
            if session.get("id") == data.get("writer_id"):
                # 값이 일치했으니 작성된 정보를 보냄
                return render_template("edit.html", data=data)
            else:
                # 값이 다르면 권한이 없는것임
                flash("글 수정 권한이 없습니다.")
                return redirect(url_for("lists"))
    else:  # 수정을 눌렀을경우 (POST요청)
        title = request.form.get("title")
        contents = request.form.get("contents")

        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if session.get("id") == data.get("writer_id"):
            # 본인 맞을 경우 수정 go
            board.update_one({"_id": ObjectId(idx)}, {
                "$set": {
                    "title": title,  # 제목과
                    "contents": contents  # 내용만 수정할 수 있게
                }
            })
            flash("수정되었습니다.")
            return redirect(url_for("board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("lists"))


@app.route("/delete/<idx>", methods=["GET", "POST"])
def board_delete(idx):  # 글 삭제
    board = mongo.db.board
    data = board.find_one({"_id": ObjectId(idx)})

    if data.get("writer_id") == session.get("id"):
        # 권한이 일치하는 경우
        board.delete_one({"_id": ObjectId(idx)})
        flash("삭제 되었습니다.")
    else:
        # 권한이 없는 경우
        flash("삭제 권한이 없습니다.")
    return redirect(url_for("lists"))


if __name__ == "__main__":  # run.py를 직접 실행할때 실행된는 구간(엔트리 포인트?)
    # 외부 접속 가능, 디버그 옵션, 포트 9000변경
    app.run(host="0.0.0.0", debug=True, port=9000)
