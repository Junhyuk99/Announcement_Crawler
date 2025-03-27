import streamlit as st
import pandas as pd
from stqdm import stqdm
from crawler_kijaebu import scrape_moef_data
from crawler_gooksechung import scrape_nts_data
from crawler_customs import scrape_customs_data
import threading
import schedule
import time
import datetime


def main():
    st.title("공지사항 크롤링 결과")
    # stqdm을 활용하여 크롤링 진행 상황을 표시합니다.
    data_tasks = [
        ("moef", load_moef_data),
        ("nts", load_nts_data),
        ("customs", load_customs_data)
    ]
    results = {}
    for key, task in stqdm(data_tasks, desc="데이터 크롤링 중..."):
        results[key] = task()

    moef_data = results["moef"]
    nts_data = results["nts"]
    customs_data = results["customs"]

    # 좌측 사이드바 메뉴로 데이터 선택
    st.sidebar.title("데이터 선택")
    option = st.sidebar.radio("크롤링 데이터", ("기획재정부 공지사항", "국세청 공지사항", "관세청 공지사항"))

    if option == "기획재정부 공지사항":
        st.header("기획재정부 공지사항")
        data = moef_data
        page_key = "moef_page"  # 기획재정부 탭에 사용할 쿼리 파라미터 키
    elif option == "국세청 공지사항":
        st.header("국세청 공지사항")
        data = nts_data
        page_key = "nts_page"  # 국세청 탭에 사용할 쿼리 파라미터 키
    else:
        st.header("관세청 공지사항")
        data = customs_data
        page_key = "customs_page"  # 관세청 탭에 사용할 쿼리 파라미터 키

    if not data:
        st.write("크롤링된 데이터가 없습니다.")
        return

    # 표 상단에 검색창을 오른쪽에 배치
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("")  # 왼쪽 공간 비워둠
    with col2:
        search_keyword = st.text_input("제목 검색", "")

    # DataFrame 생성 후 제목 검색어가 있다면 필터링
    df = pd.DataFrame(data)
    if search_keyword:
        df = df[df["제목"].str.contains(search_keyword, case=False)]

    st.write("총 공지사항 수:", len(df))

    # 제목을 하이퍼링크로 변환 (클릭 시 새 탭에서 상세페이지 열림)
    df["제목"] = df.apply(
        lambda row: f'<a href="{row["링크"]}" target="_blank">{row["제목"]}</a>',
        axis=1
    )
    # 표에서 "링크" 컬럼은 제거
    df.drop(columns=["링크"], inplace=True)

    # 페이지네이션 설정 (한 페이지에 10개씩)
    current_page = get_current_page(page_key)
    items_per_page = 10
    total_pages = (len(df) - 1) // items_per_page + 1

    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    df_page = df.iloc[start_idx:end_idx]

    st.markdown(df_page.to_html(escape=False, index=False), unsafe_allow_html=True)
    pagination_ui(current_page, total_pages, page_key)


@st.cache_data(show_spinner=False)
def load_moef_data():
    return scrape_moef_data()


@st.cache_data(show_spinner=False)
def load_nts_data():
    return scrape_nts_data()


@st.cache_data(show_spinner=False)
def load_customs_data():
    return scrape_customs_data()


def get_current_page(key="page"):
    """
    URL 쿼리 파라미터에서 지정한 key의 값을 읽어 정수로 반환.
    값이 없거나 변환 실패 시 기본 1을 반환합니다.
    """
    query_params = st.query_params
    if key in query_params:
        try:
            return int(query_params[key])
        except:
            return 1
    else:
        return 1


def pagination_ui(current_page, total_pages, key="page", max_pages_to_show=5):
    """
    중앙 정렬된 HTML/CSS 페이지네이션 UI를 생성합니다.
    링크는 ?{key}=N 형태의 쿼리 파라미터를 사용합니다.
    """
    pagination_html = """
    <style>
    .pagination-container {
      width: 100%;
      text-align: center;
      margin-top: 20px;
    }
    .pagination {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 4px;
    }
    .pagination a, .pagination strong {
      color: black;
      padding: 6px 12px;
      text-decoration: none;
      border: 1px solid #ddd;
    }
    .pagination strong {
      background-color: #4CAF50;
      color: white;
      border: 1px solid #4CAF50;
    }
    .pagination a:hover:not(.active) {
      background-color: #ddd;
    }
    </style>
    """
    start_page = max(1, current_page - max_pages_to_show // 2)
    end_page = min(total_pages, start_page + max_pages_to_show - 1)
    if end_page - start_page < max_pages_to_show - 1:
        start_page = max(1, end_page - max_pages_to_show + 1)

    page_links = []
    page_links.append(f'<a href="?{key}=1" target="_self"><<</a>')
    prev_page = max(1, current_page - 1)
    page_links.append(f'<a href="?{key}={prev_page}" target="_self"><</a>')
    for p in range(start_page, end_page + 1):
        if p == current_page:
            page_links.append(f'<strong>{p}</strong>')
        else:
            page_links.append(f'<a href="?{key}={p}" target="_self">{p}</a>')
    next_page = min(total_pages, current_page + 1)
    page_links.append(f'<a href="?{key}={next_page}" target="_self">></a>')
    page_links.append(f'<a href="?{key}={total_pages}" target="_self">>></a>')
    pagination_html += f'<div class="pagination-container"><div class="pagination">{"".join(page_links)}</div></div>'
    st.markdown(pagination_html, unsafe_allow_html=True)

def update_data_job():
    """
    매일 오후 6시(KST)에 실행되어 캐시 데이터를 초기화하여
    새로운 크롤링 데이터를 가져오도록 합니다.
    """
    load_moef_data.clear()
    load_nts_data.clear()
    load_customs_data.clear()
    print("데이터 업데이트 작업 실행:", datetime.datetime.now())


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    # 매일 한국시간 오후 6시에 데이터 업데이트 작업 예약
    schedule.every().day.at("18:00").do(update_data_job)
    # 별도 스레드에서 스케줄러 실행
    threading.Thread(target=run_schedule, daemon=True).start()
    main()
