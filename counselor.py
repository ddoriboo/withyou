import streamlit as st
import time
from openai import OpenAI
import os
import json
import hashlib
from datetime import datetime

# Set up OpenAI client
openai_api_key = st.secrets["openai"]["api_key"]
assistant_id = st.secrets["openai"]["assistant_id"]
client = OpenAI(api_key=openai_api_key)

# Check if Google Sheets credentials are available
use_google_sheets = False
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    gc = gspread.authorize(creds)
    
    # Open the Google Sheet
    sheet_url = "https://docs.google.com/spreadsheets/d/1G2hSp9NScSyQvVHAaWep2uiWm1vMUGA2Qb7JY_zAVnk/edit?usp=sharing"
    sheet = gc.open_by_url(sheet_url).sheet1
    use_google_sheets = True
except Exception as e:
    st.warning("Google Sheets integration is not available. Chats will be saved locally.")

# Helper functions
def save_chat_history(user_id, history):
    os.makedirs('chat_histories', exist_ok=True)
    with open(f'chat_histories/{user_id}.json', 'w') as f:
        json.dump(history, f)

def load_chat_history(user_id):
    try:
        with open(f'chat_histories/{user_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return [{"role": "assistant", "content": "안녕하세요! 저는 위드유 상담사입니다.💕 오늘 상담을 도와드리게 되어 기쁩니다. 먼저, 제가 당신을 어떻게 불러드리면 될까요? 이름이나 별명도 괜찮아요😊"}]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_user_credentials(username, password):
    hashed_password = hash_password(password)
    os.makedirs('user_credentials', exist_ok=True)
    with open('user_credentials/users.json', 'a+') as f:
        f.seek(0)
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            users = {}
        users[username] = hashed_password
        f.seek(0)
        f.truncate()
        json.dump(users, f)

def verify_user(username, password):
    try:
        with open('user_credentials/users.json', 'r') as f:
            users = json.load(f)
            return username in users and users[username] == hash_password(password)
    except FileNotFoundError:
        return False

def erase_chat_history(user_id):
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 위드유 상담사입니다.💕 오늘 상담을 도와드리게 되어 기쁩니다. 먼저, 제가 당신을 어떻게 불러드리면 될까요? 이름이나 별명도 괜찮아요😊"}]
    save_chat_history(user_id, st.session_state.messages)
    st.session_state.thread_id = None

def save_chat(user_id, messages):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages])
    
    if use_google_sheets:
        sheet.append_row([timestamp, user_id, content])
    else:
        os.makedirs('saved_chats', exist_ok=True)
        filename = f'saved_chats/{user_id}_{timestamp.replace(":", "-")}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return timestamp

# [Keep the show_login and show_register functions as they were]

def main():
    st.title("💬 캠퍼스 상담사 위드유")
    st.caption("🚀 대학생의 자기효능감을 진단하고 개선하는 최고의 어드바이저입니다.")

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.session_state.show_register = False

    if not st.session_state.authenticated:
        if st.session_state.show_register:
            show_register()
        else:
            show_login()
        return

    # [Keep the chat interface code as it was]

    # Chat management buttons in sidebar
    st.sidebar.markdown("### 채팅 관리")
    
    if st.sidebar.button("대화 기록 지우기", key="erase_chat"):
        erase_chat_history(st.session_state.user_id)
        st.experimental_rerun()
    
    if st.sidebar.button("대화 저장하기", key="save_chat"):
        timestamp = save_chat(st.session_state.user_id, st.session_state.messages)
        if use_google_sheets:
            st.sidebar.success(f"대화가 Google Sheet에 저장되었습니다. (저장 시간: {timestamp})")
        else:
            st.sidebar.success(f"대화가 로컬 파일에 저장되었습니다. (저장 시간: {timestamp})")
    
    if st.sidebar.button("로그아웃", key="logout"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.experimental_rerun()

if __name__ == "__main__":
    main()
