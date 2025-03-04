import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

load_dotenv()
#os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')  # 从.env加载密钥


from typing import TypedDict, List

class ProcessState(TypedDict):
    raw_text: str         # 原始文本
    category: str         # 分类结果
    entities: List[str]   # 实体列表
    summary: str          # 摘要结果



#llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 这里把gpt-4o替换成deepseek
llm = ChatOpenAI(
    base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
    model="deepseek-chat",                  # DeepSeek模型标识
    openai_api_key="sk-eddxxxxxxxxxxxxxxxxxxxx",     # 替换为DeepSeek密钥
    max_tokens=1000,
    temperature=0
)


from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage


def classify_text(state: ProcessState):
    """将文本分类为科技/金融/医疗/其他"""
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template="请将文本分类为[科技|金融|医疗|其他]:\n{text}\n分类结果:"
    )
    msg = HumanMessage(content=prompt_template.format(text=state["raw_text"]))
    return {"category": llm.invoke([msg]).content.strip()}



def extract_entities(state: ProcessState):
    """抽取公司/产品/技术术语"""
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template="请从文本中提取公司、产品和技术名词，用逗号分隔:\n{text}\n实体列表:"
    )
    msg = HumanMessage(content=prompt_template.format(text=state["raw_text"]))
    return {"entities": llm.invoke([msg]).content.strip().split(", ")}



def generate_summary(state: ProcessState):
    """生成50字以内摘要"""
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template="请用50字以内概括文本核心内容:\n{text}\n摘要:"
    )
    msg = HumanMessage(content=prompt_template.format(text=state["raw_text"]))
    return {"summary": llm.invoke([msg]).content.strip()}





# 初始化状态图
workflow = StateGraph(ProcessState)

# 添加节点
workflow.add_node("text_classifier", classify_text)
workflow.add_node("entity_extractor", extract_entities)
workflow.add_node("summary_generator", generate_summary)

# 配置流转
workflow.set_entry_point("text_classifier")
workflow.add_edge("text_classifier", "entity_extractor")
workflow.add_edge("entity_extractor", "summary_generator")
workflow.add_edge("summary_generator", END)

# 编译应用
app = workflow.compile()
#print(app.get_graph())

#os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10809'

# from IPython.display import display, Image
# from langchain_core.runnables.graph import MermaidDrawMethod
#
# display(Image(app.get_graph().draw_mermaid_png(
#     draw_method=MermaidDrawMethod.API
#
# )))

#本地打印工作流图
from graphviz import Digraph

def extract_nodes_and_edges(graph):
    # 提取所有节点名称
    nodes = list(graph.nodes.keys())

    # 提取所有边的关系
    edges = [(edge.source, edge.target) for edge in graph.edges]

    return nodes, edges


def print_state_graph(graph):
    # 提取节点和边
    nodes, edges = extract_nodes_and_edges(graph)

    # 创建 Graphviz 图形对象
    dot = Digraph(comment='StateGraph')

    # 添加节点
    for node in nodes:
        dot.node(node)

    # 添加边
    for source, target in edges:
        dot.edge(source, target)

    # 渲染并保存为文件
    dot.render('state_graph.gv', format='png', view=True)

print_state_graph(app.get_graph())


sample_text = """
深度求索公司宣布开源MoE-1T大模型，该模型采用混合专家架构，在MMLU等基准测试中超越GPT-4。
支持32种语言处理，参数量达1.2万亿，推理效率较前代提升5倍。即将在GitHub开放模型权重，
供学术研究使用，商业授权需联系deepseek@ai.com。"""

state_input = {"raw_text": sample_text}
result = app.invoke(state_input)

print("所属分类:", result["category"])
print("\n实体列表:", result["entities"])
print("\n摘要信息:", result["summary"])





