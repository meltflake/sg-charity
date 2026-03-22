# SG Charity Map — 新加坡公益全景

## 项目定位
新加坡版 Charity Navigator / GuideStar。做信息发现和数据洞察，不做捐款交易。填补新加坡公益透明度的空白。

## 数据架构

### 数据文件

**核心数据（charities.gov.sg）：**
| 文件 | 内容 | 数量 | 大小 |
|------|------|------|------|
| `data/charities_full.json` | 全量机构基础信息（含已注销） | 3,173 | 2.6MB |
| `data/charities_full.csv` | 同上 CSV 版 | 3,173 | 615KB |
| `data/charities_profiles.jsonl` | 活跃机构详情（地址/联系/描述/治理） | 2,635 | 8.6MB |
| `data/charities_financials.jsonl` | 公开财务数据（收支/资产负债） | 860 | 10MB |
| `data/charities_stats.json` | 预计算统计分布 | - | 6.6KB |

**补充数据源：**
| 文件 | 来源 | 内容 | 数量 |
|------|------|------|------|
| `data/ncss_social_service_agencies.geojson` | data.gov.sg NCSS | 社会服务机构目录（含GPS坐标） | 908 |
| `data/ncss_agencies.json` | 上述处理版 | 结构化+与charities匹配 | 908 |
| `data/givingsg_organisations.json` | giving.sg | 组织列表+描述+cause标签 | 1,707 |
| `data/givingsg_sitemap.json` | giving.sg sitemap | Profile URL+slug+lastmod | 1,723 |
| `data/charities_by_sector_annual.csv` | data.gov.sg COC | 各领域机构数 (2014-2024) | 8行 |
| `data/total_donations_by_sector.csv` | data.gov.sg COC | 各领域捐款总额 (2012-2020) | 64行 |
| `data/charities_by_income_size.csv` | data.gov.sg COC | 收入规模分布 (2009-2013) | 31行 |
| `data/government_funding.csv` | data.gov.sg COC | 政府拨款 (2013-2019) | 22行 |

### 核心字段

**基础列表** (`charities_full.json`)：
- `CharityIPCName`, `UENNo` — 名称和统一企业编号（主键）
- `CharityStatus`: Registered / Registered with IPC / Deregistered / Exempt
- `IPCStatus` / `IPCValidFrom` / `IPCValidTill` — IPC 免税资格及有效期
- `PrimarySector` (8类): Religious / Social and Welfare / Health / Education / Arts and Heritage / Community / Sports / Others
- `PrimaryClassification` 细分类 (80+): 数组
- `Activities` 活动类型 (7类): 数组
- `SectorAdministrato` 监管部门, `CharitySetup` 组织形式, `RegistrationDate`

**机构详情** (`charities_profiles.jsonl`)：
- `Address`(含邮编), `Email`, `OfficeNo`, `Website`
- `Objective` 机构目标, `VisionMission` 愿景使命
- `GoverningMembers`(数组), `KeyOfficers`(数组) — 平均9.6/3.7人
- `requiresLogin` — true=1,775家(财务需登录), false=860家(财务公开)
- 关联键: `_uen`

**财务数据** (`charities_financials.jsonl`)：
- `FinancialInfos` 近3年收支总览
- `FinancialInfoReceipts/Expenses/BalanceSheet/OtherInformation` — **均为 JSON 字符串，需 JSON.parse**
- 关联键: `_uen`
- **仅覆盖 860/2,635 家（33%）— 其余需登录，公开API无法获取**

**NCSS 机构** (`data/ncss_agencies.json`)：
- `name`, `address`, `postal_code`, `website`, `longitude`, `latitude`(全部908家有坐标)
- `matched_uen` — 458/908 与charities.gov.sg匹配成功
- 未匹配的450家多为服务中心分支（如NKF各透析中心）或非注册慈善的社会服务机构

**giving.sg 组织** (`data/givingsg_organisations.json`)：
- `name`, `description`, `causes`(标签数组), `image_url`, `tab`(charity/organisation/groundup)
- charity:696 / organisation:620 / groundup:391
- 241/696 charity 与 charities.gov.sg 名称匹配

### 数据关联键
- `UENNo` / `_uen` — charities_full ↔ profiles ↔ financials 主键
- 机构名称大写匹配 — NCSS/giving.sg ↔ charities 的匹配方式

### 数据源全景

| 来源 | 数据类型 | 覆盖 | 状态 |
|------|----------|------|------|
| charities.gov.sg | 注册+详情+财务 | 3,173 全量 | ✅ 已获取 |
| data.gov.sg NCSS | 社服机构+GPS坐标 | 908 | ✅ 已获取 |
| data.gov.sg COC | 行业统计CSV | 行业级汇总 | ✅ 已获取 |
| giving.sg | 描述+cause标签+图片 | 1,707 | ✅ 已获取 |
| data.gov.sg ACRA | 企业注册(筛CLG) | 210万待筛 | ⏳ 待处理 |
| Registry of Societies | 社团注册 | 全量社团 | ❌ 无批量接口 |
| GlobalGiving Atlas | 验证非营利状态 | 3,021 | ❌ 需付费 |

## 爬虫脚本

| 脚本 | 用途 | 方式 |
|------|------|------|
| `scrape_charities.py` | 列表+基础详情 | charities.gov.sg HTTP API |
| `scrape_all.py` | 全量列表+统计+CSV | charities.gov.sg Export API |
| `scrape_details.py` | 详情+财务(支持断点续爬) | charities.gov.sg SearchResultHandler |
| `scrape_givingsg.py` | giving.sg 组织列表 | Playwright headless browser |
| `analyze_highlights.py` | 数据分析生成亮点 | 本地 Python |

## 关键数据洞察
- 活跃 2,635 家，已注销 537 家（17%死亡率）
- 活跃 IPC 707 家（26.8%），宗教类 40% 占比但 IPC 率 0%
- 养老仅 81 家 vs 儿童青少年 203 家（老龄化社会供给缺口）
- 230 家 IPC 今年到期（占 1/3），对捐款人有实际价值
- 27.5% 机构缺活动类型数据
- "Others"类注销率 37%（定位模糊易消亡）

## 技术方向
- 静态站: Astro 或 Next.js (SSG) + Cloudflare Pages
- 搜索: 客户端 Fuse.js / FlexSearch
- 可视化: D3.js / Chart.js
- 数据更新: GitHub Actions cron 月度爬取
- 中英双语
- 爬虫依赖: Python 3, Playwright (giving.sg)

## 产品规划
- **P0 MVP**: 机构目录 + 搜索筛选 + 机构详情页 + 全景 Dashboard + 双语
- **P1**: IPC 到期追踪, 新机构追踪, 领域专题页, 数据下载
- **P2**: 财务透明度, 地理分布图, AI 语义搜索, 趋势报告

## 待完成
- [ ] giving.sg 与 charities.gov.sg 深度交叉匹配（目前仅241/696名称匹配）
- [ ] ACRA 数据下载筛选 CLG（发现未注册慈善的非营利组织）
- [ ] 财务数据 ETL（解析嵌套 JSON 字符串为结构化字段）
- [ ] 多源数据合并为统一机构档案 JSON
- [ ] 建站开发

## 相关文档
- `PRD.md` — 完整产品需求文档
- `README.md` — 项目概览和竞品分析
- `data/analysis_highlights.md` — 数据亮点和差异化方向
