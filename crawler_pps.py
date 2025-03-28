import re
import time
import logging
import requests
from bs4 import BeautifulSoup

# 로깅 설정: INFO 레벨 이상의 메시지를 콘솔에 출력
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_pps_data():
    """
    https://www.pps.go.kr/kor/bbs/list.do?key=00641 페이지에서 크롤링합니다.

    각 페이지의 URL은:
      https://www.pps.go.kr/kor/bbs/list.do?key=00641&pageIndex={페이지번호}
    (페이지 이동은 fn_egov_link_page(pageNo)를 통해 이루어짐)

    각 게시글은 <div class="board_list"> 내부 <tbody>의 <tr> 요소에 위치합니다.

    - 제목: <td class="title" style="text-align:left;"> 내부의 <div class="viewbox">의 텍스트
    - 등록일: 각 행의 5번째 <td> 요소의 텍스트
    - 링크: <a href="#none" onclick="goView('2503270008', '0001');"> 에서
             정규표현식으로 첫 번째 인자(key)를 추출하여,
             상세페이지 URL "https://www.pps.go.kr/kor/bbs/view.do?bbsSn={key}&key=00641"로 구성합니다.

    총 175페이지에 대해 데이터를 수집합니다.
    """
    base_url = "https://www.pps.go.kr/kor/bbs/list.do?key=00641"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )
    }

    results = []

    # 1페이지부터 175페이지까지 반복
    for page in range(1, 176):
        url = f"{base_url}&pageIndex={page}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"페이지 {page} 에서 에러 발생: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        board_list_div = soup.find("div", class_="board_list")
        if not board_list_div:
            logging.info(f"페이지 {page} 에서 게시판 리스트 영역을 찾을 수 없습니다.")
            continue

        tbody = board_list_div.find("tbody")
        if not tbody:
            logging.info(f"페이지 {page} 에서 tbody 영역을 찾을 수 없습니다.")
            continue

        rows = tbody.find_all("tr")
        if not rows:
            logging.info(f"페이지 {page} 에서 게시글을 찾을 수 없습니다.")
            continue

        for row in rows:
            # 제목 추출
            title_td = row.find("td", class_="title", style="text-align:left;")
            if not title_td:
                continue
            viewbox_div = title_td.find("div", class_="viewbox")
            if viewbox_div:
                title_text = viewbox_div.get_text(strip=True)
            else:
                title_text = title_td.get_text(strip=True)

            # 등록일 추출: 각 행의 5번째 <td> 요소에서 가져오기
            tds = row.find_all("td")
            if len(tds) >= 5:
                reg_date = tds[4].get_text(strip=True)
            else:
                reg_date = ""

            # 링크 추출: onclick 속성에서 goView('키', 'stype') 형식으로 추출
            a_tag = title_td.find("a")
            if a_tag:
                onclick_attr = a_tag.get("onclick", "")
                match = re.search(r"goView\('([^']+)',\s*'([^']*)'\)", onclick_attr)
                if match:
                    key_val = match.group(1)
                    link_url = f"https://www.pps.go.kr/kor/bbs/view.do?bbsSn={key_val}&key=00641"
                else:
                    link_url = ""
            else:
                link_url = ""

            results.append({
                "제목": title_text,
                "등록일": reg_date,
                "링크": link_url
            })
        logging.info(f"조달청 페이지 {page} 크롤링 완료, {len(rows)}개 행 처리됨.")
        # time.sleep(0.3)  # 서버 부담 완화를 위한 대기 (필요시 활성화)

    return results

if __name__ == "__main__":
    data = scrape_pps_data()
    logging.info(f"총 항목 수: {len(data)}")
    for item in data[:5]:
        logging.info(item)
