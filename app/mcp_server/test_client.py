import asyncio

from mcp import Client


async def main():
    async with Client(
        "http://127.0.0.1:8001/mcp"
    ) as client:

        print("\n========== MCP Server ==========")
        print(client.server_info)

        print("\n========== MCP Tools ==========")

        tools = await client.list_tools()

        for tool in tools.tools:
            print(f"- {tool.name}")
            print(f"  描述: {tool.description}")
            print(f"  参数: {tool.input_schema}")
            print()

        result = await client.call_tool(
            "get_route_speed_summary",
            {
                "route_id": 12,
                "window_limit": 10
            }
        )

        print("\n========== MCP Tool Result ==========")

        print("是否错误：", result.is_error)

        print("\n原始内容：")
        for block in result.content:
            print(block)

        print("\n结构化结果：")
        print(result.structured_content)


if __name__ == "__main__":
    asyncio.run(main())