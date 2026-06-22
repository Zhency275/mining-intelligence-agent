# Mining Intelligence Agent — Quick Start Guide

基于 MCP (Model Context Protocol) 的矿业情报 Agent，集成 3 个 MCP Server（矿山生产、矿价行情、矿业新闻），通过 ReAct 循环自动生成结构化 Markdown 简报。

## 前置条件

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.11+ | 推荐 3.12 |
| Anthropic API Key | sk-ant-... | 从 [console.anthropic.com](https://console.anthropic.com) 获取 |
| Docker | 可选 | 如使用容器化部署 |

---

## 方式 1：Docker 一键启动（推荐演示用）

```bash
# 1. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY=sk-ant-...

# 2. 启动（使用默认查询：Pilbara 锂矿简报）
docker compose up

# 3. 或指定自定义查询
QUERY="分析锂矿价格走势和 Pilbara 主要矿山产量" docker compose up
```

---

## 方式 2：本地 Python 运行

```bash
# 1. 创建虚拟环境
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 ANTHROPIC_API_KEY

# 4. 运行（默认查询）
python -m agent_client.main

# 5. 自定义查询
python -m agent_client.main --query "请给我一份关于 Pilbara 锂矿的简报"

# 6. 交互模式（逐条提问）
python -m agent_client.main --interactive

# 7. 详细输出模式
python -m agent_client.main --verbose
```

---

## 方式 3：接入 Claude Desktop

将此项目的 MCP Server 注册到 Claude Desktop，让 Claude 直接调用这些工具：

### 步骤

1. **找到 Claude Desktop 配置文件**：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **编辑配置文件**：将 `mcp-config.json` 中的三个 server 配置合并进去。
   > ⚠️ 注意：`cwd` 路径必须改为本机的绝对路径。

```json
{
  "mcpServers": {
    "mine-production": {
      "command": "python",
      "args": ["-m", "server_a_mine_production.server"],
      "cwd": "D:\\mining-intelligence-agent"
    },
    "commodity-price": {
      "command": "python",
      "args": ["-m", "server_b_commodity_price.server"],
      "cwd": "D:\\mining-intelligence-agent"
    },
    "mining-news": {
      "command": "python",
      "args": ["-m", "server_c_mining_news.server"],
      "cwd": "D:\\mining-intelligence-agent"
    }
  }
}
```

3. **重启 Claude Desktop**

4. **验证**：在 Claude Desktop 中询问 "What MCP tools do you have access to?"，应该看到 12 个来自 3 个 server 的 tools。

---

## 项目结构

```
mining-intelligence-agent/
├── server_a_mine_production/    # MCP Server A: 矿山生产数据 (4 tools)
│   ├── server.py                # FastMCP server
│   └── data_loader.py           # 从共享数据加载
├── server_b_commodity_price/    # MCP Server B: 矿价行情 (4 tools)
│   ├── server.py
│   └── data_loader.py
├── server_c_mining_news/        # MCP Server C: 矿业新闻 (4 tools)
│   ├── server.py
│   └── data_loader.py
├── agent_client/                # Agent 客户端
│   ├── agent.py                 # 手写 ReAct 循环
│   ├── mcp_client_manager.py    # MCP 多 server 管理
│   ├── system_prompt.py         # 系统提示词
│   └── main.py                  # CLI 入口
├── shared_data/                 # 样本数据 (JSON)
│   ├── mines/                   # Pilbara 锂矿数据 (7 mines)
│   ├── prices/                  # 3 种矿物 2024-2026 月度价格
│   └── news/                    # 15 条矿业新闻 + 投资信号
├── reports/                     # 生成的报告输出
├── mcp-config.json              # Claude Desktop 配置
├── docker-compose.yml           # Docker 一键启动
├── Dockerfile
├── requirements.txt
├── RUN.md                       # 本文档
└── .env.example
```

## 可用的 MCP Tools（12 个）

### mine-production server
| Tool | 功能 |
|------|------|
| `get_mine_overview` | 获取矿山详细信息 |
| `list_mines_by_region` | 列出区域所有矿山 |
| `get_production_trend` | 获取产量趋势 |
| `search_mines` | 按矿种/国家搜索 |

### commodity-price server
| Tool | 功能 |
|------|------|
| `get_current_price` | 获取当前现货价格 |
| `get_price_history` | 获取历史价格走势 |
| `get_price_forecast` | 获取价格预测 |
| `list_materials` | 列出所有跟踪矿种 |

### mining-news server
| Tool | 功能 |
|------|------|
| `search_news` | 搜索矿业新闻 |
| `get_topic_summary` | 获取主题摘要 |
| `get_investment_indicators` | 获取投资信号 |
| `list_recent_headlines` | 列出近期头条 |

## 示例查询

```bash
# 区域简报
python -m agent_client.main -q "请给我一份关于 Pilbara 锂矿的简报"

# 价格分析
python -m agent_client.main -q "分析锂辉石、碳酸锂和氢氧化锂近6个月的价格走势"

# 投资分析
python -m agent_client.main -q "Pilbara lithium mining investment outlook 2026"

# 矿山对比
python -m agent_client.main -q "对比 Pilgangoora 和 Wodgina 的产量和成本"
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| `ANTHROPIC_API_KEY not set` | 检查 .env 文件是否存在，或手动 export |
| `ModuleNotFoundError: mcp` | `pip install -r requirements.txt` |
| MCP Server 启动失败 | 检查 Python 版本（需 3.11+），验证 `shared_data/` 目录完整性 |
| 工具调用超时 | MCP stdio transport 超时，重启 agent 重试 |
| Claude Desktop 不显示 tools | 检查 `claude_desktop_config.json` 绝对路径和 JSON 语法 |
