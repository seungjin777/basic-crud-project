from flask import Flask
from flask import request
from flask import render_template  # 템플릿 렌더링 함수?
from flask_pymongo import PyMongo
import datetime as dt  # 시간관련 라이브러리


app = Flask(__name__)  # 플라스크 인스턴스 생성
app.config["MONGO_URI"] = "mongodb://localhost:27017/myweb"  # DB연결
mongo = PyMongo(app)  # 모든 코드에서 mongo 인스턴스로 DB접근 가능


@app.route("/write", methods=["GET", "POST"])  # GET, POST를 둘 다 사용할 거다
def board_write():
    if request.method == "POST":  # 데이터가 POST로 전송(요청)됐을 경우
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")

        current_utc_time = round(dt.datetime.now(dt.UTC).timestamp() * 1000)
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
        return ""
    else:  # GET으로 전송(요청)됐을 경우
        return render_template("write.html")  # 그냥 write페이지를 렌더링 시킴


if __name__ == "__main__":  # run.py를 직접 실행할때 실행된는 구간(엔트리 포인트?)
    # 외부 접속 가능, 디버그 옵션, 포트 9000변경
    app.run(host="0.0.0.0", debug=True, port=9000)
