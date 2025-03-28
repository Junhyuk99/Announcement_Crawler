import re
import time
import requests
import logging
from bs4 import BeautifulSoup
from stqdm import stqdm  # stqdm 임포트

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_customs_data():
    """
    관세청 공지사항 페이지에서
    1페이지부터 150페이지까지 크롤링하여 각 게시글의 제목, 등록일, 상세페이지 링크를
    딕셔너리 형태의 리스트로 반환합니다.

    - 제목: <td data-table="subject"> 내부의 <a> 태그의 title 속성
    - 등록일: <td data-table="date"> 의 텍스트
    - 상세 링크: <a> 태그의 data-id와 data-url 속성을 이용하여
       "https://www.customs.go.kr/kcs/na/ntt/selectNttInfo.do?nttSn={data-id}&nttSnUrl={data-url}"
       형태로 생성합니다.
    """
    data_list = []
    url = "https://www.customs.go.kr/kcs/na/ntt/selectNttList.do"

    # 폼 데이터에 포함된 필수 파라미터 (페이지 이동 시 currPage만 변경)
    payload_common = {
        "confmUseAt": "N",
        "bbsId": "1341",
        "minSn": "0",
        "menuId": "2889",
        "newHour": "24",
        "cntntsId": "1341",
        "maxSn": "10",
        "manageAt": "N",
        "sysId": "kcs",
        "menuTy": "BBS",
        "listUseAt": "Y",
        "bbsTy": "NORMAL",
        "useAt": "Y",
        "mi": "2889",
        "noticeAt": "Y"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.customs.go.kr/kcs/na/ntt/selectNttList.do?mi=2889&bbsId=1341"
    }

    for page in range(1, 151):
        # 업데이트된 페이지 번호를 포함한 폼 데이터 준비
        payload = payload_common.copy()
        payload["currPage"] = str(page)

        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                response = requests.post(url, data=payload, headers=headers, timeout=10)
                response.raise_for_status()
                break  # 성공 시 while 루프 탈출
            except Exception as e:
                retry_count += 1
                logging.error(f"페이지 {page} 에서 에러 발생: {e}. 재시도 {retry_count}/{max_retries}")
                time.sleep(2)
        if retry_count == max_retries:
            logging.error(f"페이지 {page} 을(를) {max_retries}회 재시도 후 실패하여 넘어갑니다.")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        # 게시글 리스트가 들어 있는 테이블은 클래스명이 "bbList" 입니다.
        table = soup.find("table", class_="bbsList")
        if not table:
            logging.info(f"페이지 {page} 에서 게시판 리스트 영역을 찾을 수 없습니다.")
            continue
        tbody = table.find("tbody")
        if not tbody:
            logging.info(f"페이지 {page} 에서 tbody 영역을 찾을 수 없습니다.")
            continue

        rows = tbody.find_all("tr")
        if not rows:
            logging.info(f"페이지 {page} 에서 게시글을 찾을 수 없습니다.")
            continue

        for row in rows:
            # 제목 및 상세 링크 추출: <td data-table="subject">
            subject_td = row.find("td", {"data-table": "subject"})
            if subject_td:
                a_tag = subject_td.find("a")
                if a_tag:
                    title = a_tag.get("title", "").strip()
                    data_id = a_tag.get("data-id", "").strip()
                    token = a_tag.get("data-url", "").strip()
                    if data_id and token:
                        detail_link = f"https://www.customs.go.kr/kcs/na/ntt/selectNttInfo.do?nttSn={data_id}&nttSnUrl={token}"
                    else:
                        detail_link = ""
                else:
                    title = ""
                    detail_link = ""
            else:
                title = ""
                detail_link = ""

            # 등록일 추출: <td data-table="date">
            date_td = row.find("td", {"data-table": "date"})
            reg_date = date_td.get_text(strip=True) if date_td else ""

            if title:  # 제목이 있으면 데이터 저장
                data_list.append({
                    "제목": title,
                    "등록일": reg_date,
                    "링크": detail_link
                })

        logging.info(f"관세청 페이지 {page} 크롤링 완료, {len(rows)}개 행 처리됨.")
        # 서버 부하를 줄이기 위해 잠시 대기 (필요 시)
        # time.sleep(0.3)

    return data_list


if __name__ == "__main__":
    results = scrape_customs_data()
    logging.info(f"총 항목 수: {len(results)}")
    for item in results[:5]:
        logging.info(item)
