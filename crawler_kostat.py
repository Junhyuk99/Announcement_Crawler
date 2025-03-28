import re
import logging
import requests
from bs4 import BeautifulSoup

# 로깅 설정: INFO 레벨 이상의 메시지를 콘솔에 출력
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def scrape_kostat_data():
    """
    크롤링 대상:
      https://sri.kostat.go.kr/board.es?mid=a10306020000&bid=a103060100&ref_bid=106,108
    페이지 이동은 POST 방식으로, 폼 데이터의 nPage 값을 변경하여 1페이지부터 39페이지까지 데이터를 수집합니다.

    각 게시글은 <div class="board_list_01"> 내의 <ul>의 <li> 요소에 위치합니다.

    - 제목: <a class="board_link">의 하위 <span>의 텍스트
    - 등록일: 해당 게시글 내 <div class="board_class">의 <ul> 안에서,
             <li> 요소 중 <strong>게시일</strong>가 포함된 항목의 <span>의 텍스트
    - 링크: <a class="board_link">의 href 속성에서 "javascript:addSearchParam('URL');" 형태의
             URL 인자를 추출한 후, 앞에 "https://sri.kostat.go.kr/"를 붙여 최종 URL로 구성합니다.
    """
    base_url = "https://sri.kostat.go.kr/board.es?mid=a10306020000&bid=a103060100&ref_bid=106,108"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # 폼 데이터 기본값 (페이지 이동 시 nPage만 변경)
    payload_common = {
        "mid": "a10306020000",
        "bid": "a103060100",
        "nPage": "1",  # 페이지 번호 (변경됨)
        "b_list": "10",
        "orderby": "",
        "dept_code": "",
        "tag": "",
        "list_no": "",
        "act": "list",
        "actionURL": "/board.es?mid=a10306020000&bid=a103060100",
        "ref_bid": "106,108"
    }

    results = []

    for page in range(1, 40):  # 1페이지부터 39페이지까지
        payload = payload_common.copy()
        payload["nPage"] = str(page)

        try:
            response = requests.post(base_url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"페이지 {page} 요청 에러: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        board_list_div = soup.find("div", class_="board_list_01")
        if not board_list_div:
            logging.error(f"페이지 {page}: board_list_01 영역을 찾을 수 없습니다.")
            continue
        ul = board_list_div.find("ul")
        if not ul:
            logging.error(f"페이지 {page}: 게시글 목록 ul 요소를 찾을 수 없습니다.")
            continue
        li_elements = ul.find_all("li")
        if not li_elements:
            logging.info(f"페이지 {page}: 게시글 항목이 없습니다.")
            continue

        for li in li_elements:
            # 제목 추출: <a class="board_link">의 하위 <span> 텍스트
            a_tag = li.find("a", class_="board_link")
            if not a_tag:
                continue
            title_span = a_tag.find("span")
            title_text = title_span.get_text(strip=True) if title_span else ""

            # 링크 추출: href 속성에서 addSearchParam 함수의 인자로 전달된 URL 추출 후 접두사 붙이기
            href = a_tag.get("href", "")
            match = re.search(r"addSearchParam\('([^']+)'\)", href)
            if match:
                extracted_url = match.group(1)
                link_url = f"https://sri.kostat.go.kr/{extracted_url.lstrip('/')}"
            else:
                link_url = ""

            # 등록일 추출: <div class="board_class"> 내의 <ul>에서, <li> 중 "게시일"이 포함된 항목의 <span> 텍스트
            reg_date = ""
            board_class_div = li.find("div", class_="board_class")
            if board_class_div:
                ul_class = board_class_div.find("ul")
                if ul_class:
                    li_items = ul_class.find_all("li")
                    for li_item in li_items:
                        strong_tag = li_item.find("strong")
                        if strong_tag and "게시일" in strong_tag.get_text():
                            span_tag = li_item.find("span")
                            if span_tag:
                                reg_date = span_tag.get_text(strip=True)
                            break

            results.append({
                "제목": title_text,
                "등록일": reg_date,
                "링크": link_url
            })

        logging.info(f"통계청 페이지 {page} 크롤링 완료, 총 {len(results)}개 행 처리됨.")

    logging.info(f"총 {len(results)}개의 게시글 크롤링 완료.")
    return results


if __name__ == "__main__":
    data = scrape_kostat_data()
    for item in data[:5]:
        logging.info(item)
