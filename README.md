# 电影票房数据分析工具

## 项目概述

`movie_income.py` 是一个用于获取中国大陆热门电影票房数据、进行简单分析并生成可视化报告的Python脚本。该工具支持从在线API获取最新数据或读取本地CSV文件，将处理后的数据导出为多种格式（CSV/JSON/XLSX），并自动生成多种数据可视化图表。


## 功能特点

- **数据获取**：支持从在线API获取热门电影数据（默认获取Top 50），也可读取本地CSV文件
- **数据处理**：自动解析上映日期、提取年份、排序等预处理操作
- **数据导出**：将处理后的数据导出为CSV、JSON、XLSX格式（XLSX包含原始数据和年度汇总两个工作表）
- **数据可视化**：生成5种不同类型的图表，直观展示电影票房相关指标
- **结果管理**：自动创建以 `movie_income_{时间戳}` 命名的文件夹，统一存储所有输出文件


## 安装依赖

使用前需安装以下Python库：

```bash
pip install requests pandas matplotlib openpyxl
```

- `requests`：用于发送HTTP请求获取在线数据
- `pandas`：用于数据处理和导出
- `matplotlib`：用于生成数据可视化图表
- `openpyxl`：用于支持XLSX文件导出


## 使用方法

### 1. 在线获取数据（默认方式）

直接运行脚本即可从API获取最新电影数据：

```bash
python movie_income.py
```

### 2. 读取本地CSV文件

如果需要使用本地CSV文件（例如网络受限或需要分析历史数据），可指定文件路径：

```bash
python movie_income.py --local your_file.csv
```

> 本地CSV文件需包含以下字段（中英文均可，脚本会自动映射）：
> - 排名/Rank
> - 电影名称/MovieName
> - 上映时间/ReleaseDate
> - 总票房(万)/TotalBoxOffice(10k RMB)
> - 平均票价/AvgTicketPrice(RMB)
> - 平均场次/AvgAudienceCount


## 输出文件说明

运行脚本后，会自动创建一个命名格式为 `movie_income_YYYYMMDD_HHMMSS` 的文件夹，包含以下内容：

### 数据文件
- `movie_income_YYYYMMDD_HHMMSS.csv`：CSV格式数据
- `movie_income_YYYYMMDD_HHMMSS.json`：JSON格式数据
- `movie_income_YYYYMMDD_HHMMSS.xlsx`：Excel文件（含"Data"和"YearlySummary"两个工作表）

### 可视化图表
- `movie_income_YYYYMMDD_HHMMSS_line_release_vs_boxoffice.png`：上映日期与票房关系折线图
- `movie_income_YYYYMMDD_HHMMSS_pie_share_by_year.png`：年度票房占比饼图
- `movie_income_YYYYMMDD_HHMMSS_bar_top10_avg_ticket_price.png`：平均票价Top 10柱状图
- `movie_income_YYYYMMDD_HHMMSS_bar_top10_avg_audience.png`：平均场次观众数Top 10柱状图
- `movie_income_YYYYMMDD_HHMMSS_scatter_price_vs_boxoffice.png`：票价与票房关系散点图


## 注意事项

1. 在线API可能存在访问限制，若无法获取数据，建议使用本地CSV文件
2. 脚本已设置中文字体支持，确保电影名称等中文内容正常显示
3. Excel文件导出依赖 `openpyxl` 库，若缺失会导致导出失败
4. 图表中的电影名称标注可能因数据量较大出现重叠，可在代码中调整 `xytext` 参数优化显示


## 扩展方向

- 增加更多数据筛选条件（如按年份、类型筛选）
- 支持更多可视化图表类型（如票房增长率、地区分布等）
- 增加数据清洗功能，处理异常值和缺失值
- 实现定时任务，自动获取并更新数据
