import requests
from bs4 import BeautifulSoup  # lxml 파서로 HTML을 파싱 후 선택자로 요소 추출
from pymongo import MongoClient
import datetime
from time import sleep

client = MongoClient(host="localhost", port=27017)
db = client.myweb  # DB 접근
col = db.board     # 컬렉션 접근

# 요청 헤더
header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

query = "포켓몬레전드za"

for i in range(5):
    # start=0,10,20... 페이지네이션 / 언어, 지역, 개인화(비활성) 고정
    params = {"q": query, "start": i * 10, "hl": "ko", "gl": "KR", "pws": "0"}

    r = requests.get("https://www.google.com/search", params=params, headers=header, timeout=10)
    r.raise_for_status()

    bs = BeautifulSoup(r.text, "lxml")  # lxml 파서로 파싱

    # 비교적 안정적인 결과 컨테이너들(OR 선택자). 구조가 달라도 한 쪽은 잡힐 확률이 높음
    lists = bs.select("div#rso > div.MjjYud, div#rso > div.g, div#rso .g")

    for li in lists:
        # 현재 UTC 밀리초 타임스탬프
        current_utc_time = round(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)

        try:
            # 제목: 특정 클래스 대신 h3 자체 사용(가장 내구성 좋음)
            h3 = li.select_one("h3")
            if not h3:
                continue
            title = h3.get_text(strip=True)
            if not title:
                continue

            # 요약: 가장 흔한 스니펫 블록 -> 없으면 h3 부모의 다음 형제들에서 텍스트 긴 블록을 탐색
            snippet_el = li.select_one("div.VwiC3b")
            if snippet_el:
                contents = snippet_el.get_text(" ", strip=True)
            else:
                contents = ""
                parent = h3.parent
                for sib in parent.next_siblings:
                    try:
                        text = sib.get_text(" ", strip=True)
                    except Exception:
                        text = ""
                    # 너무 짧은 조각(예: 버튼/링크 텍스트)은 제외
                    if text and len(text) >= 20:
                        contents = text
                        break

            # MongoDB 저장
            col.insert_one({
                "name": "테스트",
                "title": title,
                "contents": contents,
                "view": 0,
                "pubdate": current_utc_time
            })
            print("Success:", title)

        except Exception as e:
            print("Fail:", repr(e))
            continue

    # 과한 연속 요청 방지(실험/학습 용도)
    sleep(5)
