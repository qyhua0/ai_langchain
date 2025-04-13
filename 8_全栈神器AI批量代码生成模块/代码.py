import os
from typing import Dict, List, Optional, Tuple, Union
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from common.my_llm import get_language_model



class Constants:


    # API契约相关提示词
    API_CONTRACT_SYSTEM_PROMPT = """你是一位专业的全栈开发工程师。你的任务是设计一个模块的API契约，包括前后端交互的接口规范。
    契约应该清晰地定义每个API的URL路径、HTTP方法、请求参数和返回数据结构。"""

    API_CONTRACT_PROMPT_TEMPLATE = """为{module_name}模块设计一个完整的API契约。

    该模块的主要功能是：{module_description}

    请提供以下内容：
    1. 该模块所需的所有API端点列表
    2. 每个API的详细规范，包括：
       - URL路径
       - HTTP方法(GET/POST)
       - 请求参数(包括路径参数、查询参数和请求体)
       - 成功响应的数据结构

    请确保API设计符合RESTful规范，并适合前后端分离的架构。
    """

    # 后端代码生成提示词
    BACKEND_SYSTEM_PROMPT = """你是一位专业的Java后端开发工程师，精通Spring Boot2框架。
    你的任务是根据提供的API契约，编写符合规范的Java控制器代码，确保代码风格一致、注释完善。"""

    BACKEND_PROMPT_TEMPLATE = """请根据以下API契约，编写一个完整的Java控制器类来实现{module_name}模块的后端接口。

    API契约:
    {api_contract}

    请提供以下内容：
    1. 控制器类(Controller)代码
    2. 必要的实体类(Entity)代码
    3. 必要的数据传输对象(DTO)或值对象(VO)代码

    代码要符合Spring Boot2最佳实践，包含完整的Java注解、参数验证、异常处理和详细注释。
    """

    # 前端代码生成提示词
    FRONTEND_SYSTEM_PROMPT = """你是一位专业的Vue.js前端开发工程师，精通Vue 2和iView UI框架。
    你的任务是根据提供的API契约，编写符合规范的Vue组件代码，确保代码风格一致、交互体验良好。"""

    FRONTEND_PROMPT_TEMPLATE = """请根据以下API契约，编写一个完整的Vue 2组件来实现{module_name}模块的前端界面。

    API契约:
    {api_contract}

    请提供以下内容：
    1. Vue组件(.vue文件)，包含template、script和style部分
    2. API请求函数(推荐放在单独的api文件中)

    代码要符合Vue 2 Composition API的最佳实践，使用iView组件库，实现以下功能：
    1. 查询条件，如果需求未指定查询条件的需要选择合理的列表字段作为查询条件
    2. 数据列表显示,默认显示三条未示例记录数据
    3. 分页、排序和筛选(如适用)
    4. 表单提交和验证(如适用)
    5. 必要的CRUD操作
    6. 良好的错误处理和用户反馈
    """

    # API请求函数生成提示词
    API_FUNCTIONS_SYSTEM_PROMPT = """你是一位专业的前端开发工程师，精通JavaScript和API交互。
    你的任务是根据提供的API契约，编写用于与后端交互的API请求函数，确保代码清晰易用。"""

    API_FUNCTIONS_PROMPT_TEMPLATE = """请根据以下API契约，编写一组用于{module_name}模块的API请求函数。

    API契约:
    {api_contract}

    请使用axios库(或类似的HTTP客户端库)编写这些函数，确保：
    1. 函数命名清晰，符合模块功能
    2. 函数参数类型合适，与API契约匹配
    3. 提供完整的JSDoc注释，说明参数和返回值
    4. 函数应该位于一个独立的JS/TS文件中，便于导入使用
    """


class CodeGenerator:
    def __init__(self, llm_name: Optional[str] = None):
        """初始化代码生成器。

        Args:
            llm_name: 模型名称
        """
        self.constants = Constants()
        self.llm = get_language_model(llm_name)


        # 初始化输出解析器
        self.output_parser = StrOutputParser()

        # 初始化提示模板
        self._init_prompt_templates()

    def _init_prompt_templates(self):
        """初始化各种提示模板"""
        # API契约提示模板
        self.api_contract_prompt = PromptTemplate(
            template=self.constants.API_CONTRACT_PROMPT_TEMPLATE,
            input_variables=["module_name", "module_description"]
        )

        # 后端代码提示模板
        self.backend_prompt = PromptTemplate(
            template=self.constants.BACKEND_PROMPT_TEMPLATE,
            input_variables=["module_name", "api_contract"]
        )

        # 前端代码提示模板
        self.frontend_prompt = PromptTemplate(
            template=self.constants.FRONTEND_PROMPT_TEMPLATE,
            input_variables=["module_name", "api_contract"]
        )

        # API请求函数提示模板
        self.api_functions_prompt = PromptTemplate(
            template=self.constants.API_FUNCTIONS_PROMPT_TEMPLATE,
            input_variables=["module_name", "api_contract"]
        )

    def generate_api_contract(self, module_name: str, module_description: str) -> str:
        """生成API契约。

        Args:
            module_name: 模块名称
            module_description: 模块功能描述

        Returns:
            生成的API契约
        """
        chain = self.api_contract_prompt | self.llm | self.output_parser

        return chain.invoke({
            "module_name": module_name,
            "module_description": module_description
        })

    def generate_backend_code(self, module_name: str, api_contract: str) -> str:
        """生成后端Java代码。

        Args:
            module_name: 模块名称
            api_contract: API契约

        Returns:
            生成的后端代码
        """
        chain =self.backend_prompt | self.llm | self.output_parser


        return chain.invoke({
            "module_name": module_name,
            "api_contract": api_contract
        })

    def generate_frontend_code(self, module_name: str, api_contract: str) -> str:
        """生成前端Vue代码。

        Args:
            module_name: 模块名称
            api_contract: API契约

        Returns:
            生成的前端代码
        """
        chain =self.frontend_prompt | self.llm | self.output_parser


        return chain.invoke({
            "module_name": module_name,
            "api_contract": api_contract
        })

    def generate_api_functions(self, module_name: str, api_contract: str) -> str:
        """生成API请求函数。

        Args:
            module_name: 模块名称
            api_contract: API契约

        Returns:
            生成的API请求函数代码
        """
        chain = self.api_functions_prompt | self.llm | self.output_parser

        return chain.invoke({
            "module_name": module_name,
            "api_contract": api_contract
        })

    def generate_full_stack_code(self, module_name: str, module_description: str) -> Dict[str, str]:
        """生成完整的全栈代码。

        Args:
            module_name: 模块名称
            module_description: 模块功能描述

        Returns:
            包含所有生成代码的字典
        """
        # 1. 生成API契约
        api_contract = self.generate_api_contract(module_name, module_description)
        print(f"✅ API契约生成完成")

        # 2. 生成后端代码
        backend_code = self.generate_backend_code(module_name, api_contract)
        print(f"✅ 后端代码生成完成")

        # 3. 生成前端Vue组件
        frontend_code = self.generate_frontend_code(module_name, api_contract)
        print(f"✅ 前端Vue组件生成完成")

        # 4. 生成API请求函数
        api_functions = self.generate_api_functions(module_name, api_contract)
        print(f"✅ API请求函数生成完成")

        # 返回所有生成的代码
        return {
            "api_contract": api_contract,
            "backend_code": backend_code,
            "frontend_code": frontend_code,
            "api_functions": api_functions
        }

    def save_code_to_files(self,
                           module_name: str,
                           output_dir: str,
                           code_dict: Dict[str, str]) -> None:
        """将生成的代码保存到文件中。

        Args:
            module_name: 模块名称
            output_dir: 输出目录
            code_dict: 包含所有生成代码的字典
        """
        # 创建必要的目录
        backend_dir = os.path.join(output_dir, "backend", "src", "main", "java", "com", "example", "demo")
        frontend_dir = os.path.join(output_dir, "frontend", "src")
        api_dir = os.path.join(frontend_dir, "api")

        os.makedirs(backend_dir, exist_ok=True)
        os.makedirs(frontend_dir, exist_ok=True)
        os.makedirs(api_dir, exist_ok=True)

        # 保存API契约
        with open(os.path.join(output_dir, f"{module_name}_api_contract.md"), "w",encoding='utf-8') as f:
            f.write(code_dict["api_contract"])

        # 保存后端代码 - 这里简化处理，实际上可能需要解析代码并分别保存到不同文件
        with open(os.path.join(backend_dir, f"{module_name.capitalize()}Controller.java"), "w",encoding='utf-8') as f:
            f.write(code_dict["backend_code"])

        # 保存前端Vue组件
        with open(os.path.join(frontend_dir, f"{module_name.capitalize()}.vue"), "w",encoding='utf-8') as f:
            f.write(code_dict["frontend_code"])

        # 保存API请求函数
        with open(os.path.join(api_dir, f"{module_name}.js"), "w",encoding='utf-8') as f:
            f.write(code_dict["api_functions"])

        print(f"✅ 所有代码已保存到 {output_dir} 目录")


# 使用示例
def main():
    """
    主函数，演示代码生成器的使用。
    """
    # generator = CodeGenerator('qwen2.5-coder')
    generator = CodeGenerator('deepseek-chat')

    # 定义模块信息
    module_name = "user"
    module_description = """
    用户管理模块，需要实现用户的增删改查功能。

    用户信息包括：
    - ID
    - 用户名
    - 邮箱
    - 电话
    - 状态(启用/禁用)
    - 创建时间
    - 更新时间

    需要支持的功能：
    1. 分页获取用户列表，支持按用户名搜索
    2. 获取单个用户详情
    3. 创建新用户
    4. 更新用户信息
    5. 删除用户
    """

    # 生成完整的全栈代码
    codes = generator.generate_full_stack_code(module_name, module_description)

    # 保存代码到文件
    output_dir = "./generated_code"
    generator.save_code_to_files(module_name, output_dir, codes)


if __name__ == "__main__":
    main()