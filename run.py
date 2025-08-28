from main import app


if __name__ == "__main__":  # run.py를 직접 실행할때 실행된는 구간(엔트리 포인트?)
    # 외부 접속 가능, 디버그 옵션, 포트 9000변경
    app.run(host="0.0.0.0", debug=True, port=9000)
