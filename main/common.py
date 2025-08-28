# 데코레이터 파일

from functools import wraps  # 데코레이터에 사용됨
from main import session, redirect, request, url_for


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
