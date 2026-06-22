# Mining Intelligence Agent — 面试演示脚本

## 演示场景 1：基础简报（核心功能）

**查询**：`请给我一份关于 Pilbara 锂矿的简报`

**期望输出结构**：
- Executive Summary: Pilbara 区域概览，5-7 个运营/在建矿山
- Production Overview: 各矿山的产量、产能爬坡/停产状态
- Price Analysis: 锂辉石当前价格 ~US$1,100/t，近6个月趋势
- Investment Signals: 偏多情绪（7.5/10），催化剂+风险
- Data Sources: 标注来源

**关键说辞**：
> "这个 Agent 通过 MCP 协议连接了 3 个独立的数据服务——矿山生产数据、矿价行情、矿业新闻情报——每个服务可以独立部署、独立扩展。Agent 使用 ReAct 循环自动规划数据采集策略，最后合成结构化报告。"

---

## 演示场景 2：实时多工具调用

**查询**：`对比 Pilgangoora 和 Wodgina 的产量，并分析锂辉石价格前景`

**验证点**：
1. Agent 调用了 `get_mine_overview` x2（两个矿山）
2. Agent 调用了 `get_production_trend`（产量对比）
3. Agent 调用了 `get_current_price` + `get_price_forecast`（价格分析）
4. 报告中包含对比数据

**关键说辞**：
> "注意看，Agent 自动判断需要调用哪些工具、按什么顺序调用——它先获取两个矿山的基础信息，发现需要价格背景，再查询价格数据。整个决策过程是 LLM 自主完成的，不是硬编码的工作流。"

---

## 演示场景 3：展示 MCP Server 独立性

**命令行演示**：
```bash
# 单独启动一个 MCP Server 并验证
python -m server_a_mine_production.server
# (展示 MCP 协议握手 + tool listing)

# 在另一个终端
python -m server_b_commodity_price.server
# (展示价格查询 tools)

# 验证 Claude Desktop 配置
python scripts/validate_config.py
```

**关键说辞**：
> "每个 MCP Server 是独立进程，通过 stdio JSON-RPC 通信。你可以把任何一个 Server 单独注册到 Claude Desktop、Cursor 或其他 MCP 客户端——它们是松耦合的。"

---

## 演示场景 4：数据质量

**操作**：展示 `shared_data/` 目录中的 JSON 数据文件

**关键说辞**：
> "数据层做了抽象：目前用的是 curated sample data（来自公开年报、USGS、BMI、Fastmarkets），但 data_loader 的接口设计使得切换到实时 API 只需要改动 data_loader，不影响 server 和 agent 的代码。RSS 拉取接口也已经预留好了。"

---

## 演示场景 5：架构深度

**画架构图**（白板/屏幕共享）：
```
User Query
    │
    ▼
Agent Client (ReAct Loop)
    │       MCP Protocol (stdio JSON-RPC)
    ├────── Mine Production Server ──── shared_data/mines/
    ├────── Commodity Price Server ──── shared_data/prices/
    └────── Mining News Server ─────── shared_data/news/
```

**关键说辞**：
> "我选择手写 ReAct 循环而不是直接用 LangGraph，因为我想展示对 MCP 协议底层和 LLM tool-use 机制的深入理解。同时我也准备了 LangGraph 版本作为对比——两个版本用了同样的 MCP client manager，只是编排层不同。"

---

## 可能的面试追问 & 准备

### Q: 为什么用 stdio 而不是 HTTP/SSE？
> "MCP 协议原生支持两种 transport。stdio 的优势在于：零网络配置、零端口冲突、天然适合本地 agent 场景。如果需要远程访问，可以用 SSE transport 替换——只需要改 `StdioServerParameters` 为 `SseServerParameters`，工具定义保持不变。"

### Q: 如何处理 MCP Server 崩溃？
> "当前实现中，MCPClientManager 在启动时会捕获异常，单个 server 失败不影响其他 server 继续运行。生产环境可以加入健康检查心跳、自动重启、以及工具不可用时的 graceful degradation——Agent 的 ReAct 循环天然支持'工具不可用则尝试替代方案'的模式。"

### Q: 样本数据能换成实时数据吗？
> "可以。data_loader 的函数签名保持不变（`get_mine_by_name(name) -> dict`），只需在内部加入 API 调用逻辑，遇到网络错误时 fallback 到样本数据。这种设计使得系统既可以在离线环境演示，又可以接入实时数据。"

### Q: 12 个 tool 会不会太多，LLM 选不对？
> "这是个好问题。目前的解决方案有三层：1) System prompt 中明确写明了工作流，引导 LLM 按正确顺序调用；2) MCP SDK 的 tool description 提供了充分的上下文；3) 如果需要进一步优化，可以用 LangGraph 的 conditional edges 做显式的工具路由。当前测试中，Claude Sonnet 4 在工具选择上表现非常好。"

### Q: 怎么评估 Agent 的输出质量？
> "可以从几个维度评估：1) 报告结构和完整性——是否覆盖了所有要求的章节；2) 数据准确性——引用的数字是否和 shared_data 一致；3) 工具调用效率——是否有冗余调用或遗漏关键数据。可以用 eval/ 目录的 ground truth Q&A 做自动评测（类似于题目#1 的要求）。"
