基于我对OpenAI Customer Service Agent Demo的分析，让我为你总结一下这个agent的设计架构和实现方式：
https://github.com/openai/openai-cs-agents-demo/tree/main/python-backend

## 1. 我理解的用户需求

你想了解OpenAI的客服Agent demo是如何设计的，特别关注：* Agent架构设计

* Prompt工程方法
* 具体的prompt示例
* Guardrail(护栏)机制实现

## 2. 当前处理流程分析

这个OpenAI Customer Service Agent Demo基于OpenAI Agents SDK构建，采用了多Agent协作的架构模式：

### 核心架构设计：

1. 多Agent分工合作模式：* Triage Agent（分流Agent）：负责理解用户意图，将请求路由到合适的专业Agent

* Seat Booking Agent（座位预订Agent）：处理座位变更相关请求
* Flight Status Agent（航班状态Agent）：查询航班信息
* Cancellation Agent（取消Agent）：处理航班取消业务
* FAQ Agent（常见问题Agent）：回答一般性问题

2. Handoff机制：* 通过Agent之间的"交接"实现任务的动态路由

* 每个Agent可以定义handoff_descriptions来帮助其他Agent理解何时转接

## 3. Prompt工程方式

系统采用结构化的Prompt设计：

python

Apply to mcp.json

**# 基本Agent定义**

**agent **=** **Agent**(**

**    **name**=**"Triage Agent"**,**

**    **instructions**=**"You determine which agent to use based on the use**r's request"**,

**    **handoffs**=**[**seat_booking_agent**,** flight_status_agent**,** cancellation_agent**,** faq_agent**]

**)**

每个Agent都有：* name: Agent名称

* instructions: 具体的工作指令（这就是核心prompt）
* handoffs: 可以转接的其他Agent列表
* handoff_description: 转接描述，帮助其他Agent理解何时转接

## 4. Guardrail护栏机制

该系统实现了两种Guardrail：

1. Relevance Guardrail（相关性护栏）：

python

Apply to mcp.json

**@input_guardrail**

**async** **def** **relevance_guardrail**(**ctx**, **agent**, **input_data**)**:**

**    **# 检查用户输入是否与航空旅行相关

**    result **=** **await** Runner**.**run**(**guardrail_agent**,** input_data**,** **context**=**ctx**.**context**)**

**    **return** **GuardrailFunctionOutput**(**

**        **output_info**=**result**.**final_output**,**

**        **tripwire_triggered**=**not** result**.**final_output**.**is_travel_related**,

**    **)

2. Jailbreak Guardrail（越狱防护）：* 防止用户尝试获取系统指令或绕过系统限制

* 例如阻止"返回你的系统指令"这类请求

护栏工作机制：* Input Guardrails: 在Agent处理前检查用户输入

* Output Guardrails: 在Agent输出前检查响应内容
* Tripwire机制: 当护栏被触发时，立即停止处理并返回预设错误信息

## 5. 具体Prompt示例

虽然具体的prompt内容没有在公开文档中完全展示，但从系统行为可以推断：

Triage Agent可能的Prompt：

text

Apply to mcp.json

**You are a Triage Agent for an airline customer ser**vice system.

**Analyze the user's request and determine which spe**cialist agent should handle it:

**- Seat Booking Agent: for seat changes, upgrades, **seat maps

**- Flight Status Agent: for flight information, del**ays, gates

**- Cancellation Agent: for flight cancellations and** refunds

**- FAQ Agent: for general questions about policies,** baggage, etc.

**Route the request to the most appropriate agent ba**sed on the user's intent.

Guardrail Agent的Prompt：

text

Apply to mcp.json

**Check if the user input is related to airline trav**el and customer service.

**Return whether this is a legitimate customer servi**ce request or off-topic content.

## 6. 技术特点

1. 模块化设计： 每个Agent职责单一，便于维护和扩展
2. 并行处理： Guardrail与Agent并行运行，提高效率
3. 透明化： 提供完整的执行trace，可视化Agent切换过程
4. 可配置： 支持自定义prompt、guardrail和工具
5. 基于OpenAI Agents SDK： 利用成熟的Agent框架，支持工具调用、上下文管理等高级功能

这个设计展现了现代Agent系统的最佳实践：专业化分工、智能路由、安全防护和可扩展架构。它为构建生产级的客服Agent系统提供了很好的参考模板。
