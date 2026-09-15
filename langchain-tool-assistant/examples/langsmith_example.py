"""Classroom ChatGroq and optional LangSmith example.
Run with the project's venv; enter keys in hidden terminal prompts.

課堂 ChatGroq 與選用 LangSmith 範例。
使用專案 venv 執行，金鑰只在終端機隱藏提示輸入。
"""
import getpass
import os
from langchain_groq import ChatGroq

if __name__ == '__main__':
    if not os.getenv('GROQ_API_KEY'):
        os.environ['GROQ_API_KEY'] = getpass.getpass('Groq API Key / Groq 金鑰: ').strip()
    if os.getenv('LANGSMITH_TRACING', 'false').lower() == 'true':
        if not os.getenv('LANGSMITH_API_KEY'):
            os.environ['LANGSMITH_API_KEY'] = getpass.getpass('LangSmith API Key / LangSmith 金鑰: ').strip()
        os.environ.setdefault('LANGSMITH_PROJECT', 'LangChain-Classroom')
    llm = ChatGroq(model=os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b'), temperature=0.3,
                   max_tokens=700, timeout=20, max_retries=0)
    response = llm.invoke('Hello, World!', config={'run_name': 'classroom_hello'})
    print(response.content)
