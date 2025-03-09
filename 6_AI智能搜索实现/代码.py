from duckduckgo_search import DDGS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate


class SearchAssistant:
    def __init__(self):
        self.ddgs = DDGS(proxy="http://127.0.0.1:10809", timeout=20)  # "tb" is an alias for "socks5://127.0.0.1:9150"
        self.llm  = ChatOpenAI(
            base_url="https://api.deepseek.com/v1",  # DeepSeek API端点
            model="deepseek-chat",                  # DeepSeek模型标识
            openai_api_key="sk-xxxxxxxxxxxxx",     # 替换为DeepSeek密钥
            max_tokens=100000,
            temperature=0.7
)

    def _generate_summary(self, text: str, source: tuple) -> str:
        """增强的摘要生成器"""
        prompt_template = """
        请用中文以2-4个要点总结以下内容，保持专业严谨：
        来源：{title} ({url})
        内容：{content}

        要点总结：
        """
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["title", "url", "content"]
        )

        formatted_prompt = prompt.format(
            title=source[0],
            url=source[1],
            content=text[:3000]  # 限制输入长度
        )

        response = self.llm.invoke(formatted_prompt)
        return f"## 来源：{source[0]}\n{response.content}\n链接：{source[1]}\n"

    def search_and_summarize(self, query: str, site: str = None) -> str:
        """完整的搜索摘要流程"""
        try:
            # 构建搜索查询
            search_query = f"site:{site} {query}" if site else query
            # print('------0------')
            # print(search_query)

            # 执行搜索
            results = self.ddgs.text(search_query, max_results=10)
            # print('-----1-----')
            # print(results)


            if not results:
                return "⚠️ 未找到相关结果"

            # 生成摘要
            summaries = []
            i = 1
            for item in results:
                summary = self._generate_summary(
                    text=item['body'],
                    source=(item['title'], item['href'])
                )
                summaries.append(str(i)+'---------------\n'+summary)
                i = i+1

            return "\n".join(summaries)

        except Exception as e:
            return f"❌ 处理出错：{str(e)}"

def main():
    assistant = SearchAssistant()

    # 示例1：普通搜索
    print("## 通用搜索示例：量子计算最新进展")
    print(assistant.search_and_summarize("量子计算最新研究进展"))

    # 示例2：指定网站搜索
    # print("\n## 指定网站示例：Nature上的AI突破")
    # print(assistant.search_and_summarize(
    #     "AI breakthrough",
    #     site="nature.com"
    # ))


if __name__ == "__main__":
    main()