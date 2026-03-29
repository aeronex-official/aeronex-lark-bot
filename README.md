# AERONEX 库存查询助手 / Inventory Query Assistant

## 简介 / Introduction

**中文**：AERONEX 库存查询助手是一款 Lark 智能机器人，支持通过私聊或群组 @ 的方式，快速查询迪拜和沙特两个仓库的实时库存数量。

**English**: AERONEX Inventory Query Assistant is a Lark bot that allows you to instantly check real-time stock availability across Dubai and Saudi Arabia warehouses, via private chat or group mention.

---

## 使用方式 / How to Use

### 私聊 / Private Chat

直接向机器人发送消息即可：

| 操作 | 示例 |
|------|------|
| 按型号搜索 | `Matrice 400` |
| 按EAN码查询 | `6937224120570` |
| 选择编号查看详情 | `3` |

**English**:

| Action | Example |
|--------|---------|
| Search by model | `Matrice 400` |
| Search by EAN code | `6937224120570` |
| Select number for details | `3` |

---

### 群组 / Group Chat

在群组中需要 **@ 机器人** 后输入关键词：

Copy
@AERONEX Inventory Sync Matrice 400 @AERONEX Inventory Sync 6937224120570


---

## 查询流程 / Query Flow

### 型号搜索 / Model Search

**步骤 1**：发送型号关键词

Matrice 4T


**机器人回复**：

🔍 「Matrice 4T」找到 6 个相关产品

📋 请输入编号查看库存详情：

DJI Matrice 4TD（DJI RC Plus 2 Enterprise Overseas Edition）
DJI Matrice 4T (Demo Unit)
DJI Matrice 4T (Universal Edition)
DJI Matrice 4TD (Demo Unit)
DJI Matrice 4TD (Overseas Edition)
DJI Matrice 4T (EU)
💡 输入数字 1-6 查看详情


**步骤 2**：输入编号

3


**机器人回复**：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📦 DJI Matrice 4T (Universal Edition) EAN: 6941565994172 🇦🇪 Dubai: ✅ 259 件 🇸🇦 Saudi: ✅ 8 件 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━


---

### EAN 码查询 / EAN Code Search

直接发送 EAN 码，机器人立即返回该产品库存：

6941565994172


**机器人回复**：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 📦 DJI Matrice 4T (Universal Edition) EAN: 6941565994172 🇦🇪 Dubai: ✅ 259 件 🇸🇦 Saudi: ✅ 8 件 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━


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

库存数据每 **2 小时**自动从 Lark 表格同步一次（全天候运行）。

Data is automatically synced from Lark Sheets every **2 hours** (runs 24/7).

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
A: 库存数据每2小时同步一次，如有差异请以 Lark 表格为准，或联系管理员手动触发同步。

**Q: Data doesn't match actual inventory?**
A: Data syncs once every 2 hours. If discrepancies exist, refer to the Lark Sheet or ask admin to trigger a manual sync.

---

**Q: 编号选择后没有反应？**
A: 查询会话有效期为当次会话，重新搜索关键词后再选择编号即可。

**Q: No response after entering a number?**
A: The session expires after each query. Search again and then select a number.

---

## 技术支持 / Support

如遇问题请联系 IT 管理员或在 AERONEX 库存查询群反馈。

For technical issues, please contact the IT admin or post in the AERONEX Inventory Query group.
