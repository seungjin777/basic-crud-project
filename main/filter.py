# 필터 파일
from main import app, datetime, time


@app.template_filter("formatdatetime")  # html 페이지에서 사용할 수 있는 필터
def format_datetime(value):  # 필터를 통해 해당 함수가 실행 됨, utc 타임을 보기 좋게 가공해주는 함수
    if value is None:
        return ""

    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) \
        - datetime.datetime.utcfromtimestamp(now_timestamp)
    value = datetime.datetime.fromtimestamp((int(value) / 1000)) + offset
    return value.strftime('%Y-%m-%d %H:%M:%S')
