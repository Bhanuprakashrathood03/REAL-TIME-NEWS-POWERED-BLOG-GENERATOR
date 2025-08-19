import streamlit as st
import os
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Fetch API keys from environment variables.
# The app will show an error if these are not set.
groq_api_key = os.getenv("GROQ_API_KEY")
news_api_key = os.getenv("NEWS_API_KEY")

# --- Helper Functions ---

def get_latest_news_headlines():
    """Fetches the latest news headlines from NewsAPI.org."""
    if not news_api_key:
        st.error("NEWS_API_KEY not found. Please set it in your .env file.")
        return []
    
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={news_api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes
        articles = response.json().get("articles", [])
        return [article['title'] for article in articles]
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch news: {e}")
        return []

def get_groq_response(topic, no_of_words, blog_style):
    """Generates a blog post using the Groq API."""
    if not groq_api_key:
        st.error("GROQ_API_KEY not found. Please set it in your .env file.")
        return None

    try:
        llm = ChatGroq(
            api_key=groq_api_key,
            model_name='llama3-8b-8192',
            temperature=0.7
        )

        template = """
        Write a blog for a {blog_style} audience on the topic "{topic}" within {no_of_words} words.
        The blog should be well-structured, engaging, and informative.
        """
        prompt = PromptTemplate(
            input_variables=["blog_style", "topic", "no_of_words"],
            template=template
        )
        
        # Using LangChain Expression Language (LCEL) for the chain
        chain = prompt | llm
        
        response = chain.invoke({
            "blog_style": blog_style,
            "topic": topic,
            "no_of_words": no_of_words
        })
        
        # The response object from ChatGroq has a 'content' attribute
        return response.content

    except Exception as e:
        st.error(f"An error occurred with the Groq API: {e}")
        return None

# --- Streamlit UI ---

def main():
    """The main function to run the Streamlit web app."""
    st.set_page_config(page_title="News-Powered Blog Generator", page_icon="✍️", layout="centered")
    st.title("News-Powered Blog Generator ✍️")
    st.write("Generate blog posts based on the latest news or your own topics.")

    st.subheader("1. Choose a Topic")

    if 'headlines' not in st.session_state:
        st.session_state.headlines = []

    if st.button("Fetch Latest News Headlines"):
        with st.spinner("Fetching news..."):
            st.session_state.headlines = get_latest_news_headlines()

    if st.session_state.headlines:
        topic_options = ["-- Select a headline --"] + st.session_state.headlines
        selected_topic = st.selectbox("Select a News Headline:", topic_options)
        custom_topic = st.text_input("Or write your own topic below:")
        topic = custom_topic if custom_topic else (selected_topic if selected_topic != "-- Select a headline --" else "")
    else:
        topic = st.text_input("Enter the Blog Topic")
    
    st.subheader("2. Configure Your Blog Post")
    col1, col2 = st.columns([1, 1])
    with col1:
        no_of_words = st.text_input("Number of Words (e.g., 300)")
    with col2:
        blog_style = st.selectbox("Writing Style For:", ("General Audience", "Researchers", "Data Scientists"), index=0)

    st.subheader("3. Generate")
    submit = st.button("Generate Blog")

    if submit:
        if not topic or not no_of_words:
            st.warning("Please choose or enter a topic and specify the number of words.")
        else:
            with st.spinner(f"Generating a blog post on '{topic}'..."):
                response = get_groq_response(topic, no_of_words, blog_style)
                if response:
                    st.subheader("Your Generated Blog Post")
                    st.write(response)
                    st.success("Blog post generated successfully!")

if __name__ == '__main__':
    main()