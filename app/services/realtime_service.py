# 业务层
from app.doris_client import execute_query


async def get_latest_route_metrics(limit: int = 20):
    sql = f"""
        SELECT
            window_start,
            route_id,
            window_end,
            gps_count,
            avg_speed
        FROM route_realtime_metrics
        ORDER BY window_start DESC, route_id
        LIMIT {limit}
    """

    result = await execute_query(sql)

    meta = result["meta"]
    rows = result["data"]

    columns = [
        column["name"]
        for column in meta
    ]

    return [
        dict(zip(columns, row))
        for row in rows
    ]

async def get_route_metrics(route_id: int, limit: int = 20):
    sql = f"""
        SELECT
            window_start,
            route_id,
            window_end,
            gps_count,
            avg_speed
        FROM route_realtime_metrics
        WHERE route_id = {route_id}
        ORDER BY window_start DESC
        LIMIT {limit}
    """

    result = await execute_query(sql)

    meta = result["meta"]
    rows = result["data"]

    columns = [
        column["name"]
        for column in meta
    ]

    return [
        dict(zip(columns, row))
        for row in rows
    ]

async def get_slow_routes(speed_threshold: float = 25.0):  # tools 里面是58
    sql = f"""
        SELECT
            window_start,
            route_id,
            window_end,
            gps_count,
            avg_speed
        FROM route_realtime_metrics
        WHERE window_start = (
            SELECT MAX(window_start)
            FROM route_realtime_metrics
        )
        AND avg_speed < {speed_threshold}
        ORDER BY avg_speed ASC
    """

    result = await execute_query(sql)

    columns = [
        column["name"]
        for column in result["meta"]
    ]

    return [
        dict(zip(columns, row))
        for row in result["data"]
    ]

async def get_route_speed_summary(
    route_id: int,
    window_limit: int = 10
):
    sql = f"""
        SELECT
            route_id,
            COUNT(*) AS window_count,
            ROUND(AVG(avg_speed), 2) AS avg_speed,
            ROUND(MIN(avg_speed), 2) AS min_speed,
            ROUND(MAX(avg_speed), 2) AS max_speed
        FROM (
            SELECT
                route_id,
                avg_speed
            FROM route_realtime_metrics
            WHERE route_id = {route_id}
            ORDER BY window_start DESC
            LIMIT {window_limit}
        ) t
        GROUP BY route_id
    """

    result = await execute_query(sql)

    if not result["data"]:
        return None

    columns = [
        column["name"]
        for column in result["meta"]
    ]

    return dict(
        zip(
            columns,
            result["data"][0]
        )
    )