# PRD: SG Charity Map — 新加坡公益全景

> Version: 0.1 | Author: Luca & Nix | Date: 2026-03-10

## 1. Problem Statement

新加坡有 2,635 家活跃慈善机构，但没有一个地方能让人快速了解"新加坡公益长什么样"。

现有信息散落在三个地方：政府注册系统（charities.gov.sg，能查但不能逛）、捐款平台（giving.sg，只关心交易）、各机构自己的官网。想做公益的人——无论是捐款人、志愿者、企业 CSR 负责人还是研究者——都面临同样的问题：信息碎片化，没有全景视角，无法对比和发现。

美国有 Charity Navigator 和 GuideStar 做这件事。新加坡是空白。

## 2. Goals

- 成为新加坡公益领域的信息基础设施——想了解新加坡公益，第一个想到的就是这个站
- 让任何人在 30 秒内找到与自己关注领域匹配的慈善机构
- 用数据讲故事：让公益生态的结构性特征可视化（领域分布、资金流向、增长趋势）
- 提供官方数据没有的增值信息（机构对比、IPC 追踪、趋势分析）

## 3. Non-Goals

- 不做捐款交易（giving.sg 的事，不跟政府平台竞争）
- 不做志愿者招募（同上）
- 不做机构评级/排名（初期没有足够数据支撑，贸然打分会引发争议）
- 不做用户注册/登录（v1 纯公开信息站，零门槛）
- 不覆盖非注册组织（只收录 COC 注册的正式慈善机构，保证数据可靠性）

## 4. Target Users

**Primary: 有意向的捐款人**
"我想捐款做公益，但不知道新加坡有哪些机构，也不知道该捐给谁。"
关心：领域匹配、IPC 资格（能否抵税）、机构规模和可靠性。

**Primary: 企业 CSR 负责人**
"老板说今年要做 CSR，让我找几个合作机构。"
关心：领域匹配、机构规模、是否有 IPC、是否接受企业合作。

**Secondary: 公益从业者**
"想了解同行在做什么，有没有合作机会。"
关心：同领域机构列表、活动类型、组织形式。

**Secondary: 研究者/媒体**
"要写一篇关于新加坡公益的报道/论文。"
关心：数据下载、趋势分析、统计图表。

## 5. User Stories

**发现**
- As a 捐款人, I want to 按领域浏览慈善机构（养老、教育、医疗等）so that I can 找到与我关注方向匹配的机构
- As a 捐款人, I want to 只看有 IPC 资格的机构 so that I can 确保捐款可以抵税
- As a CSR 负责人, I want to 按机构规模和领域筛选 so that I can 找到与公司规模和价值观匹配的合作伙伴

**了解**
- As a 捐款人, I want to 看到一家机构的基本信息（做什么、成立多久、IPC 状态）so that I can 判断是否值得深入了解
- As a 研究者, I want to 看到新加坡公益的全景数据可视化 so that I can 快速把握整体生态
- As a 公益从业者, I want to 看到同领域的其他机构 so that I can 发现合作机会或了解竞争格局

**追踪**
- As a 捐款人, I want to 知道哪些机构的 IPC 即将到期 so that I can 提前规划捐款时间
- As a 媒体人, I want to 看到最近新注册的机构 so that I can 发现值得报道的新趋势

**使用数据**
- As a 研究者, I want to 下载结构化数据（CSV/JSON）so that I can 在自己的工具中做分析

## 6. Requirements

### Must-Have (P0) — MVP

**6.1 机构目录**
- 收录全部 2,635 家活跃慈善机构
- 每家机构展示：名称、UEN、领域、分类、IPC 状态（含有效期）、活动类型、注册日期、监管部门、组织形式
- 按字母顺序默认排列

Acceptance Criteria:
- [ ] 页面加载后 2 秒内展示机构列表
- [ ] 数据与 charities.gov.sg 一致（定期同步）
- [ ] 已注销机构不出现在默认列表中（可选择显示）

**6.2 搜索与筛选**
- 全文搜索（机构名称）
- 筛选器：领域（8 类）、IPC 状态（有/无/即将到期）、活动类型（7 类）、组织形式（Society/CLG/Others）
- 筛选器可组合使用
- URL 参数化（筛选状态可分享）

Acceptance Criteria:
- [ ] 搜索响应 < 200ms（客户端搜索）
- [ ] 每个筛选条件显示匹配数量
- [ ] 筛选结果 URL 可收藏和分享

**6.3 机构详情页**
- 展示该机构所有可用字段
- 显示同领域同分类的相关机构（"类似机构"）
- 如有官网链接，提供跳转

Acceptance Criteria:
- [ ] 每家机构有独立 URL（SEO 友好）
- [ ] 相关机构推荐至少显示 5 家

**6.4 全景数据面板（Dashboard）**
- 领域分布饼图/树图
- IPC 分布（有/无，按领域）
- 注册时间线（按年）
- 监管部门分布
- 关键数字卡片：总数、活跃数、IPC 数、注销率

Acceptance Criteria:
- [ ] 图表可交互（hover 显示详细数字）
- [ ] 移动端可用

**6.5 中英双语**
- 界面元素中英双语
- 机构名称保留原始语言（绝大多数为英文）

### Nice-to-Have (P1) — Fast Follow

**6.6 IPC 到期追踪**
- 专题页：即将到期的 IPC 机构列表（按到期日排序）
- 标记已过期但未续期的机构

**6.7 新机构追踪**
- "最近注册"页面，按时间倒序
- 每月/每季度新注册趋势

**6.8 领域专题页**
- 养老（Eldercare）、儿童/青少年、健康等领域的深度页面
- 包含领域概述、机构列表、关键数据

**6.9 数据下载**
- 提供 CSV/JSON 格式下载
- 包含筛选功能（只下载选中的子集）

**6.10 注销档案**
- 537 家已注销机构的列表
- 按领域和时间分析注销趋势

### Future Considerations (P2)

**6.11 财务透明度**
- 接入年报数据：年度收入/支出、行政开支比
- 机构间财务对比

**6.12 地理分布图**
- 机构地址 geocoding，在地图上展示
- 按区域筛选

**6.13 AI 搜索**
- 自然语言查询："我关心老年人心理健康，新加坡有哪些机构？"
- 基于机构描述和分类的语义匹配

**6.14 趋势报告**
- 季度/年度公益生态报告（自动生成）
- 领域增长/萎缩趋势、资金流向变化

## 7. Data Architecture

### 数据源

| 来源 | 内容 | 更新频率 | 状态 |
|------|------|----------|------|
| charities.gov.sg Export API | 全量机构基础信息 | 月度 | 已接入 ✅ |
| charities.gov.sg 详情页 | 机构描述、联系方式 | 月度 | 待接入 |
| COC Annual Report | 整体统计、财务汇总 | 年度 | 待获取 |
| giving.sg | 机构描述、项目信息 | 季度 | 待调研 |
| NCSS | 社会服务机构详情 | 季度 | 待调研 |

### 数据字段（已有）

每家机构包含：
- CharityIPCName（机构名称）
- UENNo（统一企业编号）
- CharityStatus（注册状态: Registered / Registered with IPC / Deregistered / Exempt）
- IPCStatus（IPC 状态: Live / null）
- IPCValidFrom / IPCValidTill（IPC 有效期）
- PrimarySector（领域: Religious / Social and Welfare / Health / Education / Arts and Heritage / Community / Sports / Others）
- PrimaryClassification（细分类: Christianity / Eldercare / Children/Youth 等 80+ 类）
- Activities（活动类型: Direct Services / Training / Grantmaking 等 7 类）
- SectorAdministrato（监管部门）
- CharitySetup（组织形式: Society / CLG / Others）
- RegistrationDate（注册日期）
- DeRegistrationDate（注销日期，如适用）

### 数据质量

- 覆盖率: 100%（全量注册机构）
- 完整度: 72.5%（27.5% 缺少活动类型）
- 时效性: 实时同步自官方注册系统
- 局限: 无财务数据、无地址、无机构描述

## 8. Technical Approach

- 静态站生成: Astro 或 Next.js (SSG)
- 部署: Cloudflare Pages（零成本，全球 CDN）
- 搜索: 客户端 Fuse.js 或 FlexSearch（数据量小，不需要后端）
- 数据可视化: D3.js 或 Chart.js
- 数据更新: GitHub Actions cron，月度爬取 + 自动构建
- 域名: 待定（建议 sgcharity.org 或 charitymap.sg）

成本预估: 域名 ~$12/年，其余均为零成本。

## 9. Success Metrics

### Leading (上线 1 个月)
- 收录率: 覆盖 100% 活跃注册慈善机构
- 搜索体验: 用户能在 3 步内找到目标机构
- 页面性能: Lighthouse Performance > 90
- 搜索引擎: Google 收录 > 1,000 页

### Lagging (上线 3-6 个月)
- 月访问量: > 1,000 UV
- 数据引用: 被媒体或研究报告引用 > 3 次
- 搜索排名: "Singapore charity directory" 排 Google 首页
- 用户留存: 月度回访率 > 15%

## 10. Open Questions

| 问题 | 负责人 | 是否 blocking |
|------|--------|--------------|
| 域名选什么？sgcharity.org / charitymap.sg / 其他 | Luca | 否（先用 GitHub Pages） |
| 是否需要展示已注销机构？ | Luca | 否（默认隐藏，可选显示） |
| 宗教类机构如何处理？全部展示还是单独分区？ | Luca | 否（先全部展示，按领域筛选） |
| 是否需要 Malay/Tamil 语言支持？ | Luca | 否（v1 中英即可） |
| 详情页的机构描述从哪里获取？ | Nix | 是（影响详情页内容丰富度） |
| 财务数据获取路径？ | Nix | 否（P2 功能） |

## 11. Timeline

| Phase | 内容 | 时间 |
|-------|------|------|
| Phase 0 (Done) | 数据爬取 + 分析 + PRD | 2026-03-10 |
| Phase 1 | MVP 站点（目录 + 搜索 + Dashboard）| 1-2 周 |
| Phase 2 | 详情页 + IPC 追踪 + 领域专题 | 2-3 周 |
| Phase 3 | 数据补全（描述、财务）+ AI 搜索 | 1-2 月 |

## Appendix: Competitive Landscape

| 产品 | 定位 | 我们的差异 |
|------|------|-----------|
| charities.gov.sg | 政府注册查询 | 我们做信息发现 + 数据洞察，不只是查询 |
| giving.sg | 捐款 + 志愿者 | 我们不做交易，做全景视角 + 数据分析 |
| Charity Navigator (US) | 慈善评级 | 新加坡空白，我们填补 |
| GuideStar (US) | 非营利透明度 | 同上，新加坡版 |
| ngobase.org | 第三方列表 | 我们数据完整度远超（官方源 vs 人工收集） |

## Appendix: Key Data Insights

详见 `data/analysis_highlights.md`。核心发现：

1. 宗教机构占 40% 但 IPC 率 0%
2. 养老仅 81 家（vs 203 家儿童/青少年），供给严重不足
3. 230 家 IPC 今年到期（占 1/3）
4. "Others"类注销率 37%，远高于其他领域
5. 727 家机构无活动类型数据（信息补全机会）
6. SHEIN、新航等企业基金会近期入局
