import streamlit as st
import time
from openai import OpenAI
import os
import json

# Set up OpenAI client
openai_api_key = st.secrets["openai"]["api_key"]
assistant_id = st.secrets["openai"]["assistant_id"]
client = OpenAI(api_key=openai_api_key)

def save_chat_history(user_id, history):
    os.makedirs('chat_histories', exist_ok=True)
    with open(f'chat_histories/{user_id}.json', 'w') as f:
        json.dump(history, f)

def load_chat_history(user_id):
    try:
        with open(f'chat_histories/{user_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return [{"role": "assistant", "content": "어떤 질문이든 해주세요, 예를들어 학업, 진로, 대인관계, 가족, 연애 등에 대한 고민을 말씀해주세요^^"}]

def main():
    st.title("💬 캠퍼스 상담사 위드유")
    st.caption("🚀 대학생의 자기효능감을 진단하고 개선하는 최고의 어드바이저입니다.")

    # Use a session state variable as a simple user identifier
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 'default_user'

    # Load chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = load_chat_history(st.session_state.user_id)

    # Create or retrieve thread
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    thread_id = st.session_state.thread_id

    # Display chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()
        
        if not thread_id:
            st.info("Please add your thread ID to continue.")
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

        # Save chat history
        save_chat_history(st.session_state.user_id, st.session_state.messages)

    # Add a button to clear chat history
    if st.sidebar.button("대화 기록 지우기"):
        st.session_state.messages = [{"role": "assistant", "content": "어떤 질문이든 해주세요, 예를들어 학업, 진로, 대인관계, 가족, 연애 등에 대한 고민을 말씀해주세요^^"}]
        save_chat_history(st.session_state.user_id, st.session_state.messages)
        # Create a new thread
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.experimental_rerun()

if __name__ == "__main__":
    main()