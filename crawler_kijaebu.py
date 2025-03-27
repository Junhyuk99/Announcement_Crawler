import re
import time
import requests
from bs4 import BeautifulSoup

def scrape_moef_data():
    """
    1페이지부터 80페이지까지 MOEF 공지사항을 크롤링하여
    제목, 최종 URL, 날짜, 부서명을 리스트(딕셔너리 형태)로 반환합니다.
    """
    data_list = []
    base_url = "https://www.moef.go.kr/nw/nes/nesdta.do?searchBbsId=MOSFBBS_000000000030&menuNo=4050100&pageIndex="
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )
    }

    # 페이지 진행
    for page in range(1, 81):
        url = base_url + str(page)
        while True:
            try:
                # 타임아웃을 10초로 설정하여 요청 시도
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
                break  # 성공하면 while 루프 탈출
            except requests.exceptions.RequestException as e:
                print(f"Page {page} 에서 에러 발생: {e}. 5초 후 재시도합니다.")
                time.sleep(5)  # 5초 후 재시도

        soup = BeautifulSoup(response.text, "html.parser")
        ul = soup.find("ul", class_="boardType3 mt50")
        if not ul:
            # 공지사항 목록을 찾지 못한 경우 건너뛰지 않고, 재시도 대신 다음 페이지로 진행
            print(f"Page {page} 에서 공지사항 목록을 찾지 못했습니다.")
            continue

        li_elements = ul.find_all("li")
        for li in li_elements:
            a_tag = li.find("h3").find("a")
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href")

            # javascript 호출 형식 링크라면 실제 상세 URL로 변환
            if link.startswith("javascript:"):
                pattern = r"fn_egov_select\('([^']+)','([^']+)'\)"
                match = re.search(pattern, link)
                if match:
                    ntt_id = match.group(1)
                    bbs_id = match.group(2)
                    link = (
                        f"https://www.moef.go.kr/nw/nes/detailNesDtaView.do?"
                        f"searchBbsId1={bbs_id}&searchNttId1={ntt_id}&menuNo=4050100"
                    )

            date = li.find("span", class_="date").get_text(strip=True)
            depart = li.find("span", class_="depart").get_text(strip=True)

            data_list.append({
                "제목": title,
                "링크": link,
                "날짜": date,
                "부서명": depart
            })
        print(f"기획재정부 페이지 {page} 크롤링 완료")
    return data_list

if __name__ == "__main__":
    results = scrape_moef_data()
    print(f"총 항목 수: {len(results)}")
    for item in results[:5]:
        print(item)
