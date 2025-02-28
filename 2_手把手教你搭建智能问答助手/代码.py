import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

# llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     max_tokens=1000,
#     temperature=0  # 控制回答创造性
# )

llm = ChatOpenAI(
    base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
    model="deepseek-chat",                  # DeepSeek模型标识
    openai_api_key="sk-exxxxxxxxxxxxxxxxxxxx",     # 替换为DeepSeek密钥
    max_tokens=1000,
    temperature=0
)

template = """您是一个专业的AI助手，需要清晰准确地回答用户问题

用户问题：{question}

请用简洁的中文回答："""

prompt = PromptTemplate.from_template(template)

qa_chain = prompt | llm  # 管道操作符连接组件


def get_answer(question):
    response = qa_chain.invoke({"question": question})
    return response.content

# 示例问题测试
test_question = "法国的首都是哪里？"
print(f"答案：{get_answer(test_question)}")

while True:
    user_input = input("\n请输入问题（输入q退出）:")
    if user_input.lower() == 'q':
        break
    print(f"AI助手：{get_answer(user_input)}")
