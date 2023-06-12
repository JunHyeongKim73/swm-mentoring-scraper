import os
import requests
import json
import re
import time
import smtplib
import urllib3
from datetime import datetime
from email.mime.text import MIMEText

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


if __name__ == "__main__":
    SWM_URL = "https://www.swmaestro.org"
    MAIN_URL = "https://www.swmaestro.org/sw/member/user/forLogin.do?menuNo=200025"
    LOGIN_READY_URL = "https://www.swmaestro.org/sw/member/user/toLogin.do"
    LOGIN_URL = "https://www.swmaestro.org/sw/login.do"
    SEARCH_URL = "https://www.swmaestro.org/sw/mypage/mentoLec/list.do?menuNo=200046"

    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")

    TIME_TO_SLEEP = 10 * 60  # seconds

    SEND_EMAIL = os.getenv("SEND_EMAIL")
    APP_PASSWORD_OF_SEND_EMAIL = os.getenv("APP_PASSWORD_OF_SEND_EMAIL")
    RECV_EMAIL = os.getenv("RECV_EMAIL")

    saved_latest_mentoring = ""

    while True:

        # Create a session object
        session = requests.Session()

        # Send a GET request to the login page to get any required CSRF tokens or cookies
        response = session.get(MAIN_URL, verify=False)
        _, jsessionid = response.cookies.items()[0]

        # Extract the CSRF token from the response
        csrf_token = response.text.split('name="csrfToken" id="csrfToken" value="')[1].split('"')[0]

        data = {
            "csrfToken": csrf_token,
            "username": USERNAME,
            "password": PASSWORD
        }

        response = session.post(LOGIN_READY_URL, data=data, verify=False)
        encrypted_password = response.text.split("name='password' value='")[1].split("'")[0]

        login_data2 = {
            "password": encrypted_password,
            "username": USERNAME,
        }

        now = datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        response = session.post(LOGIN_URL, data=login_data2, verify=False)
        if "logout" in response.text:
            print(now + "   로그인 성공")
        else:
            print(now + "   로그인 실패")

        # 멘토링 데이터 조회
        response = session.get(SEARCH_URL, verify=False)
        html = response.text

        pattern = r"resultList.push\(\s*({.*?})\)"
        match = re.findall(pattern, html, re.DOTALL)[0]

        latest_mentoring_string = match.split("},")[0] + "\n}"
        latest_mentoring_json = json.loads(latest_mentoring_string)

        latest_mentoring_title = latest_mentoring_json['subjectTitle']
        latest_mentoring_url = latest_mentoring_json['url']

        if saved_latest_mentoring != latest_mentoring_title:
            print("새 글이 올라왔어요!")

            smtpName = "smtp.gmail.com"  # smtp 서버 주소
            smtpPort = 587  # smtp 포트 번호

            msg = MIMEText(SWM_URL + latest_mentoring_url)  # MIMEText(text , _charset = "utf8")

            msg['Subject'] = latest_mentoring_title
            msg['From'] = SEND_EMAIL
            msg['To'] = RECV_EMAIL

            s = smtplib.SMTP(smtpName, smtpPort)  # 메일 서버 연결
            s.starttls()  # TLS 보안 처리
            s.login(SEND_EMAIL, APP_PASSWORD_OF_SEND_EMAIL)  # 로그인
            s.sendmail(SEND_EMAIL, RECV_EMAIL, msg.as_string())  # 메일 전송, 문자열로 변환해야 합니다.
            s.close()  # smtp 서버 연결을 종료합니다.

            print("메시지 보내기 성공")

            saved_latest_mentoring = latest_mentoring_title

        time.sleep(TIME_TO_SLEEP)
