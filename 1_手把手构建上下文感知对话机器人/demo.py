from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = ''



# 创建内存存储字典
session_store = {}

def get_chat_history(session_id: str):
    """智能会话存储器"""
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

# 加载环境变量
load_dotenv()


# 创建内存存储字典
session_store = {}

def get_chat_history(session_id: str):
    """智能会话存储器"""
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

# 构建三级对话模板
conversation_blueprint = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的人工智能助手"),  # 角色定义层
    MessagesPlaceholder(variable_name="history"),  # 历史记忆层
    ("human", "{input}")  # 用户输入层
])


# 初始化语言引擎
#llm_engine = ChatOpenAI(model="gpt-4o-mini", max_tokens=1000, temperature=0)
# 修改base_url并调整模型名称
llm_engine = ChatOpenAI(
    base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
    model="deepseek-chat",                  # DeepSeek模型标识
    openai_api_key="sk-xxxxxxxxxxxxxxxxxx",     # 替换为DeepSeek密钥
    max_tokens=1000,
    temperature=0
)

# 构建处理链
processing_pipeline = conversation_blueprint | llm_engine

# 添加历史管理模块
smart_agent = RunnableWithMessageHistory(
    processing_pipeline,
    get_chat_history,
    input_messages_key="input",
    history_messages_key="history"
)


# 实现对话
user_session = "user_007"

# 首次对话
first_response = smart_agent.invoke(
    {"input": "你好！请问是先有鸡还是先有蛋？"},
    config={"configurable": {"session_id": user_session}}
)
print(f"AI回复: {first_response.content}")

# 延续对话
followup_response = smart_agent.invoke(
    {"input": "我刚才问的第一个问题是什么？"},
    config={"configurable": {"session_id": user_session}}
)
print(f"AI回复: {followup_response.content}")


print("\n完整对话记录:")
for message in session_store[user_session].messages:
    print(f"[{message.type.upper()}] {message.content}")



# 添加情感分析模块示例
from textblob import TextBlob

def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity