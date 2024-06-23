import streamlit as st
import time
from openai import OpenAI
import os
import json
import hashlib

# Set up OpenAI client
openai_api_key = st.secrets["openai"]["api_key"]
assistant_id = st.secrets["openai"]["assistant_id"]
client = OpenAI(api_key=openai_api_key)

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
        return [{"role": "assistant", "content": "안녕하세요! 저는 위드유 상담사입니다.💕 오늘 상담을 도와드리게 되어 기쁩니다. 먼저, 제가 당신을 어떻게 불러드리면 될까요? 이름이나 별명도 괜찮아요😊 대화가 끝난 후에는 > 버튼을 눌러 대화를 저장해주세요"}]

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
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 위드유 상담사입니다.💕 오늘 상담을 도와드리게 되어 기쁩니다. 먼저, 제가 당신을 어떻게 불러드리면 될까요? 이름이나 별명도 괜찮아요😊 대화가 끝난 후에는 > 버튼을 눌러 대화를 저장해주세요"}]
    save_chat_history(user_id, st.session_state.messages)
    st.session_state.thread_id = None

def save_chat_as_txt(user_id, messages):
    os.makedirs('saved_chats', exist_ok=True)
    filename = f'saved_chats/{user_id}_{time.strftime("%Y%m%d_%H%M%S")}.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(f"{msg['role'].capitalize()}: {msg['content']}\n\n")
    return filename

def show_login():
    st.sidebar.header("로그인")
    username = st.sidebar.text_input("사용자 이름", key="login_username")
    password = st.sidebar.text_input("비밀번호", type="password", key="login_password")
    if st.sidebar.button("로그인", key="login_button"):
        if verify_user(username, password):
            st.session_state.user_id = username
            st.session_state.authenticated = True
            st.session_state.messages = load_chat_history(username)
            st.session_state.thread_id = None
            st.experimental_rerun()
        else:
            st.sidebar.error("잘못된 사용자 이름 또는 비밀번호입니다.")
    if st.sidebar.button("회원가입으로 전환", key="switch_to_register"):
        st.session_state.show_register = True
        st.experimental_rerun()

def show_register():
    st.sidebar.header("회원가입")
    new_username = st.sidebar.text_input("새 사용자 이름", key="register_username")
    new_password = st.sidebar.text_input("새 비밀번호", type="password", key="register_password")
    if st.sidebar.button("가입하기", key="register_button"):
        save_user_credentials(new_username, new_password)
        st.sidebar.success("회원가입이 완료되었습니다. 로그인해주세요.")
        st.session_state.show_register = False
        st.experimental_rerun()
    if st.sidebar.button("로그인으로 전환", key="switch_to_login"):
        st.session_state.show_register = False
        st.experimental_rerun()

def save_chat_as_txt(user_id, messages):
    filename = f'{user_id}_{time.strftime("%Y%m%d_%H%M%S")}.txt'
    content = ""
    for msg in messages:
        content += f"{msg['role'].capitalize()}: {msg['content']}\n\n"
    return filename, content

def main():
    st.title("💬 캠퍼스 상담사 위드유")
    st.caption("🚀 대학생의 자기효능감을 진단하고 개선하는 최고의 어드바이저입니다.
좌측 상단에 > 를 눌러 회원가입 및 로그인을 해주세요")

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

    # Chat interface
    if 'thread_id' not in st.session_state or st.session_state.thread_id is None:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    thread_id = st.session_state.thread_id

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not openai_api_key:
            st.info("OpenAI API 키를 추가해주세요.")
            st.stop()
        
        if not thread_id:
            st.info("스레드 ID를 추가해주세요.")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        response = client.beta.threads.messages.create(
            thread_id, 
            role="user", 
            content=prompt,
        )
        
        run = client.beta.threads.runs.create(
           thread_id=thread_id,
           assistant_id=assistant_id
         )
        
        run_id = run.id
        
        while True: 
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
                )
            if run.status == "completed":
                break
            else: 
                time.sleep(2)
        
        thread_messages = client.beta.threads.messages.list(thread_id)
        msg = thread_messages.data[0].content[0].text.value

        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

        save_chat_history(st.session_state.user_id, st.session_state.messages)

    # Chat management buttons in sidebar
    st.sidebar.markdown("### 채팅 관리")
    
    if st.sidebar.button("대화 기록 지우기", key="erase_chat"):
        erase_chat_history(st.session_state.user_id)
        st.experimental_rerun()
    
    if st.sidebar.button("대화 저장하기", key="save_chat"):
        filename, content = save_chat_as_txt(st.session_state.user_id, st.session_state.messages)
        st.sidebar.download_button(
        label="대화 내역 다운로드",
        data=content,
        file_name=filename,
        mime="text/plain"
    )
    
    if st.sidebar.button("로그아웃", key="logout"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.experimental_rerun()

if __name__ == "__main__":
    main()
