# 矿业情报 Agent — 基于 MCP 协议的多智能体系统

> 24h 限时项目 | 面试题目 #2

基于 **MCP (Model Context Protocol)** 协议构建的矿业情报分析系统，集成 3 个独立 MCP Server（矿山生产、矿价行情、矿业新闻），通过 ReAct Agent 自动编排工具调用，生成结构化 Markdown 情报简报。

---

## 架构概览

```
User Query ("Pilbara 锂矿简报")
       │
       ▼
┌──────────────────────────────┐
│   Agent Client (ReAct 循环)   │  ← 手写编排层，无框架依赖
│   Anthropic SDK tool-use API │
└──────┬───────┬───────┬───────┘
       │ MCP stdio │       │
       ▼           ▼       ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Server A │ │ Server B │ │ Server C │
│ 矿山生产 │ │ 矿价行情 │ │ 矿业新闻 │
│ 4 tools  │ │ 4 tools  │ │ 4 tools  │
└──────────┘ └──────────┘ └──────────┘
       │           │           │
       └───────────┼───────────┘
                   ▼
            shared_data/ (JSON)
```

## 快速开始

### 前置条件
- Python 3.11+
- Anthropic API Key（[获取地址](https://console.anthropic.com)）

### 一步启动

```bash
# 1. 克隆仓库
git clone <repo-url> && cd mining-intelligence-agent

# 2. 创建虚拟环境并安装依赖
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. 设置 API Key
set ANTHROPIC_API_KEY=sk-ant-...                 # Windows
# export ANTHROPIC_API_KEY=sk-ant-...            # macOS/Linux

# 4. 运行 Agent
python -m agent_client.main --query "请给我一份关于 Pilbara 锂矿的简报"
```

### Docker 启动（无需 Python 环境）

```bash
cp .env.example .env   # 编辑填入 ANTHROPIC_API_KEY
docker compose up
```

## 三个 MCP Server

### Server A: `mine-production` — 矿山生产数据

| Tool | 功能 |
|------|------|
| `get_mine_overview` | 获取矿山详细信息（产量、储量、经营者、矿种） |
| `list_mines_by_region` | 按区域列出所有矿山 |
| `get_production_trend` | 获取年度产量趋势 |
| `search_mines` | 按矿种/国家搜索矿山 |

**数据**：7 个西澳锂矿实体的公开数据（Pilgangoora, Wodgina, Greenbushes, Mt Marion, Kathleen Valley, Bald Hill, Ngungaju）

### Server B: `commodity-price` — 矿价行情

| Tool | 功能 |
|------|------|
| `get_current_price` | 获取当前现货价格 + 环比变化 |
| `get_price_history` | 获取月度历史价格走势 |
| `get_price_forecast` | 获取 6-12 个月分析师共识预测 |
| `list_materials` | 列出所有跟踪的电池矿物 |

**数据**：锂辉石 SC6、碳酸锂、氢氧化锂 2024.01—2026.06 月度价格

### Server C: `mining-news` — 矿业新闻与投资情报

| Tool | 功能 |
|------|------|
| `search_news` | 按关键词搜索新闻（含情感标签） |
| `get_topic_summary` | 获取主题聚合摘要 + 情感分布 |
| `get_investment_indicators` | 获取投资催化剂、风险、建议 |
| `list_recent_headlines` | 列出区域近期头条 |

**数据**：15 条 Pilbara 锂矿新闻（来源：Mining Weekly, BMI, Reuters, AFR 等）

## Agent 设计

### ReAct 循环（手写实现）

```
Iteration 1:  用户查询 → 分析需求 → 并行调用 6 个 MCP tools
Iteration 2:  所有数据就绪 → 合成结构化 Markdown 报告
```

- **编排层**：手写 ReAct 循环（`agent_client/agent.py`），无框架依赖，展示对 MCP 协议和 LLM tool-use 机制的深层理解
- **MCP 连接**：使用 `contextlib.AsyncExitStack` 管理 3 个 stdio 子进程生命周期
- **模型**：Claude Sonnet 4 / Opus 4，通过 Anthropic SDK 调用

### 核心代码量

| 模块 | 行数 | 说明 |
|------|------|------|
| ReAct Agent | ~120 | 手写编排循环 |
| MCP Client Manager | ~140 | 多 server 生命周期管理 |
| 每个 MCP Server | ~55 | FastMCP 工具定义 |
| 每个 Data Loader | ~80 | 数据加载 + 查询逻辑 |

## 接入 Claude Desktop

将 `mcp-config.json` 中的 server 配置合并到 `%APPDATA%\Claude\claude_desktop_config.json`，重启 Claude Desktop 即可在对话中直接调用 12 个矿业情报工具。

```json
{
  "mcpServers": {
    "mine-production": {
      "command": "python",
      "args": ["-m", "server_a_mine_production.server"],
      "cwd": "D:\\mining-intelligence-agent"
    }
    // ... 另外 2 个 server 同理
  }
}
```

## 运行测试

```bash
pytest server_a_mine_production server_b_commodity_price server_c_mining_news agent_client -v
```

37 个单元测试覆盖所有数据加载器、工具调用和 Agent 组件。

## 项目结构

```
mining-intelligence-agent/
├── agent_client/                 # Agent 客户端
│   ├── agent.py                  # 手写 ReAct 循环
│   ├── mcp_client_manager.py     # MCP 多 server 管理
│   ├── system_prompt.py          # 系统提示词
│   └── main.py                   # CLI 入口
├── server_a_mine_production/     # MCP Server A: 矿山生产
├── server_b_commodity_price/     # MCP Server B: 矿价行情
├── server_c_mining_news/         # MCP Server C: 矿业新闻
├── shared_data/                  # 样本数据 (7 mines + 3 prices + 15 news)
├── mcp-config.json               # Claude Desktop MCP 配置
├── docker-compose.yml            # Docker 一键启动
├── RUN.md                        # 详细运行指南
├── docs/demo_script.md           # 演示脚本 + 面试追问准备
└── requirements.txt              # Python 依赖
```

## 技术选型

| 决策 | 选择 | 理由 |
|------|------|------|
| MCP Transport | stdio | 零网络配置，天然适合本地 Agent |
| MCP SDK | `mcp>=1.2` (FastMCP) | 官方维护，v1.x 稳定 |
| Agent 框架 | 手写 ReAct（主）+ LangGraph 可选 | 展示底层理解，减少框架依赖 |
| 数据层 | 抽象 data_loader → 可替换实时 API | 接口不变，切换数据源零改动 |
| 样本数据 | 公开来源的真实数据 | 可验证，不编造 |

## 设计亮点

1. **松耦合架构**：3 个 MCP Server 独立可部署，任一个可单独接入 Claude Desktop / Cursor
2. **容错设计**：单个 Server 启动失败不影响其他 Server，Agent 自动跳过不可用工具
3. **数据透明**：每条数据标注来源，样本数据明确标记，实时数据有独立 fallback 路径
4. **可扩展**：新增数据源只需添加 data_loader 函数，Server 和 Agent 无需改动
5. **面试友好**：手写 ReAct 循环 (~120 行) 展示核心能力，LangGraph 版本展示框架能力

## License

MIT
