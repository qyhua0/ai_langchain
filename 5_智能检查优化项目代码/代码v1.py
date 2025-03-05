import os
import re
import shutil
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM

# deepseek模型
# llm = ChatOpenAI(
#     base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
#     model="deepseek-chat",                  # DeepSeek模型标识
#     openai_api_key="sk-xxxxxxxxxxxxxxxxxxxx",     # 替换为DeepSeek密钥
#     max_tokens=300000, # 考虑大文件30万token
#     temperature=0.0
# )


# 千问模型
llm = ChatOpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # DeepSeek API端点
    model="qwen-coder-plus",                  # DeepSeek模型标识
    openai_api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",     # 替换为DeepSeek密钥
    max_tokens=300000, # 考虑大文件30万token
    temperature=0.0
)

# 本地模型
# v1 = 'qwen2.5-coder:latest'
# v2 ='qwen2.5-coder:14b'
# llm = OllamaLLM(model=v2,temperature= 0.0)




# 定义优化代码的 Prompt
optimization_prompt = PromptTemplate(
    input_variables=["code", "filetype"],
    template="""
    你是一个代码优化专家。请分析以下 {filetype} 代码：
    ```
    {code}
    ```
    任务：
    1. 仅去除明确未被任何代码使用的变量和方法。
    2. 修复潜在的 bug（如未定义变量、空指针等）。
    3. 提升代码可读性（优化命名、结构、添加必要注释）。
    4. 保留原有功能不变，确保不删除被直接调用、间接调用（通过 this、事件或模板）的方法。
    请返回优化后的完整代码，并用注释说明改动原因。
    """
)

# 创建 LangChain 调用链
optimization_chain = optimization_prompt | llm


def backup_file_or_directory(path):
    """备份文件或目录到当前目录下的 backup 文件夹"""
    backup_dir = os.path.join(os.getcwd(), "backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backup_path = os.path.join(backup_dir, os.path.basename(path))
    if os.path.isfile(path):
        shutil.copy2(path, backup_path)
    elif os.path.isdir(path):
        shutil.copytree(path, backup_path, dirs_exist_ok=True)
    print(f"已备份到: {backup_path}")


def optimize_code(file_path):

    print(file_path)
    """优化单个文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        original_code = f.read()


    # 根据文件类型调整处理逻辑
    filetype = os.path.splitext(file_path)[1][1:]  # 提取文件扩展名，如 vue、py
    if filetype not in ['vue', 'js','java']:  # 可扩展支持其他类型
        print(f"暂不支持优化 .{filetype} 文件")
        return

    print('-------------code1-------------------')

    print(original_code)
    print('-------------code2--------------------')
    print('filetype-->',filetype)

    # 调用大模型优化代码
    optimized_result = optimization_chain.invoke({
        "code": original_code,
        "filetype": filetype
    })

    print('---------------模型处理结果1---------------')
    print(optimized_result)
    print('---------------模型处理结果2---------------')

    # 提取 AIMessage 的 content 属性
    optimized_code = optimized_result.content if hasattr(optimized_result, 'content') else str(optimized_result)

    print('---------------优化后代码1--------------------')

    print(optimized_code)
    print('---------------优化后代码2--------------------')

    # 保存优化后的代码
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(optimized_code)
    print(f"已优化并保存: {file_path}")

def remove_empty_lines(code):
    """删除空行，保留必要缩进"""
    lines = code.splitlines()
    # 过滤掉完全空的行，但保留带有缩进的行（避免破坏代码结构）
    cleaned_lines = [line for line in lines if line.strip() != ""]
    return "\n".join(cleaned_lines)




def process_path(path):
    """处理文件或目录"""
    # 备份
    backup_file_or_directory(path)

    # 处理文件或目录
    if os.path.isfile(path):
        optimize_code(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(('.vue', '.js','.java')):  # 只处理指定类型文件
                    optimize_code(os.path.join(root, file))
    else:
        print(f"路径不存在: {path}")


if __name__ == "__main__":
    # 示例用法：优化指定文件或目录
    target_path = "D:\\projects\\xxxWeb\\src\\pages\\finance\\order\\list.vue"  # 替换为你的文件或目录路径
    process_path(target_path)