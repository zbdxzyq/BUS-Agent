from typing import Annotated, Any

import httpx
from mcp.server import MCPServer
from pydantic import Field

from app.config import settings


# =========================================================
# MCP Server
# =========================================================

mcp = MCPServer(
    "bus-agent-mcp"
)


# =========================================================
# FastAPI统一请求函数
# =========================================================

async def request_api(
    path: str,
    params: dict | None = None,
) -> dict:
    """
    统一请求 BUS-Agent 的 FastAPI 业务接口。

    MCP Tool 不直接操作 Doris，
    而是复用已经存在的 FastAPI 业务能力。
    """

    try:

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            response = await client.get(
                f"{settings.api_base_url}{path}",
                params=params,
            )

        # FastAPI返回404时，
        # 转换为结构化Tool结果，
        # 避免Agent直接因为异常而失败。
        if response.status_code == 404:

            return {
                "ok": False,
                "error": "not_found",
                "message": "没有找到对应数据",
            }

        response.raise_for_status()

        return response.json()

    except httpx.HTTPError as exc:

        return {
            "ok": False,
            "error": "api_request_failed",
            "message": str(exc),
        }


# =========================================================
# Tool 1
# 线路速度汇总
# =========================================================

@mcp.tool(
    description=(
        "查询某一条公交线路最近若干时间窗口的速度汇总统计，"
        "包括实际统计窗口数量、平均速度、最低窗口平均速度"
        "和最高窗口平均速度。"
        "用户未指定窗口数量时使用10。"
    )
)
async def get_route_speed_summary(
    route_id: Annotated[
        int,
        Field(
            ge=1,
            description=(
                "公交线路编号，"
                "例如12表示12路公交"
            ),
        ),
    ],

    window_limit: Annotated[
        int,
        Field(
            ge=1,
            le=50,
            description=(
                "最多查询最近多少个时间窗口，"
                "范围1到50，"
                "用户未指定时使用10"
            ),
        ),
    ] = 10,

) -> dict[str, Any]:

    return await request_api(
        (
            f"/api/realtime/routes/"
            f"{route_id}/speed-summary"
        ),
        {
            "window_limit":
                window_limit
        },
    )


# =========================================================
# Tool 2
# 单线路窗口明细
# =========================================================

@mcp.tool(
    description=(
        "查询某一条明确指定公交线路最近多个时间窗口的"
        "运行明细。"
        "适合查看最近窗口的平均速度、GPS数量、"
        "窗口时间和运行记录。"
        "用户没有指定返回数量时使用10。"
    )
)
async def get_route_metrics(
    route_id: Annotated[
        int,
        Field(
            ge=1,
            description="公交线路编号",
        ),
    ],

    limit: Annotated[
        int,
        Field(
            ge=1,
            le=50,
            description=(
                "最多返回最近多少个时间窗口，"
                "范围1到50，默认10"
            ),
        ),
    ] = 10,

) -> dict[str, Any]:

    return await request_api(
        (
            f"/api/realtime/routes/"
            f"{route_id}"
        ),
        {
            "limit":
                limit
        },
    )


# =========================================================
# Tool 3
# 全局低速线路查询
# =========================================================

@mcp.tool(
    description=(
        "查询当前数据中平均速度低于指定阈值的公交线路。"
        "适合回答哪些线路运行较慢、"
        "有没有低速线路等全局问题。"
        "只有用户询问全局线路情况时使用。"
    )
)
async def get_slow_routes(
    speed_threshold: Annotated[
        float,
        Field(
            gt=0,
            le=100,
            description=(
                "低速查询阈值，"
                "单位km/h，默认25。"
                "该值是查询条件，"
                "不代表整个业务系统统一认定的异常标准。"
            ),
        ),
    ] = 25.0,

) -> dict[str, Any]:

    return await request_api(
        "/api/realtime/alerts/slow-routes",
        {
            "speed_threshold":
                speed_threshold
        },
    )


# =========================================================
# Server启动
# =========================================================

if __name__ == "__main__":

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
    )