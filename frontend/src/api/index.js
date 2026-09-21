import axios from "axios";


// =========================================================
// Axios实例
// =========================================================

const api = axios.create({

  /*
   * 优先读取Vite环境变量。
   *
   * 如果没有配置，
   * 默认使用本地FastAPI。
   */
  baseURL:
    import.meta.env.VITE_API_BASE_URL
    ||
    "http://127.0.0.1:8000",

  /*
   * Agent需要调用：
   *
   * Qwen
   * MCP
   * RAG
   *
   * 本地模型推理可能较慢，
   * 因此这里设置为120秒。
   */
  timeout: 120000,

});


// =========================================================
// 实时线路概览
// =========================================================

export async function getRealtimeRoutes(
  limit = 20
) {

  const response = await api.get(
    "/api/realtime/routes",
    {
      params: {
        limit: limit,
      },
    }
  );

  return response.data;
}


// =========================================================
// 单线路时间窗口明细
// =========================================================

export async function getRouteMetrics(
  routeId,
  limit = 10
) {

  const response = await api.get(
    `/api/realtime/routes/${routeId}`,
    {
      params: {
        limit: limit,
      },
    }
  );

  return response.data;
}


// =========================================================
// Agent Chat
// =========================================================

export async function askBusAgent(
  message
) {

  const response = await api.post(
    "/api/agent/chat",
    {
      message: message,
    }
  );

  return response.data;
}