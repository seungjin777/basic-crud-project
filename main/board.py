from main import app
from main import login_required
from main import request, redirect
from main import mongo
from main import render_template
from main import datetime
from main import abort
from main import url_for
from main import flash
from main import session
from main import ObjectId
from main import math


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
