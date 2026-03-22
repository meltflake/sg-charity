# SG Charity — 新加坡公益全景项目

## 项目目标
梳理新加坡所有公益组织和慈善机构，做一个有差异化的公开网站。

## 数据源
| 来源 | URL | 说明 | 状态 |
|------|-----|------|------|
| Charity Portal (COC) | charities.gov.sg | 官方注册数据，3,173 家全量 | 已爬取 2026-03-10 |
| Charity Portal 详情页 | charities.gov.sg/Pages/SearchOrgProfile.aspx | 机构描述、财务、联系方式 | 待爬取 |
| giving.sg | giving.sg/organisations | 捐款平台，有机构描述和项目 | 待调研 |
| COC 年度报告 | mccy.gov.sg | 整体统计、趋势数据 | 待下载 |
| data.gov.sg | data.gov.sg | 开放数据集 | 待查 |
| NCSS | ncss.gov.sg | 社会服务机构目录 | 待调研 |

## 同类产品
| 产品 | URL | 定位 | 优劣 |
|------|-----|------|------|
| Charity Portal | charities.gov.sg | 官方注册查询 | 数据全但体验差，不能"逛"，无分析 |
| giving.sg | giving.sg | 捐款+志愿者 | 偏交易，不做全景梳理 |
| ngobase.org | ngobase.org/c/SG | 第三方 NGO 列表 | 信息粗糙，覆盖不全 |
| Caritas SG Finder | caritas-singapore.org | 天主教体系服务查找 | 仅覆盖 Caritas 成员 |
| Charity Navigator (US) | charitynavigator.org | 美国慈善评级 | 新加坡没有对标产品 |
| GuideStar (US) | guidestar.org | 美国非营利透明度 | 新加坡没有对标产品 |

## 差异化方向
- 不做捐款交易（giving.sg 已做），做信息发现和洞察
- 数据可视化 + 趋势分析（Charity Navigator/GuideStar 在新加坡的空白）
- 中英双语
- AI 辅助搜索（"我关心老年人心理健康"）

## 数据文件
- `data/charities_full.json` — 全量 3,173 家（2.5MB）
- `data/charities_full.csv` — CSV 版（601KB）
- `data/charities_stats.json` — 统计汇总
- `data/analysis_highlights.md` — 数据亮点分析
- Dropbox 副本: `dropbox:projects/sg-charity/data/`

## 基础数据概览（2026-03-10）
- 总计: 3,173 家
- 活跃 IPC: 707 家
- 最大领域: 宗教 38.9%
- 六个监管部门: MCCY, MSF, MOE, MOH, PA, SportSG

## 技术方案（初步）
- 静态站: Next.js/Astro + Cloudflare Pages
- 数据更新: cron 定期爬取
- 搜索: 客户端全文搜索 or Algolia
