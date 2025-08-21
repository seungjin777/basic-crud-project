from flask import Flask
from flask import request
from flask import render_template  # 템플릿 렌더링 함수?
from flask_pymongo import PyMongo
import datetime  # 시간관련 라이브러리
from bson.objectid import ObjectId  # id타입 변경을 위한 라이브러리
from flask import abort  # 오류 발생시 리턴할 함수
from flask import redirect  # 리다이렉트 함수
from flask import url_for  # 리다이렉트 주소 찾는 함수
import time  # 시간을 가공하기 위한 라이브러리

app = Flask(__name__)  # 플라스크 인스턴스 생성
app.config["MONGO_URI"] = "mongodb://localhost:27017/myweb"  # DB연결
mongo = PyMongo(app)  # 모든 코드에서 mongo 인스턴스로 DB접근 가능


@app.template_filter("formatdatetime")  # html 페이지에서 사용할 수 있는 필터
def format_datetime(value):  # 필터를 통해 해당 함수가 실행 됨, utc 타임을 보기 좋게 가공해주는 함수
    if value is None:
        return ""

    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) \
        - datetime.datetime.utcfromtimestamp(now_timestamp)
    value = datetime.datetime.fromtimestamp((int(value) / 1000)) + offset
    return value.strftime('%Y-%m-%d %H:%M:%S')


@app.route("/view/<idx>")  # 상세보기 페이지
def board_view(idx):  # 펜시방법으로 받는법 주소에 <idx>, 인자 idx (방법 2 : 펜시방식)
    # idx = request.args.get("idx")
    # /view?idx=쌀랐라라 --> GET방식으로 받아온 리다이렉트 idx값 받아오기 (방법 1 : 일반방식)

    if idx is not None:
        board = mongo.db.board  # board 컬렉션 접근
        data = board.find_one({"_id": ObjectId(idx)})

        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "pubdate": data.get("pubdate"),
                "view": data.get("view")
            }

            return render_template("view.html", result=result)
            # 받아온 데이터 result를 view.html로 넘김

    return abort(404)  # 404 오류 페이지 리턴


@app.route("/write", methods=["GET", "POST"])  # GET, POST를 둘 다 사용할 거다
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
            "view": 0,
        }

        x = board.insert_one(post)  # board 컬렉션에 post데이터 삽입
        print(x.inserted_id)  # post 값이 삽입되면서 자동으로 생성된 id값
        print(name, title, contents, current_utc_time)

        return redirect(url_for("board_view", idx=x.inserted_id))
        # board_view함수가 가리키는 url로 id값 리다이렉트

    else:  # GET으로 전송(요청)됐을 경우
        return render_template("write.html")  # 그냥 write페이지를 렌더링 시킴


if __name__ == "__main__":  # run.py를 직접 실행할때 실행된는 구간(엔트리 포인트?)
    # 외부 접속 가능, 디버그 옵션, 포트 9000변경
    app.run(host="0.0.0.0", debug=True, port=9000)
