import os

from duckduckgo_search import DDGS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer, util


class SearchAssistant:
    def __init__(self):
        self.ddgs = DDGS(proxy="http://127.0.0.1:10809", timeout=20)
        self.llm = ChatOpenAI(
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            openai_api_key="sk-xxxxxxxxxxxxxxxxxxxxx",
            max_tokens=100000,
            temperature=0.7
        )

        # paraphrase-MiniLM-L6-v2 用于去重
        # 尝试加载 SentenceTransformer，失败则禁用去重
        try:
            # 如果有本地模型路径，替换为本地路径
            local_model_path = "G:/ai/ai_model/paraphrase-MiniLM-L6-v2"
            if os.path.exists(os.path.expanduser(local_model_path)):
                self.sentence_model = SentenceTransformer(local_model_path)
            else:
                self.sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2') # 首次会从网络下载
            self.duplicate_detection_enabled = True
        except Exception as e:
            print(f"⚠️ 无法加载SentenceTransformer: {e}，去重功能已禁用")
            self.duplicate_detection_enabled = False

    def _generate_summary(self, text: str, source: tuple) -> str:
        """生成单个结果摘要"""
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
            content=text[:2000]
        )
        response = self.llm.invoke(formatted_prompt)
        return response.content

    def _check_accuracy(self, text: str, source: str) -> float:
        """评估结果准确性（0-1）"""
        prompt = f"评估以下内容的准确性（逻辑性、一致性、可信度），返回0-1的分数:\n来源:{source}\n内容:{text[:3000]}"
        response = self.llm.invoke(prompt)
        try:
            score = float(response.content.strip())  # 假设模型返回一个数字
        except:
            score = 0.5  # 默认中等可信度
        return min(max(score, 0), 1)  # 限制在0-1之间

    def _extract_keywords(self, texts: list) -> list:
        """从搜索结果提取关键词"""
        all_text = " ".join(texts)
        prompt = f"从以下文本提取3个最相关的关键词:\n{all_text[:5000]}"
        response = self.llm.invoke(prompt)
        return response.content.split()[:3]  # 假设返回空格分隔的词

    def _detect_duplicates(self, results: list) -> int:
        """检测重复结果数量"""
        embeddings = self.sentence_model.encode([r['body'] for r in results], convert_to_tensor=True)
        similarities = util.pytorch_cos_sim(embeddings, embeddings)
        duplicates = 0
        for i in range(len(similarities)):
            for j in range(i + 1, len(similarities)):
                if similarities[i][j] > 0.8:  # 相似度阈值
                    duplicates += 1
        return duplicates

    def search_and_summarize(self, query: str, site: str = None) -> str:
        """优化后的搜索与报告生成流程"""
        try:
            # 初次搜索
            search_query = f"site:{site} {query}" if site else query
            results = self.ddgs.text(search_query, max_results=5)
            if not results:
                return "⚠️ 未找到相关结果"

            # 处理初次结果
            summaries = []
            processed_results = []
            for i, item in enumerate(results, 1):
                summary = self._generate_summary(item['body'], (item['title'], item['href']))
                accuracy = self._check_accuracy(item['body'], item['href'])
                processed_results.append({
                    "index": i,
                    "title": item['title'],
                    "url": item['href'],
                    "summary": summary,
                    "accuracy": accuracy,
                    "body": item['body']
                })
                summaries.append(f"{i}---------------\n## 来源：{item['title']}\n{summary}\n链接：{item['href']}\n准确性评分：{accuracy:.2f}")

            # 去重分析
            duplicates = self._detect_duplicates(results)

            # 提取关键词并二次搜索
            keywords = self._extract_keywords([r['body'] for r in results])
            secondary_summaries = []
            for kw in keywords:
                secondary_results = self.ddgs.text(kw, max_results=3)
                for item in secondary_results:
                    summary = self._generate_summary(item['body'], (item['title'], item['href']))
                    secondary_summaries.append(f"## 来源：{item['title']}\n{summary}\n链接：{item['href']}")

            # 按准确性排序
            processed_results.sort(key=lambda x: x['accuracy'], reverse=True)
            sorted_summaries = [f"{r['index']}---------------\n## 来源：{r['title']}\n{r['summary']}\n链接：{r['url']}\n准确性评分：{r['accuracy']:.2f}" for r in processed_results]

            # 生成报告
            report = [
                "## 搜索报告",
                f"查询：{query}",
                f"初次结果数量：{len(results)}",
                f"重复结果数量：{duplicates}",
                f"提取关键词：{', '.join(keywords)}",
                f"二次搜索结果数量：{len(secondary_summaries)}",
                "\n### 初次搜索结果（按相关性排序）",
                "\n".join(sorted_summaries),
                "\n### 二次搜索推荐结果",
                "\n".join(secondary_summaries) if secondary_summaries else "无推荐结果"
            ]

            return "\n".join(report)

        except Exception as e:
            return f"❌ 处理出错：{str(e)}"

def main():
    assistant = SearchAssistant()
    print("## 通用搜索示例：量子计算最新进展")
    print(assistant.search_and_summarize("量子计算最新研究进展"))

if __name__ == "__main__":
    main()