import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)
load_dotenv()

llm = ChatOpenAI(
    base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
    model="deepseek-chat",                  # DeepSeek模型标识
    openai_api_key="",     # 替换为DeepSeek密钥
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


@app.post("/ask")
async def ask_question(request: Request):
    data = await request.json()
    question = data.get("question", "")
    answer = get_answer(question)
    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)