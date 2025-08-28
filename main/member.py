from main import app
from main import request, redirect
from main import mongo
from main import render_template
from main import datetime
from main import url_for
from main import flash
from main import session

from flask import Blueprint
blueprint = Blueprint("member", __name__, url_prefix="/member")


@blueprint.route("/join", methods=["GET", "POST"])
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


@blueprint.route("/login", methods=["GET", "POST"])
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
            return redirect(url_for("member.member_login"))
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
                    return redirect(url_for("board.lists"))
            else:  # 해당 이메일의 비밀번호가 일치하지 않을 경우
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for("member.member_login"))
    else:
        next_url = request.args.get("next_url", type=str)
        if next_url is not None:
            # 재로그인시 기존페이지를 넘겨주기 위한 편의성 기능
            return render_template("login.html", next_url=next)
        else:
            return render_template("login.html")
