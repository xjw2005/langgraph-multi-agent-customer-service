# 🤖 智能电商客服系统

基于 LangGraph 构建的完整智能客服解决方案，支持多 Agent 协作、历史回溯和数据持久化。

## 🎯 项目特性

- **多 Agent 协作**：订单、商品、售后、支付、物流等专业 Agent
- **智能路由**：自动识别用户意图，分配给合适的专业 Agent
- **历史回溯**：完整的对话历史和状态管理
- **数据持久化**：SQLite + LangGraph Checkpoints
- **人工介入**：复杂问题自动升级到人工客服
- **性能监控**：Agent 处理效果和用户满意度统计

## 📁 项目结构

```
智能客服系统/
├── README.md                 # 项目说明
├── requirements.txt          # 依赖包
├── config/
│   ├── __init__.py
│   ├── settings.py          # 配置文件
│   └── database.py          # 数据库配置
├── core/
│   ├── __init__.py
│   ├── states.py            # 状态定义
│   ├── router.py            # 路由 Agent
│   └── main_graph.py        # 主工作流
├── agents/
│   ├── __init__.py
│   ├── base_agent.py        # Agent 基类
│   ├── order_agent.py       # 订单 Agent
│   ├── product_agent.py     # 商品 Agent
│   ├── refund_agent.py      # 售后 Agent
│   ├── payment_agent.py     # 支付 Agent
│   ├── logistics_agent.py   # 物流 Agent
│   └── human_agent.py       # 人工转接 Agent
├── services/
│   ├── __init__.py
│   ├── database_service.py  # 数据库服务
│   ├── history_service.py   # 历史管理服务
│   └── mock_apis.py         # 模拟外部 API
├── utils/
│   ├── __init__.py
│   ├── logger.py            # 日志工具
│   └── helpers.py           # 辅助函数
├── tests/
│   ├── __init__.py
│   ├── test_agents.py       # Agent 测试
│   └── test_integration.py  # 集成测试
├── examples/
│   ├── basic_demo.py        # 基础演示
│   ├── advanced_demo.py     # 高级功能演示
│   └── performance_test.py  # 性能测试
└── data/
    ├── customer_service.db   # SQLite 数据库
    └── sample_data.sql       # 示例数据
```

## 🚀 快速开始

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API 配置
```

3. **初始化数据库**
```bash
python -m services.database_service
```

4. **运行演示**
```bash
python examples/basic_demo.py
```

## 💡 核心概念

### Agent 架构
- **路由 Agent**：分析用户意图，选择合适的专业 Agent
- **专业 Agent**：处理特定领域的业务逻辑
- **历史 Agent**：并行运行，记录所有交互和状态变化

### 状态管理
- 统一的状态结构，支持复杂的业务数据流转
- LangGraph Checkpoints 实现状态持久化和回溯
- 支持分支对话和状态恢复

### 数据持久化
- 用户档案和偏好学习
- 完整的对话历史记录
- 业务数据缓存和查询优化

## 📊 使用示例

```python
from core.main_graph import CustomerServiceSystem

# 创建客服系统实例
cs_system = CustomerServiceSystem()

# 处理用户咨询
result = cs_system.process_message(
   d="user_123",
    message="我想查询订单 ORD001 的物流信息"
)

print(result["response"])
# 输出：您的订单 ORD001 已发货，预计明天下午送达...
```

## 🔧 扩展指南

### 添加新的 Agent
1. 继承 `BaseAgent` 类
2. 实现 `process` 方法
3. 在路由 Agent 中注册新的意图识别

### 自定义业务逻辑
1. 修改 `states.py` 添加新的状态字段
2. 在相应的 Agent 中实现业务逻辑
3. 更新数据库 schema（如需要）

## 📈 性能监控

系统内置性能监控功能：
- Agent 处理时间统计
- 用户满意度跟踪
- 人工介入率分析
- 常见问题识别

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License