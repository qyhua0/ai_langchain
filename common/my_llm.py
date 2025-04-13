import os
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from dotenv import load_dotenv

def load_openai_api_key(key='OPENAI_API_KEY', dotenv_path=r'Z:\src\ai\ai_agent\.env'):
    """
    加载 OpenAI API Key，优先从环境变量，找不到时尝试从 .env 文件。

    :param env_var_name: 环境变量名
    :param dotenv_path: .env 文件路径
    :return: API Key 字符串
    :raises: RuntimeError 如果未找到 API Key
    """
    # 尝试加载 .env 文件
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    api_key = os.getenv(key)
    if api_key:
        return api_key
    else:
        raise RuntimeError(
            f"API Key not found. Please set the {key} environment variable or check your .env file.")




def get_language_model(model_type="qwen-coder-plus", temperature=0.1, timeout=60000):
    """
    获取语言模型实例

    参数:
        model_type (str): 模型类型，支持 "qwen-coder-plus"、"qwen2.5-coder"、"qwen2.5-coder-14b"、"custom"
        timeout (int): 请求超时时间（秒）

    返回:
        语言模型实例
    """
    # 设置请求超时时间
    requests_timeout = timeout
    api_key_qwen = load_openai_api_key(key='OPENAI_API_KEY_QWEN', dotenv_path=r'/.env')
    api_key_deepseek = load_openai_api_key(key='OPENAI_API_KEY_DEEPSEEK', dotenv_path=r'/.env')


    if model_type == "qwen-coder-plus":
        # DashScope API 的 qwen-coder-plus 模型
        return ChatOpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-coder-plus",
            temperature=temperature,
            openai_api_key= api_key_qwen,
            max_tokens=10000,
            request_timeout=requests_timeout
        )
    elif model_type == "qwen2.5-coder":
        # 本地 Ollama qwen2.5-coder 模型
        return OllamaLLM(
            model="qwen2.5-coder:latest",
            temperature=temperature,
            request_timeout=requests_timeout
        )
    elif model_type == "qwen2.5-coder-14b":
        # 本地 Ollama qwen2.5-coder 14B 模型
        return OllamaLLM(
            model="qwen2.5-coder:14b",
            temperature=temperature,
            request_timeout=requests_timeout
        )

    elif model_type == "deepseek-chat":
        return ChatOpenAI(
            base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
            model="deepseek-chat",  # DeepSeek模型标识
            openai_api_key= api_key_deepseek,  # 替换为DeepSeek密钥
            max_tokens=100000,  # 考虑大文件10万token
            temperature=temperature,
        )

    else:
        # 自定义模型配置示例,后续用其它模型测试
        return ChatOpenAI(
            model="gpt-4",
            temperature=temperature,
            request_timeout=requests_timeout
        )


# 获取语言模型实例 - 默认使用 qwen2.5-coder-14b 本地模型
# language_model = get_language_model("qwen2.5-coder-14b", timeout=600)
language_model = get_language_model("qwen-coder-plus", timeout=600 ,temperature=0.2)