# -*- coding: utf-8 -*-
"""
movie_income_cn.py
- 获取热门电影数据并导出CSV/JSON/XLSX文件，文件名为movie_income_{时间戳}.*
- 将多个图表(PNG)保存到当前目录的指定文件夹中
- 折线图上为每个点标注电影名称
- 使用纯matplotlib绘制；每个图表单独一个图形；不指定颜色
"""

import os
import json
import csv
from datetime import datetime
import warnings
import requests
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# 确保中文电影名称能正确显示（数据标签）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

API_URL = "https://ys.endata.cn/enlib-api/api/home/getrank_mainland.do"
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/105.0.0.0 Safari/537.36'),
    'Accept': 'application/json, text/plain, */*'
}
PAYLOAD = {'r': '0.9936776079863086', 'top': '50', 'type': '0'}

def fetch_online() -> pd.DataFrame:
    """从API获取数据并返回标准化的DataFrame"""
    resp = requests.post(API_URL, headers=HEADERS, data=PAYLOAD, timeout=20)
    resp.raise_for_status()
    table = (resp.json() or {}).get('data', {}).get('table0', []) or []

    def to_row(item):
        return {
            "排名": item.get("Irank"),
            "电影名称": item.get("MovieName"),
            "上映时间": item.get("ReleaseTime"),
            "总票房(万元)": float(item.get("BoxOffice", 0) or 0),
            "平均票价(元)": float(item.get("AvgBoxOffice", 0) or 0),
            "平均场次观众数": float(item.get("AvgAudienceCount", 0) or 0),
        }

    df = pd.DataFrame([to_row(x) for x in table])
    if df.empty:
        raise ValueError("API返回空数据集")
    return df

def read_local(csv_path: str) -> pd.DataFrame:
    """读取本地CSV文件（如果已存在），需包含预期的表头"""
    df = pd.read_csv(csv_path)
    # 如果本地文件使用英文表头，在此处映射
    mapper = {
        "Rank": "排名",
        "MovieName": "电影名称",
        "ReleaseDate": "上映时间",
        "TotalBoxOffice(10k RMB)": "总票房(万元)",
        "AvgTicketPrice(RMB)": "平均票价(元)",
        "AvgAudienceCount": "平均场次观众数",
    }
    for en, cn in mapper.items():
        if en in df.columns and cn not in df.columns:
            df[cn] = df[en]
    expected = ["排名", "电影名称", "上映时间", "总票房(万元)", "平均票价(元)", "平均场次观众数"]
    return df[expected]

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """排序、解析日期、添加年份列"""
    df = df.copy()
    # 解析上映日期
    def _parse_date(s):
        try:
            return pd.to_datetime(s)
        except Exception:
            return pd.NaT
    df["上映日期解析"] = df["上映时间"].apply(_parse_date)
    df["年份"] = pd.to_datetime(df["上映日期解析"]).dt.year
    df.sort_values(["上映日期解析", "排名"], inplace=True, ignore_index=True)
    return df

def export_all(df: pd.DataFrame, folder: str, ts: str) -> dict:
    """导出CSV/JSON/XLSX并返回文件路径"""
    base = f"movie_income_{ts}"
    csv_path = os.path.join(folder, f"{base}.csv")
    json_path = os.path.join(folder, f"{base}.json")
    xlsx_path = os.path.join(folder, f"{base}.xlsx")

    # CSV / JSON
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)

    # XLSX（包含年度汇总的第二个工作表）
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="数据", index=False)
        yearly = (df.dropna(subset=["年份"])
                    .groupby("年份")["总票房(万元)"]
                    .sum().reset_index())
        yearly.to_excel(writer, sheet_name="年度汇总", index=False)

    return {"csv": csv_path, "json": json_path, "xlsx": xlsx_path}

# --------- 图表（每个图表单独一个图形；不指定颜色） ----------
def chart_line_release_vs_boxoffice(df: pd.DataFrame, folder: str, ts: str) -> str:
    path = os.path.join(folder, f"movie_income_{ts}_上映日期 vs 票房.png")
    fig = plt.figure(figsize=(10, 6))
    x = df["上映日期解析"]
    y = df["总票房(万元)"]
    plt.plot(x, y, marker="o")
    plt.title("总票房随上映日期变化")
    plt.xlabel("上映日期")
    plt.ylabel("总票房（万元）")
    # 为每个点标注电影名称
    for xi, yi, name in zip(x, y, df["电影名称"]):
        if pd.notna(xi) and pd.notna(yi):
            plt.annotate(str(name), (xi, yi), textcoords="offset points", xytext=(5, 5))
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path

def chart_pie_share_by_year(df: pd.DataFrame, folder: str, ts: str) -> str:
    path = os.path.join(folder, f"movie_income_{ts}_年度票房占比.png")
    fig = plt.figure(figsize=(7, 7))
    share = (df.dropna(subset=["年份"])
               .groupby("年份")["总票房(万元)"]
               .sum().sort_index())
    plt.pie(share.values.tolist(),
            labels=[str(int(x)) for x in share.index.tolist()],
            autopct="%1.2f%%")
    plt.title("各年度总票房占比")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path

def chart_bar_top10_by_price(df: pd.DataFrame, folder: str, ts: str) -> str:
    path = os.path.join(folder, f"movie_income_{ts}_top10平均票价.png")
    fig = plt.figure(figsize=(10, 6))
    top_price = df.nlargest(10, "平均票价(元)")[["电影名称", "平均票价(元)"]]
    plt.bar(top_price["电影名称"], top_price["平均票价(元)"])
    plt.title("平均票价前十的电影（元）")
    plt.xlabel("电影")
    plt.ylabel("平均票价（元）")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path

def chart_bar_top10_by_audience(df: pd.DataFrame, folder: str, ts: str) -> str:
    path = os.path.join(folder, f"movie_income_{ts}_top10平均场次观众数.png")
    fig = plt.figure(figsize=(10, 6))
    top_aud = df.nlargest(10, "平均场次观众数")[["电影名称", "平均场次观众数"]]
    plt.bar(top_aud["电影名称"], top_aud["平均场次观众数"])
    plt.title("平均场次观众数前十的电影")
    plt.xlabel("电影")
    plt.ylabel("平均场次观众数")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path

def chart_scatter_price_vs_boxoffice(df: pd.DataFrame, folder: str, ts: str) -> str:
    path = os.path.join(folder, f"movie_income_{ts}_票价 vs 票房.png")
    fig = plt.figure(figsize=(10, 6))
    plt.scatter(df["平均票价(元)"], df["总票房(万元)"])
    plt.title("平均票价与总票房关系")
    plt.xlabel("平均票价（元）")
    plt.ylabel("总票房（万元）")
    # 标注一些值得注意的点
    top_box = df.nlargest(5, "总票房(万元)")
    top_price = df.nlargest(5, "平均票价(元)")
    notable = pd.concat([top_box, top_price]).drop_duplicates(subset=["电影名称"])
    for _, r in notable.iterrows():
        plt.annotate(str(r["电影名称"]),
                     (r["平均票价(元)"], r["总票房(万元)"]),
                     textcoords="offset points", xytext=(5, 5))
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path

def main(local_csv: str | None = None):
    # 1) 加载数据
    try:
        if local_csv and os.path.exists(local_csv):
            df = read_local(local_csv)
        else:
            df = fetch_online()
    except Exception as e:
        print(f"[错误] 无法获取数据: {e}")
        print("提示: 如果网络受限，可以传入本地CSV路径调用main('你的文件.csv')。")
        return

    # 2) 数据预处理
    df = preprocess(df)

    # 3) 创建输出文件夹
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"movie_income_{ts}"
    os.makedirs(folder, exist_ok=True)

    # 4) 导出带时间戳的文件
    out = export_all(df, folder, ts)

    # 5) 生成图表
    charts = [
        chart_line_release_vs_boxoffice(df, folder, ts),
        chart_pie_share_by_year(df, folder, ts),
        chart_bar_top10_by_price(df, folder, ts),
        chart_bar_top10_by_audience(df, folder, ts),
        chart_scatter_price_vs_boxoffice(df, folder, ts),
    ]

    print("✅ 导出文件:")
    for k, v in out.items():
        print(f" - {k.upper()}: {v}")
    print("✅ 保存图表:")
    for p in charts:
        print(f" - {p}")

if __name__ == "__main__":
    # 如果已有本地CSV文件（例如之前运行的结果），
    # 可以调用main('已有的文件.csv')来跳过网络获取步骤。
    main()