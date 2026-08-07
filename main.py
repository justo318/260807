import os
import re
import datetime
import urllib3
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Disable SSL warnings for government websites with self-signed or legacy certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

KEYWORDS = ["청년", "복지", "지원", "인공지능", "AI", "교육"]

def is_matching_keyword(title: str) -> bool:
    """Check if title contains any target keyword."""
    if not title:
        return False
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in KEYWORDS)

def parse_date(date_str: str) -> datetime.date:
    """Parse date string into datetime.date object."""
    if not date_str:
        return None
    # Match YYYY.MM.DD or YYYY-MM-DD or YYYY/MM/DD
    match = re.search(r'(\d{4})[-.\/](\d{1,2})[-.\/](\d{1,2})', date_str.strip())
    if match:
        year, month, day = map(int, match.groups())
        return datetime.date(year, month, day)
    return None

def fetch_mois_notices(cutoff_date: datetime.date):
    """Scrape 행정안전부 notices."""
    items = []
    base_url = "https://www.mois.go.kr"
    list_url = "https://www.mois.go.kr/frt/bbs/type013/commonSelectBoardList.do"
    
    for page in range(1, 4):  # Check first 3 pages
        params = {
            'bbsId': 'BBSMSTR_000000000006',
            'pageIndex': page
        }
        try:
            res = requests.get(list_url, params=params, headers=HEADERS, verify=False, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                table = soup.find('div', class_='table_area')
            if not table:
                continue
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) < 4:
                    continue
                
                # Check link & title
                a_tag = row.find('a')
                if not a_tag:
                    continue
                    
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                if href.startswith('javascript'):
                    # Handle onclick or JS links if present
                    match_id = re.search(r"fn_egov_inqire_notice\('([^']+)','([^']+)'\)", href)
                    if match_id:
                        ntt_id = match_id.group(1)
                        link = f"{base_url}/frt/bbs/type013/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000006&nttId={ntt_id}"
                    else:
                        link = list_url
                elif href.startswith('/'):
                    link = base_url + href
                elif href.startswith('http'):
                    link = href
                else:
                    link = f"{base_url}/frt/bbs/type013/{href}"

                # Find date column (usually 4th or 5th col)
                reg_date = None
                for col in cols:
                    parsed = parse_date(col.get_text(strip=True))
                    if parsed:
                        reg_date = parsed
                        break
                        
                if reg_date and reg_date < cutoff_date:
                    continue  # Older than 30 days
                    
                if is_matching_keyword(title):
                    items.append({
                        '기관명': '행정안전부',
                        '공고제목': title,
                        '등록일': reg_date.strftime('%Y-%m-%d') if reg_date else '-',
                        '마감일': '상세페이지 참조',
                        '링크': link
                    })
        except Exception as e:
            print(f"[행정안전부] 페이지 {page} 수집 중 오류: {e}")
            
    return items

def fetch_mss_notices(cutoff_date: datetime.date):
    """Scrape 중소벤처기업부 notices."""
    items = []
    base_url = "https://www.mss.go.kr"
    list_url = "https://www.mss.go.kr/site/smba/ex/bbs/List.do"
    
    for page in range(1, 4):
        params = {
            'cbIdx': '310',
            'pageIndex': page
        }
        try:
            res = requests.get(list_url, params=params, headers=HEADERS, verify=False, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                continue
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                
                a_tag = row.find('a')
                if not a_tag:
                    continue
                    
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                
                if href.startswith('/'):
                    link = base_url + href
                elif href.startswith('http'):
                    link = href
                else:
                    link = f"{base_url}/site/smba/ex/bbs/{href}"

                reg_date = None
                for col in cols:
                    parsed = parse_date(col.get_text(strip=True))
                    if parsed:
                        reg_date = parsed
                        break
                        
                if reg_date and reg_date < cutoff_date:
                    continue
                    
                if is_matching_keyword(title):
                    items.append({
                        '기관명': '중소벤처기업부',
                        '공고제목': title,
                        '등록일': reg_date.strftime('%Y-%m-%d') if reg_date else '-',
                        '마감일': '상세페이지 참조',
                        '링크': link
                    })
        except Exception as e:
            print(f"[중소벤처기업부] 페이지 {page} 수집 중 오류: {e}")
            
    return items

def fetch_moel_notices(cutoff_date: datetime.date):
    """Scrape 고용노동부 notices."""
    items = []
    base_url = "https://www.moel.go.kr"
    list_url = "https://www.moel.go.kr/news/notice/noticeList.do"
    
    for page in range(1, 4):
        params = {
            'pageIndex': page
        }
        try:
            res = requests.get(list_url, params=params, headers=HEADERS, verify=False, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                continue
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                
                a_tag = row.find('a')
                if not a_tag:
                    continue
                    
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                
                if href.startswith('/'):
                    link = base_url + href
                elif href.startswith('http'):
                    link = href
                else:
                    link = f"{base_url}/news/notice/{href}"

                reg_date = None
                for col in cols:
                    parsed = parse_date(col.get_text(strip=True))
                    if parsed:
                        reg_date = parsed
                        break
                        
                if reg_date and reg_date < cutoff_date:
                    continue
                    
                if is_matching_keyword(title):
                    items.append({
                        '기관명': '고용노동부',
                        '공고제목': title,
                        '등록일': reg_date.strftime('%Y-%m-%d') if reg_date else '-',
                        '마감일': '상세페이지 참조',
                        '링크': link
                    })
        except Exception as e:
            print(f"[고용노동부] 페이지 {page} 수집 중 오류: {e}")
            
    return items

def main():
    today = datetime.date.today()
    cutoff_date = today - datetime.timedelta(days=30)
    
    print(f"[{today.strftime('%Y-%m-%d')}] 공고 수집 시작 (수집 기준: 최근 30일 이내 - {cutoff_date.strftime('%Y-%m-%d')} 이후)...")
    
    mois_data = fetch_mois_notices(cutoff_date)
    print(f"▶ 행정안전부 수집 건수: {len(mois_data)}건")
    
    mss_data = fetch_mss_notices(cutoff_date)
    print(f"▶ 중소벤처기업부 수집 건수: {len(mss_data)}건")
    
    moel_data = fetch_moel_notices(cutoff_date)
    print(f"▶ 고용노동부 수집 건수: {len(moel_data)}건")
    
    combined_data = mois_data + mss_data + moel_data
    print(f"▶ 총 합계 건수: {len(combined_data)}건")
    
    # Create DataFrames
    df_combined = pd.DataFrame(combined_data)
    df_mois = pd.DataFrame(mois_data)
    df_mss = pd.DataFrame(mss_data)
    df_moel = pd.DataFrame(moel_data)
    
    # Ensure default columns if empty
    columns = ['기관명', '공고제목', '등록일', '마감일', '링크']
    for df in [df_combined, df_mois, df_mss, df_moel]:
        if df.empty:
            for col in columns:
                df[col] = []
        else:
            df = df[columns]

    filename = f"타기관벤치마킹_{today.strftime('%Y%m%d')}.xlsx"
    
    # Export to Excel with multiple sheets
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_combined.to_excel(writer, sheet_name='통합 비교표', index=False)
        df_mois.to_excel(writer, sheet_name='행정안전부', index=False)
        df_mss.to_excel(writer, sheet_name='중소벤처기업부', index=False)
        df_moel.to_excel(writer, sheet_name='고용노동부', index=False)
        
    print(f"성공적으로 엑셀 파일이 저장되었습니다: {filename}")

if __name__ == '__main__':
    main()
