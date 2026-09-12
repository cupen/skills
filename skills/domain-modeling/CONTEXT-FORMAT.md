# CONTEXT.md 格式

## 结构

```md
# {Context 名}

{一两句话：这个 context 是什么、为何存在。}

## Language

**Order（订单）**:
{一两句话说明该术语}
_Avoid_: Purchase, transaction

**Invoice（发票）**:
交付后向客户发出的付款请求。
_Avoid_: Bill, payment request

**Customer（客户）**:
下单的个人或组织。
_Avoid_: Client, buyer, account
```

## 规则

- **要有立场。**同一概念存在多个说法时，选定最好的一个，其余列进 `_Avoid_`。
- **定义要紧。**最多一两句。定义它**是什么**，不是它做什么。
- **只收本 context 特有的术语。**通用编程概念（超时、错误类型、工具函数模式）哪怕项目用得再多也不收。加术语前先问：这是本 context 独有的概念，还是通用编程概念？只有前者属于这里。
- 术语自然聚簇时**用小标题分组**；全部术语同属一个内聚领域时，平铺一份即可。

## 单 context vs 多 context 仓库

**单 context（多数仓库）：** 根目录一份 `CONTEXT.md`。

**多 context：** 根目录一份 `CONTEXT-MAP.md`，列出各 context 的位置与相互关系：

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md): receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md): generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md): manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering 发出 `OrderPlaced` 事件；Fulfillment 消费它开始拣货
- **Fulfillment → Billing**: Fulfillment 发出 `ShipmentDispatched` 事件；Billing 消费它生成发票
- **Ordering ↔ Billing**: 共享 `CustomerId` 与 `Money` 类型
```

本技能自行推断适用哪种结构：

- 存在 `CONTEXT-MAP.md` → 读它找到各 context
- 只有根目录 `CONTEXT.md` → 单 context
- 两者皆无 → 第一个术语敲定时，惰性创建根目录 `CONTEXT.md`

多 context 时，推断当前话题属于哪个 context；判断不了就问。
