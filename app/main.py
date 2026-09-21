# 接口层
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.database import get_connection, init_database
import sqlite3
from app.services.realtime_service import (
    get_latest_route_metrics,
    get_route_metrics,
    get_slow_routes,
    get_route_speed_summary,
)
from app.agent.mcp_agent_service import ask_bus_agent_mcp
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
init_database()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GPSData(BaseModel):
    vehicle_id: str
    route_id: int
    speed: float

class RouteCreate(BaseModel):
    id: int
    name: str

class RouteUpdate(BaseModel):
    name: str

class AgentChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "BUS-AGENT-30 is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/routes")
def get_routes(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name
            FROM route
            ORDER BY id
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        routes = [dict(row) for row in rows]

        return {
            "count": len(routes),
            "routes": routes
        }

    finally:
        conn.close()

@app.get("/routes/{route_id}")
def get_route(route_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name
            FROM route
            WHERE id = ?
            """,
            (route_id,)
        )

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Route {route_id} not found"
            )

        return dict(row)

    finally:
        conn.close()

@app.post("/gps", status_code=201)
def create_gps(data: GPSData):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO gps_record (vehicle_id, route_id, speed)
        VALUES (?, ?, ?)
        """,
        (data.vehicle_id, data.route_id, data.speed)
    )

    record_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "message": "GPS data created",
        "id": record_id,
        "data": data
    }

@app.get("/gps")
def get_gps_records():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, vehicle_id, route_id, speed
        FROM gps_record
    """)

    rows = cursor.fetchall()

    conn.close()

    records = [dict(row) for row in rows]

    return {
        "count": len(records),
        "records": records
    }

@app.post("/routes", status_code=201)
def create_route(route: RouteCreate):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO route (id, name)
            VALUES (?, ?)
            """,
            (route.id, route.name)
        )

        conn.commit()

    except sqlite3.IntegrityError:
        conn.rollback()

        raise HTTPException(
            status_code=409,
            detail=f"Route {route.id} already exists"
        )

    finally:
        conn.close()

    return {
        "message": "Route created",
        "route": route
    }

@app.put("/routes/{route_id}")
def update_route(route_id: int, route: RouteUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE route
            SET name = ?
            WHERE id = ?
            """,
            (route.name, route_id)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Route {route_id} not found"
            )

        conn.commit()

        return {
            "message": "Route updated",
            "route": {
                "id": route_id,
                "name": route.name
            }
        }

    finally:
        conn.close()

@app.delete("/routes/{route_id}")
def delete_route(route_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM route
            WHERE id = ?
            """,
            (route_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Route {route_id} not found"
            )

        conn.commit()

        return {
            "message": f"Route {route_id} deleted"
        }

    finally:
        conn.close()

@app.get("/api/realtime/routes")
async def get_realtime_routes(limit: int = 20):
    data = await get_latest_route_metrics(limit)

    return {
        "count": len(data),
        "data": data
    }

@app.get("/api/realtime/routes/{route_id}")
async def get_realtime_route(
    route_id: int,
    limit: int = 20
):
    data = await get_route_metrics(
        route_id=route_id,
        limit=limit
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"未找到线路 {route_id} 的实时指标"
        )

    return {
        "route_id": route_id,
        "count": len(data),
        "data": data
    }

@app.get("/api/realtime/alerts/slow-routes")
async def get_slow_route_alerts(
    speed_threshold: float = 25.0
):
    data = await get_slow_routes(speed_threshold)

    return {
        "speed_threshold": speed_threshold,
        "alert_count": len(data),
        "data": data
    }

@app.get("/api/realtime/routes/{route_id}/speed-summary")
async def get_realtime_route_speed_summary(
    route_id: int,
    window_limit: int = 10
):
    data = await get_route_speed_summary(
        route_id=route_id,
        window_limit=window_limit
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"未找到线路 {route_id} 的运行数据"
        )

    return {
        "route_id": route_id,
        "window_limit": window_limit,
        "data": data
    }

@app.post("/api/agent/chat")
async def chat_with_bus_agent(
    request: AgentChatRequest
):
    try:
        result = await ask_bus_agent_mcp(
            request.message
        )

        return {
            "message": request.message,
            "answer": result["answer"],
            "available_tools": result["available_tools"],
            "tools_used": result["tools_used"]
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent 执行失败: {str(exc)}"
        )