# 필요한 모듈들을 임포트합니다.
import streamlit as st
from streamlit.hashing import _CodeHasher
import time
import stock_app_login
import stock_app_dashboard
import stock_app_testing
import boto3
import socket
import os
import getpass
import pandas as pd 

import sqlite3
from sqlite3 import Error

# 데이터베이스 파일의 위치를 설정합니다.
DATABASE_FILE_LOCATION = os.getcwd()+"\pythonsqlite.db" 

# 사용할 테이블의 이름을 사전 형태로 저장합니다.
TABLE_DIC = {'stocks':'stocks','stock_trans':'stock_transaction'} 

# SQLite 데이터베이스 연결을 생성하는 함수입니다.
def create_connection(db_file):
    """SQLite 데이터베이스에 연결을 생성합니다."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)

        # 데이터베이스에 필요한 테이블이 없으면 생성합니다.
        if (conn.execute("SELECT name FROM sqlite_master").fetchall() not in TABLE_DIC.values()):
            print("Creating "+ str(TABLE_DIC.values()) +" Table")

        # 주식 거래 테이블 생성
        conn.execute("""CREATE TABLE IF NOT EXISTS """ + TABLE_DIC['stock_trans'] + """ (    
                    Stock                       TEXT     PRIMARY KEY     NOT NULL,
                    Bought_Price                REAL                     NOT NULL,
                    Currency                    TEXT                     NOT NULL,
                    Fees                        REAL                     NOT NULL,
                    Quantity                    REAL                     NOT NULL);""")
    
        # 주식 정보 테이블 생성
        conn.execute("""CREATE TABLE IF NOT EXISTS """ + TABLE_DIC['stocks'] + """ (
                    Stock                       TEXT     PRIMARY KEY     NOT NULL,
                    Bought_Price_Avg            REAL                     NOT NULL,
                    Currency                    TEXT                     NOT NULL,
                    Fees                        REAL                     NOT NULL,
                    Quantity                    REAL                     NOT NULL);""")

        print("Successfully created "+ str(TABLE_DIC.values()) +" Table")

    except Error as e:
        print(e)
    finally:
        # 연결이 열려있으면 닫습니다.
        if conn:
            conn.close()

# 애플리케이션의 메인 함수입니다.
def main(test):
    st.set_page_config(layout="wide")
    state = _get_state()

    # 페이지를 추가하거나 제거합니다.
    pages = {
        "Login": page_login,
    }

    create_connection(DATABASE_FILE_LOCATION) 

    # 테스팅 대시보드를 바로 실행하기 위해 로그인 과정을 건너뜁니다.
    if test == "testing_dashboard":
        state.login = True
        state.user_name = getpass.getuser()

    # 로그인 상태라면 로그인 페이지를 제거하고 대시보드와 테스팅 페이지를 추가합니다.
    if state.login:
        pages.pop("Login")
        pages["Dashboard"] = page_dashboard
        pages["Testing"] = page_testing

    st.sidebar.title(":floppy_disk: Dashboard")
    page = st.sidebar.radio("Select your page", tuple(pages.keys()))

    # 선택된 페이지를 세션 상태와 함께 렌더링합니다.
    pages[page](state)

    # 위젯과 관련된 롤백을 방지하기 위해 앱의 마지막에 상태를 동기화해야 합니다.
    state.sync()

# 로그인, 대시보드, 테스팅 페이지를 처리하는 함수들입니다.
def page_login(state):
    stock_app_login.login_process(state)

def page_dashboard(state):
    stock_app_dashboard.dashboard_process(state)

def page_testing(state):
    stock_app_testing.testing_process(state)

# Streamlit 세션 상태를 관리하는 클래스입니다.
class _SessionState:

    def __init__(self, session, hash_funcs):
        """세션 상태 인스
        탄스를 초기화합니다."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "session": session,
            "hash_funcs": hash_funcs,
        }

    def __call__(self, **kwargs):
        """세션 상태 데이터를 업데이트합니다."""
        for item, value in kwargs.items():
            self._state["data"][item] = value

    def __getitem__(self, item):
        """세션 상태 데이터에서 특정 항목을 가져옵니다."""
        return self._state["data"][item]

    def __getattr__(self, item):
        """세션 상태 데이터에서 특정 속성을 가져옵니다."""
        return self._state["data"].get(item, None)

    def __setitem__(self, key, value):
        """세션 상태 데이터에 특정 항목을 설정합니다."""
        self._state["data"][key] = value

    def __setattr__(self, key, value):
        """세션 상태 데이터에 특정 속성을 설정합니다."""
        self._state["data"][key] = value

    def sync(self):
        """세션 상태를 동기화합니다."""
        if self._state["session"] is not None:
            self._state["session"].request_rerun()

    def clear(self):
        """세션 상태 데이터를 초기화합니다."""
        for key in list(self._state["data"].keys()):
            del self._state["data"][key]

# Streamlit 세션 상태를 관리하는 함수입니다.
def _get_state(hash_funcs=None):
    ctx = get_report_ctx()

    if ctx.session_id not in Server.get_current()._session_info_by_id:
        Server.get_current()._session_info_by_id[ctx.session_id] = {}

    if "_custom_session_state" not in Server.get_current()._session_info_by_id[ctx.session_id]:
        Server.get_current()._session_info_by_id[ctx.session_id]["_custom_session_state"] = _SessionState(ctx, hash_funcs)

    return Server.get_current()._session_info_by_id[ctx.session_id]["_custom_session_state"]

# 앱의 메인 함수를 실행합니다.
if __name__ == "__main__":
    main(test="")

