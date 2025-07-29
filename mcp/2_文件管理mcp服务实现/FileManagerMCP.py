#!/usr/bin/env python3
"""
Cherry Studio MCP 文件管理服务示例
这个MCP服务提供基本的文件管理功能，包括读取、写入、列出文件等操作
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FileManagerMCP:
    """文件管理MCP服务"""

    def __init__(self, base_directory: str = "./workspace"):
        """
        初始化MCP服务

        Args:
            base_directory: 工作目录，默认为 ./workspace
        """
        self.base_directory = Path(base_directory).resolve()
        self.base_directory.mkdir(exist_ok=True)
        logger.info(f"MCP服务初始化，工作目录: {self.base_directory}")

    def _is_safe_path(self, path: str) -> bool:
        """检查路径是否安全（在工作目录内）"""
        try:
            full_path = (self.base_directory / path).resolve()
            return str(full_path).startswith(str(self.base_directory))
        except Exception:
            return False

    async def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """列出目录中的文件"""
        if not self._is_safe_path(directory):
            return {"error": "路径不安全或超出工作目录范围"}

        try:
            target_dir = self.base_directory / directory
            if not target_dir.exists():
                return {"error": f"目录不存在: {directory}"}

            files = []
            for item in target_dir.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime
                })

            return {
                "directory": str(directory),
                "files": files,
                "total": len(files)
            }
        except Exception as e:
            return {"error": f"列出文件失败: {str(e)}"}

    async def read_file(self, filepath: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """读取文件内容"""
        if not self._is_safe_path(filepath):
            return {"error": "路径不安全或超出工作目录范围"}

        try:
            target_file = self.base_directory / filepath
            if not target_file.exists():
                return {"error": f"文件不存在: {filepath}"}

            if not target_file.is_file():
                return {"error": f"不是一个文件: {filepath}"}

            content = target_file.read_text(encoding=encoding)
            return {
                "filepath": str(filepath),
                "content": content,
                "size": len(content),
                "encoding": encoding
            }
        except Exception as e:
            return {"error": f"读取文件失败: {str(e)}"}

    async def write_file(self, filepath: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """写入文件内容"""
        if not self._is_safe_path(filepath):
            return {"error": "路径不安全或超出工作目录范围"}

        try:
            target_file = self.base_directory / filepath
            # 确保父目录存在
            target_file.parent.mkdir(parents=True, exist_ok=True)

            target_file.write_text(content, encoding=encoding)
            return {
                "filepath": str(filepath),
                "size": len(content),
                "encoding": encoding,
                "message": "文件写入成功"
            }
        except Exception as e:
            return {"error": f"写入文件失败: {str(e)}"}

    async def delete_file(self, filepath: str) -> Dict[str, Any]:
        """删除文件"""
        if not self._is_safe_path(filepath):
            return {"error": "路径不安全或超出工作目录范围"}

        try:
            target_file = self.base_directory / filepath
            if not target_file.exists():
                return {"error": f"文件不存在: {filepath}"}

            if target_file.is_file():
                target_file.unlink()
                return {"message": f"文件删除成功: {filepath}"}
            elif target_file.is_dir():
                target_file.rmdir()
                return {"message": f"目录删除成功: {filepath}"}
            else:
                return {"error": f"无法删除: {filepath}"}
        except Exception as e:
            return {"error": f"删除失败: {str(e)}"}

    async def create_directory(self, directory: str) -> Dict[str, Any]:
        """创建目录"""
        if not self._is_safe_path(directory):
            return {"error": "路径不安全或超出工作目录范围"}

        try:
            target_dir = self.base_directory / directory
            target_dir.mkdir(parents=True, exist_ok=True)
            return {"message": f"目录创建成功: {directory}"}
        except Exception as e:
            return {"error": f"创建目录失败: {str(e)}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """返回MCP工具定义"""
        return [
            {
                "name": "list_files",
                "description": "列出指定目录中的文件和子目录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "要列出的目录路径，默认为当前目录",
                            "default": "."
                        }
                    }
                }
            },
            {
                "name": "read_file",
                "description": "读取文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "要读取的文件路径"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "文件编码",
                            "default": "utf-8"
                        }
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "write_file",
                "description": "写入文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "要写入的文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的文件内容"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "文件编码",
                            "default": "utf-8"
                        }
                    },
                    "required": ["filepath", "content"]
                }
            },
            {
                "name": "delete_file",
                "description": "删除文件或空目录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "要删除的文件或目录路径"
                        }
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "create_directory",
                "description": "创建目录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "要创建的目录路径"
                        }
                    },
                    "required": ["directory"]
                }
            }
        ]

    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        try:
            if method == "list_files":
                return await self.list_files(params.get("directory", "."))
            elif method == "read_file":
                return await self.read_file(
                    params["filepath"],
                    params.get("encoding", "utf-8")
                )
            elif method == "write_file":
                return await self.write_file(
                    params["filepath"],
                    params["content"],
                    params.get("encoding", "utf-8")
                )
            elif method == "delete_file":
                return await self.delete_file(params["filepath"])
            elif method == "create_directory":
                return await self.create_directory(params["directory"])
            else:
                return {"error": f"未知方法: {method}"}
        except Exception as e:
            logger.error(f"处理请求失败: {method}, 错误: {str(e)}")
            return {"error": f"处理请求失败: {str(e)}"}


class MCPServer:
    """MCP服务器"""

    def __init__(self):
        self.file_manager = FileManagerMCP()
        logger.info("MCP服务器启动")

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "file-manager-mcp",
                "version": "1.0.0"
            }
        }

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具列表请求"""
        return {
            "tools": self.file_manager.get_tools()
        }

    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        result = await self.file_manager.handle_request(tool_name, arguments)

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ]
        }

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP消息"""
        method = message.get("method")
        params = message.get("params", {})

        if method == "initialize":
            return await self.handle_initialize(params)
        elif method == "tools/list":
            return await self.handle_tools_list(params)
        elif method == "tools/call":
            return await self.handle_tools_call(params)
        else:
            return {"error": {"code": -32601, "message": f"未知方法: {method}"}}


async def main():
    """主函数"""
    server = MCPServer()

    print("Cherry Studio MCP 文件管理服务已启动")
    print("等待来自Cherry Studio的连接...")

    try:
        while True:
            # 从stdin读取JSON-RPC消息
            line = sys.stdin.readline()
            if not line:
                break

            try:
                message = json.loads(line.strip())
                response = await server.handle_message(message)

                # 如果有id，返回响应
                if "id" in message:
                    response["id"] = message["id"]
                    response["jsonrpc"] = "2.0"
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
            except Exception as e:
                logger.error(f"处理消息错误: {e}")

    except KeyboardInterrupt:
        logger.info("服务器关闭")
    except Exception as e:
        logger.error(f"服务器错误: {e}")


if __name__ == "__main__":
    # 运行MCP服务器
    asyncio.run(main())