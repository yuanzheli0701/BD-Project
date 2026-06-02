# Demo Script / 演示脚本
## City Mood x Weather - Big Data Project

### [0:00-0:30] Opening

EN: Hello, I present my Big Data project: City Mood x Weather Correlation Analysis.
The question: do people listen to sadder music when it rains?

ZH: 大家好，我展示我的大数据项目：城市情绪与天气相关性分析。问题是：下雨天人们会听更悲伤的音乐吗？

### [0:30-1:30] Architecture

EN: Complete Data Lake pipeline. Left side: two REST APIs ingest real data.
Four layers: raw JSON, formatted Parquet, combined CDI calculation, indexed to Elasticsearch, visualized in Kibana.

ZH: 完整 Data Lake 管道。左侧两个 REST API 拉取真实数据。四层：原始 JSON、格式化 Parquet、合并计算 CDI、索引到 Elasticsearch、Kibana 可视化。

### [1:30-2:30] Running Pipeline

EN: One command to run: python run_pipeline.py. Fetches weather and music for 10 cities,
formats, computes CDI, indexes to ES. About 30 seconds total.

ZH: 一条命令：python run_pipeline.py。拉取 10 个城市的天气和音乐数据，格式化，计算 CDI，索引到 ES。总共约 30 秒。

[ACTION: Run pipeline in terminal]

### [2:30-3:30] CDI Formula

EN: Core innovation: City Depression Index. CDI = (1 - valence) x (1 + rain_bonus + cloud_bonus + humidity_bonus).
Valence: 0 = sad, 1 = happy. Rain: +0.3, clouds: +0.2, humidity: +0.1.

ZH: 核心创新：City Depression Index。CDI = (1 - valence) x (1 + 雨天 + 云量 + 湿度加成)。
Valence：0=悲伤，1=快乐。下雨+0.3，云量+0.2，湿度+0.1。

### [3:30-5:00] Kibana Dashboard

EN: World map: each circle is a city. Bigger and redder = higher CDI.
Tokyo Paris red today (raining). New York green (sunny).
Bar chart ranks cities. Line chart shows 31-day trend. Metric cards show high/low.

ZH: 世界地图：每个圆圈代表城市。越大越红=CDI越高。
Tokyo Paris 今天红色（下雨）。New York 绿色（晴天）。
柱状图排名。折线图 31 天趋势。指标卡显示最高最低。

[ACTION: Show dashboard visualizations]

### [5:00-6:30] Data Lake Structure

EN: Clean naming convention: data/layer/source/YYYY-MM-DD/.
Raw=JSON from APIs. Formatted=normalized Parquet. Combined=joined + CDI.
Respects Data Lake V2 architecture.

ZH: 命名规范：data/layer/source/YYYY-MM-DD/。
Raw=API 返回的 JSON。Formatted=标准化 Parquet。Combined=合并+CDI。
遵循 Data Lake V2 架构。

### [6:30-8:00] Bonus Features

EN: Five bonus features. Spark PySpark formatting and combination.
S3 distributed storage with LocalStack and boto3. Airflow DAG orchestration.
Blog post. Innovative self-invented CDI metric.

ZH: 五项加分功能。Spark PySpark 格式化和合并。
S3 分布式存储（LocalStack + boto3）。Airflow DAG 编排。
博客文章。创新的自创 CDI 指标。

[ACTION: Show bonus code files]

### [8:00-9:00] Results

EN: 31 days, 10 cities, 320 records. Rainy cities show 2x higher CDI than sunny ones.
Weather does correlate with musical mood. Hypothesis confirmed.

ZH: 31 天，10 个城市，320 条记录。雨天城市 CDI 是晴天的 2 倍。
天气确实与音乐情绪相关。假设得到验证。

### [9:00-10:00] Q&A

EN: Thank you. Happy to answer questions about architecture, code, or methodology.

ZH: 谢谢。很乐意回答关于架构、代码、方法的任何问题。
