from typing import Dict, TypedDict

from langgraph.constants import START
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables.graph import MermaidDrawMethod


#使用deepseek
def llm():
    return ChatOpenAI(
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        openai_api_key="sk-eddxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        max_tokens=10000,
        temperature=0
    )

class State(TypedDict):
    query: str
    category: str
    sentiment: str
    response: str

def categorize(state: State) -> State:
    """将客户查询分类为技术支持、账单支持或常规问题。"""
    prompt = ChatPromptTemplate.from_template(
        "将以下客户查询归类为：技术支持、账单查询、常规问题。查询内容：{query}"
    )
    chain = prompt | llm()
    category = chain.invoke({"query": state["query"]}).content
    return {"category": category}

def analyze_sentiment(state: State) -> State:
    """对客户查询进行情绪分析，判断为积极、中性或消极。"""
    prompt = ChatPromptTemplate.from_template(
        "分析以下客户查询的情绪。请回复 '积极'、'中性' 或 '消极'。查询内容：{query}"
    )
    chain = prompt | llm()
    sentiment = chain.invoke({"query": state["query"]}).content
    return {"sentiment": sentiment}

def handle_technical(state: State) -> State:
    """针对技术支持问题生成回复。"""
    prompt = ChatPromptTemplate.from_template(
        "请为以下技术问题生成技术支持回复：{query}"
    )
    chain = prompt | llm()
    response = chain.invoke({"query": state["query"]}).content
    return {"response": response}

def handle_billing(state: State) -> State:
    """针对账单问题生成回复。"""
    prompt = ChatPromptTemplate.from_template(
        "请为以下账单问题生成账单支持回复：{query}"
    )
    chain = prompt | llm()
    response = chain.invoke({"query": state["query"]}).content
    return {"response": response}

def handle_general(state: State) -> State:
    """针对常规问题生成回复。"""
    prompt = ChatPromptTemplate.from_template(
        "请为以下查询生成常规支持回复：{query}"
    )
    chain = prompt | llm()
    response = chain.invoke({"query": state["query"]}).content
    return {"response": response}

def escalate(state: State) -> State:
    """因消极情绪将查询上报给人工客服。"""
    return {"response": "由于查询情绪消极，此问题已上报给人工客服。"}


def route_query(state: State) -> str:
    """根据情绪和类别路由，情绪消极时优先升级"""
    if state["sentiment"] == "消极":
        return "升级处理"
    if state["category"] == "技术支持":
        return "处理技术问题"
    elif state["category"] == "账单查询":
        return "处理账单问题"
    else:
        return "处理一般问题"

# 创建工作流图
workflow = StateGraph(State)

# 添加节点
workflow.add_node("分类", categorize)
workflow.add_node("情绪分析", analyze_sentiment)  # 确保存在此节点
workflow.add_node("处理技术问题", handle_technical)
workflow.add_node("处理账单问题", handle_billing)
workflow.add_node("处理一般问题", handle_general)
workflow.add_node("升级处理", escalate)

# 连接节点
workflow.add_edge(START,"分类")

workflow.add_edge("分类", "情绪分析")  # 第一步：分类 → 情绪分析
workflow.add_conditional_edges(
    "情绪分析",  # 条件路由的起点是情绪分析节点
    route_query,
    {
        "处理技术问题": "处理技术问题",
        "处理账单问题": "处理账单问题",
        "处理一般问题": "处理一般问题",
        "升级处理": "升级处理"
    }
)
# 所有处理节点连接到 END
workflow.add_edge("处理技术问题", END)
workflow.add_edge("处理账单问题", END)
workflow.add_edge("处理一般问题", END)
workflow.add_edge("升级处理", END)

# 设置入口并编译
workflow.set_entry_point("分类")
app = workflow.compile()


# 这部分不是必须的，只是为了看流程图，可以取消
# 在不改变第三方库代码的情况下，动态修改库方法
import pyppeteer

# 保存原始 launch 函数
_original_launch = pyppeteer.launch

# 定义一个新的 launch 方法，强制传入 executablePath
async def patched_launch(*args, **kwargs):
    kwargs['executablePath'] = r'Z:\src\ai\ai_agent\lib\chrome-win64\chrome.exe'
    return await _original_launch(*args, **kwargs)

# 替换 launch 方法
pyppeteer.launch = patched_launch


from pyppeteer.frame_manager import Frame

_original_addScriptTag = Frame.addScriptTag

async def patched_addScriptTag(self, options):
    if options.get('url') == 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js':
        # 覆盖URL，改成本地内容
        options.pop('url')
        local_file = r'Z:\src\ai\ai_agent\lib\mermaid.min.js'
        with open(local_file, 'r', encoding='utf8') as f:
            js_content = f.read()
        options['content'] = js_content
    return await _original_addScriptTag(self, options)

Frame.addScriptTag = patched_addScriptTag

img_bytes = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)
with open('7_output.png', 'wb') as f:
    f.write(img_bytes)
print("图片已保存到 7_output.png")




def run_customer_support(query: str) -> Dict[str, str]:
    """
    通过 LangGraph 工作流处理客户查询。
    参数:
        query (str): 客户查询内容
    返回:
        Dict[str, str]: 包含查询类别、情绪和回复的字典
    """
    results = app.invoke({"query": query},debug=False)
    return {
        "category": results["category"],
        "sentiment": results["sentiment"],
        "response": results["response"]
    }


query = "我的网络经常断线，能帮忙解决吗？"
result = run_customer_support(query)
print(f"查询内容: {query}")
print(f"类别: {result['category']}")
print(f"情绪: {result['sentiment']}")
print(f"回复: {result['response']}")
print("\n")



query = "我该在哪里找到我的收据？"
result = run_customer_support(query)
print(f"查询内容: {query}")
print(f"类别: {result['category']}")
print(f"情绪: {result['sentiment']}")
print(f"回复: {result['response']}")
print("\n")


query = "你们的营业时间是？"
result = run_customer_support(query)
print(f"查询内容: {query}")
print(f"类别: {result['category']}")
print(f"情绪: {result['sentiment']}")
print(f"回复: {result['response']}")