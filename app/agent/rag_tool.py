import asyncio

from langchain.tools import tool

from app.rag.service import BusKnowledgeService


knowledge_service = BusKnowledgeService()


@tool
async def search_bus_knowledge(
    question: str
) -> dict:
    """
    查询公交运营知识库中的业务规则和处理规范。

    适合回答：
    - 公交线路低速应该如何处理
    - 客流异常应该采取什么措施
    - GPS数据异常应该如何排查
    - 公交运营、调度和异常处理规则

    本工具查询的是业务知识和处理规则，
    不用于查询某条线路当前的实时速度、实时运行记录等数据。

    如果用户既询问实时运行状态，又询问处理建议，
    应结合实时数据工具和本知识库工具共同回答。
    """

    try:
        # Chroma Retriever目前是同步调用，
        # 放入线程避免阻塞异步Agent
        results = await asyncio.to_thread(
            knowledge_service.search,
            question
        )

        sources = []

        for item in results:
            source = item.get("source", {})
            file_name = source.get("source")

            if file_name and file_name not in sources:
                sources.append(file_name)

        return {
            "ok": True,
            "question": question,
            "sources": sources,
            "knowledge": results
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": "rag_search_failed",
            "message": str(exc)
        }