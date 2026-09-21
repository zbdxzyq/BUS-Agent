import httpx

from app.config import settings


async def execute_query(
    sql: str
):
    url = (
        f"{settings.doris_url}"
        f"/api/query/default_cluster/"
        f"{settings.doris_database}"
    )

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.post(
            url,
            auth=(
                settings.doris_user,
                settings.doris_password
            ),
            json={
                "stmt": sql
            }
        )

        response.raise_for_status()

        result = response.json()

    if result.get("code") != 0:
        raise RuntimeError(
            result.get(
                "msg",
                "Doris query failed"
            )
        )

    return result["data"]