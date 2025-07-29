#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码生成工作流系统 - 重构版
支持多LLM模型、上下文管理、可配置流程
"""

import os
import json
import re

import yaml
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate


class LLMProvider(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


@dataclass
class LLMConfig:
    """LLM配置"""
    name: str
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    base_url: Optional[str] = None
    api_key: Optional[str] = None


@dataclass
class ContextConfig:
    """上下文配置"""
    framework: str
    requirements: str
    example_files: List[str] = None
    documentation_files: List[str] = None
    mybatis_files: List[str] = None
    configuration_files: List[str] = None


@dataclass
class StepConfig:
    """工作流步骤配置"""
    name: str
    llm_name: str
    prompt_template: str
    context_type: Optional[str] = None
    depends_on: List[str] = None


@dataclass
class WorkflowConfig:
    """工作流配置"""
    name: str
    description: str
    contexts: Dict[str, ContextConfig]
    steps: List[StepConfig]
    requirement: str = "开发一个文章管理系统，包含文章的增删改查功能"  # 首个流程节点需要，具体开发需求
    output_dir: str = "./output"
    log_dir: str = "./logs"


@dataclass
class StepResult:
    """步骤执行结果"""
    step_name: str
    input_data: Dict[str, Any]
    output_data: str
    duration: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class LLMFactory:
    """LLM工厂类"""

    @staticmethod
    def create_llm(config: LLMConfig):
        """创建LLM实例"""
        if config.provider == LLMProvider.OPENAI.value:
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                api_key=config.api_key or os.getenv("OPENAI_API_KEY")
            )

        elif config.provider == LLMProvider.DEEPSEEK.value:
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                base_url=config.base_url or "https://api.deepseek.com/v1",
                api_key=config.api_key or os.getenv("DEEPSEEK_API_KEY")
            )

        elif config.provider == LLMProvider.OLLAMA.value:
            return ChatOllama(
                model=config.model,
                temperature=config.temperature,
                base_url=config.base_url or "http://localhost:11434"
            )

        else:
            raise ValueError(f"不支持的LLM提供商: {config.provider}")

    @staticmethod
    def clean_output(output: str) -> str:
        """清理LLM输出内容"""
        if not output:
            return output

        # 移除 <think></think> 标签及其内容
        output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL | re.IGNORECASE)

        # 移除其他可能的内部标签（可根据需要扩展）
        # output = re.sub(r'<reasoning>.*?</reasoning>', '', output, flags=re.DOTALL | re.IGNORECASE)
        # output = re.sub(r'<internal>.*?</internal>', '', output, flags=re.DOTALL | re.IGNORECASE)

        # 清理多余的空白字符
        output = re.sub(r'\n\s*\n\s*\n', '\n\n', output)  # 多个连续空行替换为两个
        output = output.strip()

        return output


class ContextManager:
    """上下文管理器"""

    def __init__(self, contexts: Dict[str, ContextConfig]):
        self.contexts = contexts
        self._load_all_contexts()

    def _load_all_contexts(self):
        """加载所有上下文"""
        for context_name, context_config in self.contexts.items():
            self._load_context_files(context_config)

    def _load_context_files(self, context_config: ContextConfig):
        """加载上下文文件"""
        # 加载示例文件
        if context_config.example_files:
            context_config.examples = []
            for file_path in context_config.example_files:
                content = self._load_file_content(file_path)
                if content:
                    context_config.examples.append({
                        "file": file_path,
                        "content": content
                    })

        # 加载文档文件
        if context_config.documentation_files:
            context_config.documentation = []
            for file_path in context_config.documentation_files:
                content = self._load_file_content(file_path)
                if content:
                    context_config.documentation.append({
                        "file": file_path,
                        "content": content
                    })

        # 加载MyBatis文件
        if context_config.mybatis_files:
            context_config.mybatis_examples = []
            for file_path in context_config.mybatis_files:
                content = self._load_file_content(file_path)
                if content:
                    context_config.mybatis_examples.append({
                        "file": file_path,
                        "content": content
                    })

        # 加载配置文件
        if context_config.configuration_files:
            context_config.configurations = []
            for file_path in context_config.configuration_files:
                content = self._load_file_content(file_path)
                if content:
                    context_config.configurations.append({
                        "file": file_path,
                        "content": content
                    })

    def _load_file_content(self, file_path: str) -> Optional[str]:
        """加载文件内容"""
        try:
            file_path = Path(file_path)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print(f"警告: 上下文文件不存在: {file_path}")
                return None
        except Exception as e:
            print(f"错误: 加载文件 {file_path} 失败: {e}")
            return None

    def get_context(self, context_type: str) -> str:
        """获取指定类型的上下文"""
        if context_type not in self.contexts:
            return ""

        context_config = self.contexts[context_type]
        return self._format_context(context_config)

    def _format_context(self, context_config: ContextConfig) -> str:
        """格式化上下文数据"""
        formatted = []

        formatted.append(f"技术框架: {context_config.framework}")
        formatted.append(f"开发要求:\n{context_config.requirements}")

        # 格式化示例代码
        if hasattr(context_config, 'examples'):
            formatted.append("示例代码:")
            for example in context_config.examples:
                file_name = Path(example["file"]).name
                formatted.append(f"\n=== {file_name} ===")
                formatted.append(f"```{self._get_file_extension(example['file'])}")
                formatted.append(example["content"])
                formatted.append("```")

        # 格式化MyBatis示例
        if hasattr(context_config, 'mybatis_examples'):
            formatted.append("\nMyBatis XML示例:")
            for example in context_config.mybatis_examples:
                file_name = Path(example["file"]).name
                formatted.append(f"\n=== {file_name} ===")
                formatted.append("```xml")
                formatted.append(example["content"])
                formatted.append("```")

        # 格式化配置文件
        if hasattr(context_config, 'configurations'):
            formatted.append("\n配置文件示例:")
            for config in context_config.configurations:
                file_name = Path(config["file"]).name
                formatted.append(f"\n=== {file_name} ===")
                formatted.append(f"```{self._get_file_extension(config['file'])}")
                formatted.append(config["content"])
                formatted.append("```")

        # 格式化文档
        if hasattr(context_config, 'documentation'):
            formatted.append("\n相关文档:")
            for doc in context_config.documentation:
                file_name = Path(doc["file"]).name
                formatted.append(f"\n=== {file_name} ===")
                formatted.append(doc["content"])

        return "\n".join(formatted)

    def _get_file_extension(self, file_path: str) -> str:
        """获取文件扩展名用于代码高亮"""
        extension = Path(file_path).suffix.lower()
        extension_map = {
            '.vue': 'vue',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.xml': 'xml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.sql': 'sql',
            '.md': 'markdown',
            '.json': 'json'
        }
        return extension_map.get(extension, 'text')


class Logger:
    """日志管理器"""

    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log_step_result(self, result: StepResult):
        """记录步骤结果"""
        log_entry = {
            "timestamp": result.timestamp.isoformat(),
            "step_name": result.step_name,
            "duration": result.duration,
            "success": result.success,
            "input_size": len(str(result.input_data)),
            "output_size": len(result.output_data),
            "error_message": result.error_message
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def log_message(self, message: str, level: str = "INFO"):
        """记录普通消息"""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


class WorkflowExecutor:
    """工作流执行器"""

    def __init__(self, workflow_config: WorkflowConfig, llm_configs: Dict[str, LLMConfig]):
        self.workflow_config = workflow_config
        self.llm_configs = llm_configs
        self.context_manager = ContextManager(workflow_config.contexts)
        self.logger = Logger(workflow_config.log_dir)
        self.results: Dict[str, StepResult] = {}

        # 创建输出目录
        Path(workflow_config.output_dir).mkdir(exist_ok=True)

    async def execute(self) -> Dict[str, StepResult]:
        """执行工作流"""
        self.logger.log_message(f"开始执行工作流: {self.workflow_config.name}")

        for step_config in self.workflow_config.steps:
            try:
                result = await self._execute_step(step_config)
                self.results[step_config.name] = result
                self.logger.log_step_result(result)

                # 保存步骤输出
                self._save_step_output(step_config.name, result.output_data)

            except Exception as e:
                error_result = StepResult(
                    step_name=step_config.name,
                    input_data={},
                    output_data="",
                    duration=0.0,
                    timestamp=datetime.now(),
                    success=False,
                    error_message=str(e)
                )
                self.results[step_config.name] = error_result
                self.logger.log_step_result(error_result)
                self.logger.log_message(f"步骤 {step_config.name} 执行失败: {e}", "ERROR")

        self.logger.log_message("工作流执行完成")
        return self.results

    async def _execute_step(self, step_config: StepConfig) -> StepResult:
        """执行单个步骤"""
        print('-'*30)
        print(f"执行工作流步骤: {step_config.name}")

        start_time = time.time()

        # 准备输入数据
        input_data = self._prepare_step_input(step_config)
        print(f"---input_data: {input_data}")


        # 获取LLM配置并创建实例
        llm_config = self.llm_configs[step_config.llm_name]
        print(f"---create llm: {step_config.llm_name}")

        llm = LLMFactory.create_llm(llm_config)

        # 构建提示
        prompt = self._build_prompt(step_config, input_data)
        print(f"---prompt: {prompt}")

        # 执行LLM调用
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)

        # 清理输出内容
        cleaned_output = LLMFactory.clean_output(response.content)

        print(f"---response.content: {cleaned_output}")


        duration = time.time() - start_time
        print('='*30)

        return StepResult(
            step_name=step_config.name,
            input_data=input_data,
            output_data=cleaned_output,
            duration=duration,
            timestamp=datetime.now(),
            success=True
        )

    def _prepare_step_input(self, step_config: StepConfig) -> Dict[str, Any]:
        """准备步骤输入数据"""
        input_data = {}

        if step_config.name == "architecture_design":
            if hasattr(self.workflow_config, 'requirement') and self.workflow_config.requirement:
                input_data["requirement"] = self.workflow_config.requirement
            else:
                input_data["requirement"] = input("请输入需求描述: ")

        # 添加依赖步骤的输出
        if step_config.depends_on:
            for dep_step in step_config.depends_on:
                if dep_step in self.results:
                    input_data[dep_step] = self.results[dep_step].output_data

        # 添加上下文信息
        if step_config.context_type:
            input_data["context"] = self.context_manager.get_context(step_config.context_type)

        return input_data

    def _build_prompt(self, step_config: StepConfig, input_data: Dict[str, Any]) -> str:
        """构建提示词"""
        prompt_template = ChatPromptTemplate.from_template(step_config.prompt_template)
        return prompt_template.format(**input_data)

    def _save_step_output(self, step_name: str, output: str):
        """保存步骤输出"""
        output_file = Path(self.workflow_config.output_dir) / f"{step_name}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_configs(llm_config_path: str, workflow_config_path: str):
        """加载所有配置"""
        llm_configs = ConfigLoader._load_llm_configs(llm_config_path)
        workflow_config = ConfigLoader._load_workflow_config(workflow_config_path)
        return llm_configs, workflow_config

    @staticmethod
    def _load_llm_configs(config_path: str) -> Dict[str, LLMConfig]:
        """加载LLM配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        llm_configs = {}
        for config_data in data.get("llm_configs", []):
            config = LLMConfig(**config_data)
            llm_configs[config.name] = config

        return llm_configs

    @staticmethod
    def _load_workflow_config(config_path: str) -> WorkflowConfig:
        """加载工作流配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        # 解析上下文配置
        contexts = {}
        for context_name, context_data in data.get("contexts", {}).items():
            contexts[context_name] = ContextConfig(**context_data)

        # 解析步骤配置
        steps = []
        for step_data in data.get("steps", []):
            step_config = StepConfig(
                name=step_data["name"],
                llm_name=step_data["llm_name"],
                prompt_template=step_data["prompt_template"],
                context_type=step_data.get("context_type"),
                depends_on=step_data.get("depends_on", [])
            )
            steps.append(step_config)

        return WorkflowConfig(
            name=data["name"],
            description=data.get("description", ""),
            contexts=contexts,
            steps=steps,
            output_dir=data.get("output_dir", "./output"),
            log_dir=data.get("log_dir", "./logs")
        )


async def main():
    """主函数"""
    # 加载配置
    llm_configs, workflow_config = ConfigLoader.load_configs(
        "llm_config.yaml",
        "workflow_config.yaml"
    )

    # 创建执行器
    executor = WorkflowExecutor(workflow_config, llm_configs)

    # 执行工作流
    results = await executor.execute()

    # 打印结果摘要
    print(f"\n工作流 '{workflow_config.name}' 执行完成")
    print("=" * 50)

    for step_name, result in results.items():
        status = "✅ 成功" if result.success else "❌ 失败"
        print(f"{step_name}: {status} (耗时: {result.duration:.2f}s)")
        if not result.success:
            print(f"  错误: {result.error_message}")

    print(f"\n详细日志: {executor.logger.log_file}")
    print(f"输出目录: {workflow_config.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())