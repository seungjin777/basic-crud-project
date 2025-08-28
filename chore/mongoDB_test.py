import pymongo

m = {
    "이름": "강승진",
    "나이": 30,
    "거주지": "서울"
}

conn = pymongo.MongoClient("localhost", 27017)  # 디폴트 로컬, 포트는 27017
db = conn.test # DB서버.DB이름 -- test라는 DB가 없으면 자동 생성
col = db.members # DB에 members라는 컬렉션(테이블)이 없으면 자동 생성


# 데이터 삽입
col.insert_one(m)


# 데이터 검색
result = col.find({"이름": "홍길동"}) # 이름이 홍길동인
print(result) # 커서를 가져옴
for r in result: # 실제 데이터 컬렉션별 출력
    print(r)

result = col.find({"$or": [{"이름": "홍길동"}, {"이름": "강승진"}]}) # or연산
for r in result:
    print(r)

r = col.find_one({"이름": "강승진"}) # 값 1개만 가져옴
print(r)

result = col.find({"나이": {"$gt": 30}}) # great than 나이가 30초과인 값 추출
for r in result:
    print(r)
# $gte 이상, $lt 미만, $lte 이하

result = col.find({"이름": True}) # 이름만 추출, false 제외

result = col.find().skip(1).limit(3) # 1번째 제외하고 3개만 출력

result = col.find().sort(1) # 오름차순 정렬, -1이면 내림차순

col.upadate({"이름": "강승진"}, {"이름": "홍길동"}) # 이름이 강승진인 하나의 필드 전체가 2번째 인자로 바뀜
col.upadate({"이름": "강승진"}, {"set": {"이름": "홍길동"}}) # 이름이 강승진인 하나의 필드 이름만 2번째 인자로 바뀜
col.upadate({"이름": "가악앙"}, {"이름": "홍길동"}, upsert=True) # 이름이 가악앙인 필드가 없으면 인서트해줌

col.remove({"이름": "가악앙"}) # 이름이 가악앙인 필드 삭제, 조건빼면 전체 삭제된 조심!!!
# .delete_one() .delete_many()

