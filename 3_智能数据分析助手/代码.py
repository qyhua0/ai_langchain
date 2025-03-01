import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from langchain.agents import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

# 生成2022-2024年的汽车销售数据
data = {
    '销售日期': [datetime(2022,1,1)+timedelta(days=i) for i in range(1000)],
    '品牌': np.random.choice(['比亚迪', '特斯拉', '理想', '小鹏', '蔚来'], 1000),
    '车型': np.random.choice(['SUV', '轿车', 'MPV', '跑车'], 1000),
    '颜色': np.random.choice(['珍珠白', '星空蓝', '曜石黑', '烈焰红'], 1000),
    '出厂年份': np.random.randint(2019, 2024, 1000),
    '售价(万元)': np.round(np.random.uniform(15, 50, 1000), 1),
    '续航里程(km)': np.random.randint(300, 700, 1000),
    '电池容量(kWh)': np.random.choice([60, 70, 80, 100], 1000),
    '销售人员': np.random.choice(['王芳', '李明', '张伟', '陈静'], 1000)
}

df = pd.DataFrame(data).sort_values('销售日期')

# 这里查看生成的数据情况
# print(df.head())
# df.info()
# print(df.describe())

# 初始化语言模型
#llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 这里把gpt-4o替换成deepseek
llm = ChatOpenAI(
    base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
    model="deepseek-chat",                  # DeepSeek模型标识
    openai_api_key="sk-edddxxxxxxxxxxxxxxxxxxxx",     # 替换为DeepSeek密钥
    max_tokens=1000,
    temperature=0
)

# 创建数据分析代理
agent = create_pandas_dataframe_agent(
    llm=llm,
    df=df,
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    allow_dangerous_code=True  # 要保证输入数据和问题安全全，会动态生成python代码与执行，可能生成并执行危险的代码
)

def 智能问答(question):
    """自然语言交互入口"""
    response = agent.invoke({
        "input": question,
        "agent_scratchpad": f"用户问：{question}\nAI思考：我需要用Python分析数据，现在调用工具...\n动作：python_repl_ast\n输入："
    })
    print(f"🔍 问题：{question}")
    print(f"💡 答案：{response}")

智能问答("数据包含哪些字段？")
智能问答("近三年哪个颜色的车最畅销？")

智能问答("按季度分析各品牌销售额趋势")
智能问答("比较不同续航区间的平均售价")

智能问答("按季度分析各品牌销售额趋势")
智能问答("比较不同续航区间的平均售价")

智能问答("预测下个季度哪个品牌的增长潜力最大？")
智能问答("哪些销售人员的客户回购率最高？")