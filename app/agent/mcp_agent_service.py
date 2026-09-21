from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_ollama import ChatOllama

from app.agent.rag_tool import search_bus_knowledge
from app.config import settings


# =========================================================
# LLM
# =========================================================

model = ChatOllama(
    model=settings.ollama_chat_model,
    base_url=settings.ollama_base_url,
    temperature=0,
)


# =========================================================
# Agent System Prompt
# =========================================================

SYSTEM_PROMPT = """
你是城市公交智能运营分析助手。

你具有两类工具能力：

第一类：实时数据工具。
这些工具通过 MCP 动态提供，
用于查询公交线路当前或最近的运行数据。

第二类：公交知识库工具。
search_bus_knowledge 用于查询公交运营规则、
异常处理流程和调度建议。


工具选择规则：

1. 用户明确指定线路号，并询问平均速度、最低速度、
   最高速度或整体速度水平时，
   使用 get_route_speed_summary。

2. 用户明确指定线路号，并询问最近多个时间窗口、
   最近运行记录、窗口明细或趋势时，
   使用 get_route_metrics。

3. 用户没有指定具体线路，而是询问哪些线路较慢、
   有没有低速线路等全局问题时，
   使用 get_slow_routes。

4. 用户询问低速线路如何处理、客流异常如何处理、
   GPS异常如何排查、公交调度规则等业务知识时，
   使用 search_bus_knowledge。

5. 如果用户同时询问某条线路的实际运行状态
   和应该采取什么处理措施，
   应同时使用实时数据工具和 search_bus_knowledge，
   再结合两类结果回答。

6. 不得编造线路号、速度、时间窗口、
   事故、施工、拥堵原因或知识库中不存在的规定。

7. 用户没有明确指定查询数量时，
   使用工具 Schema 中提供的默认值。

8. 如果工具返回没有数据或调用失败，
   必须如实说明。

9. window_limit 只是最大查询数量。
   描述实际统计窗口数量时，
   必须以工具返回的 window_count 为准，
   不得直接把 window_limit 当作实际窗口数量。

10. 如果工具或知识库没有给出明确的正常速度标准、
    阈值或基准，
    不得自行判断某个速度属于“正常”“偏低”或“异常”。

    可以客观陈述：
    “平均速度为33.7 km/h，
    最低窗口平均速度为28.15 km/h”。

    但不得自行写：
    “低于正常水平”。

11. 使用 search_bus_knowledge 后，
    处理建议必须以知识库工具返回的内容为依据。

    不得自行增加知识库中没有明确提供的调度措施、
    管理制度或操作流程。

    可以对知识库内容进行归纳和改写，
    但不能扩展出新的业务规定。

12. 综合实时数据和知识库时，
    必须区分三类信息：

    - 实时数据事实：来自实时数据工具；
    - 可能影响因素：来自知识库，
      但不能说这些因素当前已经发生；
    - 处理建议：仅来自知识库已有规则。

    不得把“可能原因”
    表述成已经确认的事实。

13. 使用知识库回答时，
    在回答最后简要标注知识来源文件名。

14. 不要因为用户在问题中使用
    “低”“慢”“异常”等描述，
    就自动将该描述作为系统已经验证的事实。

    应先查询数据，再根据已有标准判断。

    如果没有明确标准，
    只客观报告工具返回的数据。


回答使用简洁中文。

当同时使用实时数据和知识库时，
尽量将回答组织为：

“实时数据结果”
“知识库建议”
“知识来源”

三个部分。
"""


# =========================================================
# Agent Service
# =========================================================

async def ask_bus_agent_mcp(
    message: str
) -> dict:

    # MCPAdapter负责连接MCP Server，
    # 并动态发现实时业务工具。
    async with MCPAdapter(
        settings.mcp_url
    ) as adapter:

        # -------------------------------------------------
        # ① 动态获取 MCP Tools
        # -------------------------------------------------

        mcp_tools = await adapter.list_tools()

        # -------------------------------------------------
        # ② MCP实时工具 + 本地RAG工具
        # -------------------------------------------------

        all_tools = (
            mcp_tools
            +
            [
                search_bus_knowledge
            ]
        )

        # -------------------------------------------------
        # ③ 创建 Agent
        # -------------------------------------------------

        agent = create_agent(
            model=model,
            tools=all_tools,
            system_prompt=SYSTEM_PROMPT,
        )

        # -------------------------------------------------
        # ④ 执行用户问题
        # -------------------------------------------------

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            }
        )

        # -------------------------------------------------
        # ⑤ 收集 Tool Calling Trace
        # -------------------------------------------------

        tools_used = []

        for msg in result["messages"]:

            tool_calls = getattr(
                msg,
                "tool_calls",
                None,
            )

            if not tool_calls:
                continue

            for call in tool_calls:

                tools_used.append(
                    {
                        "name":
                            call.get("name"),

                        "args":
                            call.get(
                                "args",
                                {}
                            ),
                    }
                )

        # -------------------------------------------------
        # ⑥ 返回前端需要的数据
        # -------------------------------------------------

        return {
            "answer":
                result[
                    "messages"
                ][-1].content,

            "available_tools": [
                tool.name
                for tool in all_tools
            ],

            "tools_used":
                tools_used,
        }