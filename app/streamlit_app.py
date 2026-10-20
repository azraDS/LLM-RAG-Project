import streamlit as st

from fashion_rag.assistant import FashionAssistant
from fashion_rag.config import settings
from fashion_rag.data import load_dataframe


@st.cache_data
def load_data():
    return load_dataframe(settings.modified_data_path)


def main():
    st.title("👗 Fashion Assistant")
    st.markdown("---")

    # Initialize session states
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = []
    if 'total_results' not in st.session_state:
        st.session_state.total_results = 0

    # Initialize FashionAssistant
    try:
        df = load_data()
        if 'assistant' not in st.session_state:
            st.session_state.assistant = FashionAssistant(df)

    except Exception as e:
        st.error(f"Error initializing Fashion Assistant: {str(e)}")
        return

    # Chat interface
    with st.container():
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "intent" in message:
                    st.write(f"🎯 *Intent: {message['intent']}*")




        # User input
        if prompt := st.chat_input("What would you like to know about our fashion products?"):
            with st.chat_message("user"):
                st.markdown(prompt)

            intent = st.session_state.assistant.classify_intent(prompt)


            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.assistant.process_query(prompt)
                        st.markdown(response)
                        st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response,
                                "intent": intent
                            })

                    except Exception as e:
                        error_message = f"Error processing query: {str(e)}"
                        st.error(error_message)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_message,
                            "intent": "error"
                        })


    with st.sidebar:
        st.header("Available Categories")

        # Display available categories
        st.subheader("Categories")
        if st.session_state.assistant.categories:
            st.write(", ".join(st.session_state.assistant.categories))

        st.subheader("Sub Categories")
        if st.session_state.assistant.sub_categories:
            st.write(", ".join(st.session_state.assistant.sub_categories))

        st.subheader("Product Categories")
        if st.session_state.assistant.product_categories:
            st.write(", ".join(st.session_state.assistant.product_categories))



        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.current_results = []
            st.session_state.total_results = 0
            st.rerun()

if __name__ == "__main__":
    main()
