import streamlit as st
from PIL import Image
import requests


BE_URL = "https://rag-chatbot-temp-backend-943956214135.europe-west3.run.app"
# NOTE: cambiare URL in questa costante per cambiare backend. La cosa importante è che il backend alternativo supporti il payload usato nella funzione `send_request_and_get_responses`


def send_request_and_get_response(session):
    cutted_session = session[-10:]
    # NOTE: per evitare troppa latenza nell'interazione col backend la sessione è attualmente limitata agli 10 messaggi.
    # Per gestire al meglio una sessione in produzione bisogna avere un db o una cache, e un microservizio che la gestisca.
    headers = {"Content-type": "application/json"}
    payload = {
        "messages": cutted_session
    }  # NOTE: payload che deve essere obbligatoriamente supportato da qualunque backend alternativo
    response = requests.post(url=BE_URL, headers=headers, json=payload, stream=True)
    response.raise_for_status()  # NOTE: gestire eventuali errori evitando che il front-end esploda
    return response


def stream_response(response):
    for response_chunk in response.iter_content():
        if response_chunk:
            try:
                yield response_chunk.decode(
                    "utf-8"
                )  # NOTE: trovare un modo per decodificare correttamente anche le lettere accentate
            except Exception:
                pass


batman_icon = Image.open("./pics/batman_icon.webp")
alfred_icon = Image.open("./pics/alfred_icon.png")
ROLE_AVATARS_DICT = {
    "user": batman_icon,
    "human": batman_icon,
    "ai": alfred_icon,
    "assistant": alfred_icon,
}


st.set_page_config(
    page_title="Alfred",
    page_icon="./pics/alfred_icon.png",
    layout="wide",
)


st.markdown(
    body="""
    <style>
    .st-key-header-container {
        top: 5%;
        position: fixed;
    }
    .st-key-chat-messages-container {
        top: 33%;
        position: static;
    }
    .st-key-chat-input-container {
        bottom: 5%;
        position: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


header_container = st.container(key="header-container")
with header_container:
    logo_col, title_col = st.columns([1, 4])
    with logo_col:
        st.image("./pics/logo_maticmind.webp", width=250)
    with title_col:
        st.title("Alfred")

chat_messages_container = st.container(
    key="chat-messages-container", border=True, height=370
)

chat_input_container = st.container(key="chat-input-container")
with chat_input_container:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        curr_role = message["role"]
        chat_messages_container.chat_message(
            name=curr_role, avatar=ROLE_AVATARS_DICT[curr_role]
        ).markdown(message["content"])

    if prompt := st.chat_input("Cosa vuoi chiedere?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_messages_container.chat_message(name="user", avatar=batman_icon).markdown(
            prompt
        )

        # NOTE: chiamata a backend qui
        response = send_request_and_get_response(session=st.session_state.messages)

        full_bot_response = chat_messages_container.chat_message(
            name="assistant", avatar=alfred_icon
        ).write_stream(stream_response(response))
        st.session_state.messages.append(
            {"role": "assistant", "content": full_bot_response}
        )
