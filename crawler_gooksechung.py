# crawler_gooksechung.py
import requests
from bs4 import BeautifulSoup
from stqdm import stqdm  # stqdm 임포트


def scrape_nts_data():
    """
    https://www.nts.go.kr/nts/na/ntt/selectNttList.do 페이지에서
    1페이지부터 59페이지까지 크롤링하여 각 공지사항의 제목, 작성일자, 링크를
    딕셔너리 형태의 리스트로 반환합니다.

    - 제목: <td data-table="subject" class="bbs_tit"> 내부의 <a> 태그의 title 속성
    - 작성일자: <td data-table="date">의 텍스트
    - 링크: <a> 태그의 data-id 값을 이용하여
      "https://nts.go.kr/nts/na/ntt/selectNttInfo.do?nttSn={data_id}&mi=2207" 형태로 생성
    """
    data_list = []
    url = "https://www.nts.go.kr/nts/na/ntt/selectNttList.do"

    # 폼에 포함되어 있는 모든 파라미터
    payload_common = {
        "listUseAt": "Y",
        "manageAt": "N",
        "confmUseAt": "N",
        "transIp": "https://doc.nts.go.kr:8080",
        "bbsTy": "NORMAL",
        "newHour": "24",
        "maxSn": "10",
        "authorAt": "N",
        "noticeAt": "Y",
        "synapViewerAt": "Y",
        "mi": "2207",
        "filepathIp": "http://www.nts.go.kr",
        "useAt": "Y",
        "minSn": "0",
        "bbsId": "1011"
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        ),
        # Referer를 지정하면 정상적인 페이지 로딩에 도움이 될 수 있습니다.
        "Referer": "https://www.nts.go.kr/nts/na/ntt/selectNttList.do?mi=2207&bbsId=1011"
    }

    # 1페이지부터 59페이지까지 순회
    for page in stqdm(range(1, 60), desc="국세청 공지사항 가져오는 중.."):
        # 페이지 번호를 포함한 폼 데이터 준비
        payload = payload_common.copy()
        payload["currPage"] = str(page)

        response = requests.post(url, data=payload, headers=headers)
        if response.status_code != 200:
            print(f"Page {page}: HTTP error {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # 페이지 내 게시판 리스트가 들어 있는 컨테이너 (div.bbs_ListA)
        container = soup.find("div", class_="bbs_ListA")
        if not container:
            print(f"Page {page}: div.bbs_ListA not found")
            continue

        table = container.find("table")
        if not table:
            print(f"Page {page}: table not found")
            continue

        tbody = table.find("tbody")
        if not tbody:
            print(f"Page {page}: tbody not found")
            continue

        rows = tbody.find_all("tr")
        if not rows:
            print(f"Page {page}: no rows found")
            continue

        for row in rows:
            # 제목과 링크 추출: <td data-table="subject" class="bbs_tit">
            subject_td = row.find("td", {"data-table": "subject", "class": "bbs_tit"})
            if subject_td:
                a_tag = subject_td.find("a", class_="nttInfoBtn")
                if a_tag:
                    title = a_tag.get("title", "").strip()
                    data_id = a_tag.get("data-id", "").strip()
                    link = f"https://nts.go.kr/nts/na/ntt/selectNttInfo.do?nttSn={data_id}&mi=2207" if data_id else ""
                else:
                    title, link = "", ""
            else:
                title, link = "", ""

            # 작성일자 추출: <td data-table="date">
            date_td = row.find("td", {"data-table": "date"})
            date_text = date_td.get_text(strip=True) if date_td else ""

            if title:
                data_list.append({
                    "제목": title,
                    "작성일자": date_text,
                    "링크": link
                })

        print(f"Page {page} crawled, processed {len(rows)} rows.")

    return data_list


if __name__ == "__main__":
    results = scrape_nts_data()
    print(f"총 항목 수: {len(results)}")
    for item in results[:5]:
        print(item)
