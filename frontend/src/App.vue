<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
} from "vue";

import * as echarts from "echarts";

import {
  askBusAgent,
  getRealtimeRoutes,
  getRouteMetrics,
} from "./api";


const routes = ref([]);
const routeHistory = ref([]);

const selectedRouteId = ref(null);

const question = ref("");
const answer = ref("");
const toolsUsed = ref([]);

const routeLoading = ref(false);
const trendLoading = ref(false);
const agentLoading = ref(false);

const overviewChartRef = ref(null);
const trendChartRef = ref(null);

let overviewChart = null;
let trendChart = null;


/*
 * 后端可能返回：
 * [...]
 *
 * 或：
 * {
 *   "data": [...]
 * }
 *
 * 统一转成数组。
 */
function normalizeRows(result) {
  if (Array.isArray(result)) {
    return result;
  }

  if (
    result &&
    Array.isArray(result.data)
  ) {
    return result.data;
  }

  return [];
}


/*
 * /api/realtime/routes 可能包含同一路线的多个窗口。
 *
 * 首页只保留每条线路最新的一条数据。
 */
const latestRoutes = computed(() => {

  const latestMap = new Map();

  for (const item of routes.value) {

    const routeId = item.route_id;

    const oldItem =
      latestMap.get(routeId);

    if (!oldItem) {
      latestMap.set(
        routeId,
        item
      );

      continue;
    }

    const oldTime =
      new Date(
        oldItem.window_start
      ).getTime();

    const newTime =
      new Date(
        item.window_start
      ).getTime();

    if (newTime > oldTime) {
      latestMap.set(
        routeId,
        item
      );
    }
  }

  return Array.from(
    latestMap.values()
  ).sort(
    (a, b) =>
      Number(a.route_id)
      -
      Number(b.route_id)
  );
});


const routeCount = computed(() => {
  return latestRoutes.value.length;
});


const overallAvgSpeed = computed(() => {

  if (
    latestRoutes.value.length === 0
  ) {
    return 0;
  }

  const total =
    latestRoutes.value.reduce(
      (sum, item) =>
        sum +
        Number(
          item.avg_speed || 0
        ),
      0
    );

  return (
    total /
    latestRoutes.value.length
  );
});


const lowestSpeedRoute = computed(() => {

  if (
    latestRoutes.value.length === 0
  ) {
    return null;
  }

  return latestRoutes.value.reduce(
    (lowest, current) => {

      if (
        Number(current.avg_speed)
        <
        Number(lowest.avg_speed)
      ) {
        return current;
      }

      return lowest;
    }
  );
});


const totalGpsCount = computed(() => {

  return latestRoutes.value.reduce(
    (sum, item) =>
      sum +
      Number(
        item.gps_count || 0
      ),
    0
  );
});


async function loadRoutes() {

  routeLoading.value = true;

  try {

    const result =
      await getRealtimeRoutes(
        50
      );

    routes.value =
      normalizeRows(result);


    /*
     * 第一次进入页面时，
     * 自动选择第一条线路。
     */
    if (
      selectedRouteId.value === null
      &&
      latestRoutes.value.length > 0
    ) {
      selectedRouteId.value =
        latestRoutes.value[0]
          .route_id;
    }


    await nextTick();

    renderOverviewChart();


    if (
      selectedRouteId.value
      !== null
    ) {
      await loadRouteHistory(
        selectedRouteId.value
      );
    }

  } catch (error) {

    console.error(
      "加载线路数据失败:",
      error
    );

  } finally {

    routeLoading.value = false;
  }
}


async function loadRouteHistory(
  routeId
) {

  trendLoading.value = true;

  selectedRouteId.value =
    routeId;

  try {

    const result =
      await getRouteMetrics(
        routeId,
        10
      );

    routeHistory.value =
      normalizeRows(result);


    /*
     * Doris查询通常可能按时间倒序返回。
     * 趋势图需要从旧到新显示。
     */
    routeHistory.value.sort(
      (a, b) =>
        new Date(
          a.window_start
        ).getTime()
        -
        new Date(
          b.window_start
        ).getTime()
    );


    await nextTick();

    renderTrendChart();

  } catch (error) {

    console.error(
      "加载线路趋势失败:",
      error
    );

  } finally {

    trendLoading.value = false;
  }
}


function renderOverviewChart() {

  if (!overviewChartRef.value) {
    return;
  }


  if (!overviewChart) {
    overviewChart =
      echarts.init(
        overviewChartRef.value
      );
  }


  const routeNames =
    latestRoutes.value.map(
      item =>
        `${item.route_id}路`
    );


  const speedValues =
    latestRoutes.value.map(
      item =>
        Number(
          Number(
            item.avg_speed
          ).toFixed(2)
        )
    );


  overviewChart.setOption(
    {
      title: {
        text:
          "各线路最新平均速度",
        left: "center",
      },

      tooltip: {
        trigger: "axis",
        formatter(params) {

          const item =
            params[0];

          return (
            `${item.name}<br/>`
            +
            `平均速度：${item.value} km/h`
          );
        },
      },

      grid: {
        left: 50,
        right: 20,
        top: 60,
        bottom: 45,
      },

      xAxis: {
        type: "category",
        data: routeNames,
      },

      yAxis: {
        type: "value",
        name: "km/h",
      },

      series: [
        {
          type: "bar",
          data: speedValues,
          barMaxWidth: 48,
        },
      ],
    },
    true
  );
}


function renderTrendChart() {

  if (!trendChartRef.value) {
    return;
  }


  if (!trendChart) {
    trendChart =
      echarts.init(
        trendChartRef.value
      );
  }


  const times =
    routeHistory.value.map(
      item =>
        formatChartTime(
          item.window_start
        )
    );


  const speeds =
    routeHistory.value.map(
      item =>
        Number(
          Number(
            item.avg_speed
          ).toFixed(2)
        )
    );


  trendChart.setOption(
    {
      title: {
        text:
          `${selectedRouteId.value}路速度趋势`,
        left: "center",
      },

      tooltip: {
        trigger: "axis",
      },

      grid: {
        left: 50,
        right: 20,
        top: 60,
        bottom: 60,
      },

      xAxis: {
        type: "category",
        data: times,
        axisLabel: {
          rotate: 30,
        },
      },

      yAxis: {
        type: "value",
        name: "km/h",
      },

      series: [
        {
          name: "平均速度",
          type: "line",
          data: speeds,
          smooth: true,
          symbolSize: 7,
        },
      ],
    },
    true
  );
}


function formatChartTime(value) {

  if (!value) {
    return "";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date
    .toLocaleTimeString(
      "zh-CN",
      {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }
    );
}


function formatDateTime(value) {

  if (!value) {
    return "-";
  }

  return String(value)
    .replace("T", " ")
    .slice(0, 19);
}


async function sendMessage() {

  const text =
    question.value.trim();

  if (
    !text
    ||
    agentLoading.value
  ) {
    return;
  }


  agentLoading.value = true;

  answer.value = "";

  toolsUsed.value = [];


  try {

    const result =
      await askBusAgent(
        text
      );

    answer.value =
      result.answer || "";

    toolsUsed.value =
      result.tools_used || [];

  } catch (error) {

    console.error(
      "Agent请求失败:",
      error
    );

    answer.value =
      "Agent服务请求失败，请检查 FastAPI、MCP Server 和 Ollama 是否正常运行。";

  } finally {

    agentLoading.value = false;
  }
}


function handleResize() {

  overviewChart?.resize();

  trendChart?.resize();
}


onMounted(async () => {

  window.addEventListener(
    "resize",
    handleResize
  );

  await loadRoutes();
});


onBeforeUnmount(() => {

  window.removeEventListener(
    "resize",
    handleResize
  );

  overviewChart?.dispose();

  trendChart?.dispose();
});
</script>


<template>

  <div class="app">

    <header class="top-header">

      <div>

        <div class="brand-row">

          <div class="logo">
            B
          </div>

          <div>

            <h1>
              BUS-Agent
            </h1>

            <p>
              城市公交实时运行监测与智能决策平台
            </p>

          </div>

        </div>

      </div>


      <button
        class="primary-button"
        :disabled="routeLoading"
        @click="loadRoutes"
      >
        {{
          routeLoading
            ? "刷新中..."
            : "刷新数据"
        }}
      </button>

    </header>


    <!-- 顶部指标卡 -->

    <section class="stats-grid">

      <div class="stat-card">

        <div class="stat-label">
          当前线路数
        </div>

        <div class="stat-value">
          {{ routeCount }}
        </div>

        <div class="stat-unit">
          条线路
        </div>

      </div>


      <div class="stat-card">

        <div class="stat-label">
          最新线路平均速度
        </div>

        <div class="stat-value">

          {{
            overallAvgSpeed
              .toFixed(2)
          }}

        </div>

        <div class="stat-unit">
          km/h
        </div>

      </div>


      <div class="stat-card">

        <div class="stat-label">
          当前最低平均速度
        </div>

        <div class="stat-value">

          {{
            lowestSpeedRoute
              ? Number(
                  lowestSpeedRoute
                    .avg_speed
                ).toFixed(2)
              : "-"
          }}

        </div>

        <div class="stat-unit">

          {{
            lowestSpeedRoute
              ? `${lowestSpeedRoute.route_id}路`
              : "暂无数据"
          }}

        </div>

      </div>


      <div class="stat-card">

        <div class="stat-label">
          最新窗口 GPS 样本
        </div>

        <div class="stat-value">
          {{ totalGpsCount }}
        </div>

        <div class="stat-unit">
          条
        </div>

      </div>

    </section>


    <main class="main-grid">

      <!-- 左侧数据分析 -->

      <div class="left-column">


        <section class="panel">

          <div class="panel-header">

            <div>

              <h2>
                实时运行概览
              </h2>

              <p>
                每条线路最新统计窗口
              </p>

            </div>

          </div>


          <div
            ref="overviewChartRef"
            class="chart"
          />

        </section>


        <section class="panel">

          <div class="panel-header">

            <div>

              <h2>
                单线路速度趋势
              </h2>

              <p>
                最近时间窗口平均速度变化
              </p>

            </div>


            <select
              v-model="selectedRouteId"
              @change="
                loadRouteHistory(
                  selectedRouteId
                )
              "
            >

              <option
                v-for="route in latestRoutes"
                :key="route.route_id"
                :value="route.route_id"
              >
                {{ route.route_id }} 路
              </option>

            </select>

          </div>


          <div
            v-if="trendLoading"
            class="loading-text"
          >
            正在加载趋势数据...
          </div>


          <div
            ref="trendChartRef"
            class="chart"
          />

        </section>


        <section class="panel">

          <div class="panel-header">

            <div>

              <h2>
                最新线路指标
              </h2>

              <p>
                Flink窗口聚合结果
              </p>

            </div>

          </div>


          <div class="table-wrapper">

            <table>

              <thead>

                <tr>
                  <th>线路</th>
                  <th>窗口开始</th>
                  <th>GPS数</th>
                  <th>平均速度</th>
                </tr>

              </thead>


              <tbody>

                <tr
                  v-for="route in latestRoutes"
                  :key="route.route_id"
                >

                  <td class="route-name">

                    {{ route.route_id }}路

                  </td>

                  <td>

                    {{
                      formatDateTime(
                        route.window_start
                      )
                    }}

                  </td>

                  <td>

                    {{ route.gps_count }}

                  </td>

                  <td>

                    {{
                      Number(
                        route.avg_speed
                      ).toFixed(2)
                    }}
                    km/h

                  </td>

                </tr>


                <tr
                  v-if="
                    latestRoutes.length
                    === 0
                  "
                >

                  <td
                    colspan="4"
                    class="empty"
                  >
                    暂无实时数据
                  </td>

                </tr>

              </tbody>

            </table>

          </div>

        </section>

      </div>


      <!-- 右侧Agent -->

      <aside class="panel agent-panel">

        <div class="panel-header">

          <div>

            <h2>
              AI 运营助手
            </h2>

            <p>
              MCP 实时数据 + RAG 运营知识
            </p>

          </div>

          <span class="status-badge">
            Agent Online
          </span>

        </div>


        <div class="quick-questions">

          <button
            @click="
              question =
                '12路平均速度是多少？'
            "
          >
            查询12路速度
          </button>

          <button
            @click="
              question =
                'GPS数据长时间不更新应该怎么排查？'
            "
          >
            GPS异常排查
          </button>

          <button
            @click="
              question =
                '12路最近运行速度比较低，应该怎么处理？'
            "
          >
            MCP + RAG
          </button>

        </div>


        <div class="chat-input">

          <textarea
            v-model="question"
            placeholder="输入公交运营问题，例如：12路最近运行速度比较低，应该怎么处理？"
            @keydown.ctrl.enter="
              sendMessage
            "
          />

          <button
            class="primary-button send-button"
            :disabled="agentLoading"
            @click="sendMessage"
          >

            {{
              agentLoading
                ? "Agent分析中..."
                : "发送问题"
            }}

          </button>

        </div>


        <div class="answer-section">

          <div class="section-label">
            Agent 回答
          </div>


          <div
            v-if="agentLoading"
            class="agent-loading"
          >

            <div class="loading-dot" />

            正在调用工具并分析数据...

          </div>


          <div
            v-else-if="answer"
            class="answer-text"
          >

            {{ answer }}

          </div>


          <div
            v-else
            class="empty-answer"
          >

            <div class="empty-icon">
              AI
            </div>

            <p>
              可以询问实时线路状态、
              历史窗口数据以及公交运营处理规则。
            </p>

          </div>

        </div>


        <div
          v-if="
            toolsUsed.length > 0
          "
          class="trace-section"
        >

          <div class="section-label">
            Agent Tool Trace
          </div>


          <div
            v-for="
              (tool, index)
              in toolsUsed
            "
            :key="index"
            class="trace-card"
          >

            <div class="trace-index">
              {{ index + 1 }}
            </div>


            <div class="trace-content">

              <strong>
                {{ tool.name }}
              </strong>

              <pre>{{
                JSON.stringify(
                  tool.args,
                  null,
                  2
                )
              }}</pre>

            </div>

          </div>

        </div>

      </aside>

    </main>

  </div>

</template>


<style scoped>

:global(*) {
  box-sizing: border-box;
}


:global(body) {
  margin: 0;
  background: #f4f7fb;
}


:global(button),
:global(textarea),
:global(select) {
  font-family:
    Inter,
    "Microsoft YaHei",
    Arial,
    sans-serif;
}


.app {
  min-height: 100vh;
  padding: 28px 34px 40px;
  color: #1f2937;
  font-family:
    Inter,
    "Microsoft YaHei",
    Arial,
    sans-serif;
}


.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 26px;
}


.brand-row {
  display: flex;
  gap: 14px;
  align-items: center;
}


.logo {
  width: 48px;
  height: 48px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1f2937;
  color: white;
  font-size: 24px;
  font-weight: 700;
}


.top-header h1 {
  margin: 0;
  font-size: 27px;
}


.top-header p {
  margin: 5px 0 0;
  color: #6b7280;
  font-size: 14px;
}


.primary-button {
  border: none;
  border-radius: 9px;
  padding: 11px 18px;
  background: #1f2937;
  color: white;
  font-weight: 600;
  cursor: pointer;
}


.primary-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}


.stats-grid {
  display: grid;
  grid-template-columns:
    repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 20px;
}


.stat-card {
  padding: 19px 21px;
  background: white;
  border: 1px solid #e8edf3;
  border-radius: 13px;
  box-shadow:
    0 5px 18px
    rgba(15, 23, 42, 0.045);
}


.stat-label {
  font-size: 13px;
  color: #6b7280;
}


.stat-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 700;
}


.stat-unit {
  margin-top: 3px;
  color: #87909d;
  font-size: 12px;
}


.main-grid {
  display: grid;
  grid-template-columns:
    minmax(0, 1.45fr)
    minmax(360px, 0.8fr);
  gap: 20px;
  align-items: start;
}


.left-column {
  display: grid;
  gap: 20px;
}


.panel {
  background: white;
  border: 1px solid #e8edf3;
  border-radius: 14px;
  padding: 20px;
  box-shadow:
    0 5px 18px
    rgba(15, 23, 42, 0.045);
}


.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}


.panel-header h2 {
  margin: 0;
  font-size: 17px;
}


.panel-header p {
  margin: 5px 0 0;
  color: #89919c;
  font-size: 12px;
}


.chart {
  width: 100%;
  height: 310px;
  margin-top: 12px;
}


select {
  min-width: 110px;
  padding: 8px 10px;
  border: 1px solid #dce2e8;
  border-radius: 8px;
  background: white;
}


.table-wrapper {
  overflow-x: auto;
  margin-top: 16px;
}


table {
  width: 100%;
  border-collapse: collapse;
}


th {
  padding: 11px 13px;
  background: #f8fafc;
  color: #657080;
  font-size: 12px;
  font-weight: 600;
  text-align: left;
}


td {
  padding: 13px;
  border-bottom: 1px solid #edf0f4;
  font-size: 13px;
}


.route-name {
  font-weight: 700;
}


.empty {
  text-align: center;
  color: #999;
}


.agent-panel {
  position: sticky;
  top: 20px;
  min-height: 720px;
}


.status-badge {
  padding: 5px 9px;
  border-radius: 20px;
  background: #eef7ef;
  font-size: 11px;
  color: #43734a;
}


.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 20px;
}


.quick-questions button {
  border: 1px solid #dce2e8;
  border-radius: 18px;
  background: #fafbfc;
  padding: 7px 11px;
  cursor: pointer;
  font-size: 12px;
}


.chat-input {
  margin-top: 17px;
}


textarea {
  width: 100%;
  height: 120px;
  resize: vertical;
  border: 1px solid #d9dfe7;
  border-radius: 10px;
  padding: 12px;
  outline: none;
  line-height: 1.6;
}


textarea:focus {
  border-color: #6b7280;
}


.send-button {
  width: 100%;
  margin-top: 9px;
}


.answer-section,
.trace-section {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid #edf0f4;
}


.section-label {
  margin-bottom: 12px;
  color: #647080;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}


.answer-text {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
}


.empty-answer {
  padding: 50px 25px;
  text-align: center;
  color: #929aa5;
}


.empty-icon {
  width: 46px;
  height: 46px;
  margin: auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  font-weight: 700;
}


.agent-loading {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #6b7280;
  font-size: 13px;
}


.loading-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #4b5563;
  animation:
    pulse 1s infinite;
}


.trace-card {
  display: flex;
  gap: 11px;
  padding: 11px;
  margin-top: 9px;
  border-radius: 9px;
  background: #f7f9fb;
}


.trace-index {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e7ebef;
  font-size: 11px;
  font-weight: 700;
}


.trace-content {
  min-width: 0;
}


.trace-content strong {
  font-size: 13px;
}


.trace-content pre {
  margin: 6px 0 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #657080;
  font-size: 11px;
}


.loading-text {
  padding: 10px 0;
  color: #888;
  font-size: 12px;
}


@keyframes pulse {

  0%,
  100% {
    opacity: 0.35;
  }

  50% {
    opacity: 1;
  }
}


@media (
  max-width: 1100px
) {

  .stats-grid {
    grid-template-columns:
      repeat(2, 1fr);
  }

  .main-grid {
    grid-template-columns: 1fr;
  }

  .agent-panel {
    position: static;
  }
}


@media (
  max-width: 650px
) {

  .app {
    padding: 18px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .top-header {
    align-items: flex-start;
  }
}

</style>