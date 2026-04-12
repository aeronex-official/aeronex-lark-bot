# AERONEX 库存查询助手 / Inventory Query Assistant

## 简介 / Introduction

**中文**：AERONEX 库存查询助手是一款 Lark 智能机器人，支持通过私聊或群组 @ 的方式，快速查询迪拜和沙特两个仓库的实时库存数量，并支持一键导出完整库存报表（CSV 格式）。

**English**: AERONEX Inventory Query Assistant is a Lark bot that allows you to instantly check real-time stock availability across Dubai and Saudi Arabia warehouses, via private chat or group mention. It also supports one-click export of the full inventory report in CSV format.

---

## 使用方式 / How to Use

### 私聊 / Private Chat

直接向机器人发送消息即可：

| 操作 | 示例 |
|------|------|
| 按型号搜索 | `Matrice 400` |
| 按EAN码查询 | `6937224120570` |
| 选择编号查看详情 | `3` |
| 导出完整库存报表 | `导出` 或 `export` |

**English**:

| Action | Example |
|--------|---------|
| Search by model | `Matrice 400` |
| Search by EAN code | `6937224120570` |
| Select number for details | `3` |
| Export full inventory report | `导出` or `export` |

---

### 群组 / Group Chat

在群组中需要 **@ 机器人** 后输入关键词：

```
@AERONEX Inventory Sync Matrice 400
@AERONEX Inventory Sync 6937224120570
```

---

## 查询流程 / Query Flow

### 型号搜索 / Model Search

**步骤 1**：发送型号关键词

```
Matrice 4T
```

**机器人回复**：

```
🔍 「Matrice 4T」找到 6 个相关产品

📋 请输入编号查看库存详情：
1. DJI Matrice 4TD（DJI RC Plus 2 Enterprise Overseas Edition）
2. DJI Matrice 4T (Demo Unit)
3. DJI Matrice 4T (Universal Edition)
4. DJI Matrice 4TD (Demo Unit)
5. DJI Matrice 4TD (Overseas Edition)
6. DJI Matrice 4T (EU)

💡 输入数字 1-6 查看详情（有效期 5 分钟）
```

**步骤 2**：输入编号

```
3
```

**机器人回复**：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 DJI Matrice 4T (Universal Edition)
EAN: 6941565994172
🇦🇪 Dubai: ✅ 259 件
🇸🇦 Saudi: ✅ 8 件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 导出库存报表 / Export Inventory Report

发送以下任意关键词即可触发导出：

| 中文触发词 | 英文触发词 |
|-----------|----------|
| `导出` | `export` |
| `导出库存` | `export inventory` |
| `导出清单` | `export list` |
| `导出报表` | `export report` |

**机器人回复流程**：

```
⏳ 正在生成库存报表，请稍候...
```

稍后收到：

```
✅ 库存报表已生成
📦 共 182 个 SKU
🗓 数据时间：2026-04-12 04:23 UTC
```

随后自动发送 **📎 CSV 文件**，点击即可下载，用 Excel 直接打开（中文不乱码）。

**文件内容说明**：

| 列名 | 说明 |
|------|------|
| EAN | 产品条码 |
| 产品型号/Model | 产品名称 |
| 迪拜库存/Dubai | 迪拜仓可用数量 |
| 沙特库存/Saudi | 沙特仓可用数量 |
| 合计/Total | 两仓合计数量 |
| 同步时间/Sync Time | 数据同步时间（UTC） |

> ⚠️ 导出功能仅支持**私聊**触发，群组暂不支持。

---

### EAN 码查询 / EAN Code Search

直接发送 EAN 码，机器人立即返回该产品库存：

```
6941565994172
```

**机器人回复**：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 DJI Matrice 4T (Universal Edition)
EAN: 6941565994172
🇦🇪 Dubai: ✅ 259 件
🇸🇦 Saudi: ✅ 8 件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 库存状态说明 / Stock Status

| 显示 | 含义 |
|------|------|
| ✅ 259 件 | 有库存，数字为可用数量 |
| ❌ 无库存 | 库存为 0 |
| ⚠️ -5 件 | 库存为负数（超卖或数据异常） |
| — | 该仓库无此产品记录 |

**English**:

| Display | Meaning |
|---------|---------|
| ✅ 259 件 | In stock, number shows available quantity |
| ❌ 无库存 | Out of stock (qty = 0) |
| ⚠️ -5 件 | Negative stock (oversold or data issue) |
| — | No record for this warehouse |

---

## 数据更新频率 / Data Sync Schedule

库存数据每 **30 分钟**自动从 Lark 表格同步一次（全天候运行）。

Data is automatically synced from Lark Sheets every **30 minutes** (runs 24/7).

如需立即更新，请联系管理员手动触发同步。

For immediate updates, please contact the admin to trigger a manual sync.

---

## 仓库覆盖 / Warehouses Covered

| 仓库 | 说明 |
|------|------|
| 🇦🇪 Dubai | 迪拜仓库 |
| 🇸🇦 Saudi | 沙特仓库 |

---

## 常见问题 / FAQ

**Q: 搜索没有结果怎么办？**  
A: 请尝试缩短关键词，如输入 `Matrice` 而非 `DJI Matrice 400 General`。

**Q: What if no results are found?**  
A: Try shorter keywords, e.g., `Matrice` instead of `DJI Matrice 400 General`.

---

**Q: 数据和实际库存不符怎么办？**  
A: 库存数据每30分钟同步一次，如有差异请以 Lark 表格为准，或联系管理员手动触发同步。

**Q: Data doesn't match actual inventory?**  
A: Data syncs every 30 minutes. If discrepancies exist, refer to the Lark Sheet or ask admin to trigger a manual sync.

---

**Q: 编号选择后显示「查询已过期」？**  
A: 查询会话有效期为 **5 分钟**，超时后需重新搜索关键词，再输入编号选择。

**Q: Seeing "session expired" after entering a number?**  
A: The query session is valid for **5 minutes**. Please search again and then select a number.

---

**Q: 发送「导出」后没有收到文件？**  
A: 请等待约 5-10 秒，文件较大时生成需要一点时间。如果收到错误提示，请联系 IT 管理员检查权限配置。

**Q: No file received after sending "export"?**  
A: Please wait 5–10 seconds as generation may take a moment. If you receive an error message, contact the IT admin to check permissions.

---

## 技术支持 / Support

如遇问题请联系 IT 管理员或在 AERONEX 库存查询群反馈。

For technical issues, please contact the IT admin or post in the AERONEX Inventory Query group.
