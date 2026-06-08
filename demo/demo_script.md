# Demo Script / 演示脚本
## City Mood x Weather - Big Data Project

### [0:00-0:20] Opening

EN: Hi, this is my Big Data project: City Mood x Weather Correlation Analysis.
The question I wanted to answer is simple: do people listen to sadder music when it rains?

ZH: 大家好，这是我的大数据项目：城市情绪与天气相关性分析。
我想回答的问题很简单：下雨天，人们会不会听更悲伤的音乐？

### [0:20-1:00] Architecture

EN: I built a Data Lake pipeline with two APIs. On one side, Last.fm gives me music charts from 10 countries.
On the other side, OpenWeatherMap gives me live weather for 10 cities.
Data goes through three layers: raw JSON, formatted Parquet, then combined with CDI calculation.
Finally everything is indexed into Elasticsearch and shown in Kibana.

ZH: 我搭建了一个 Data Lake 管道，接入两个 API。一边是 Last.fm 提供 10 个国家的音乐榜单，
另一边是 OpenWeatherMap 提供 10 个城市的实时天气。数据经过三层：原始 JSON、格式化 Parquet、
合并计算 CDI，最后索引到 Elasticsearch 并在 Kibana 中可视化。

### [1:00-1:40] Running Pipeline

EN: Here is the pipeline running. One command: python run_pipeline.py.
It fetches data, formats it, computes CDI, and indexes everything. Takes about 30 seconds.
I ran it for 39 days from 1 May to 8 June 2026, generating 390 records across 10 cities.

[ACTION: Show terminal running pipeline]

ZH: 这是管道运行的画面。一条命令：python run_pipeline.py。
它拉取数据、格式化、计算 CDI、索引到 ES，大约 30 秒。
我跑了 39 天，从 5 月 1 日到 6 月 8 日，生成了 390 条记录，覆盖 10 个城市。

[ACTION: 展示终端运行 pipeline]

### [1:40-2:20] CDI Formula

EN: The core of the project is the City Depression Index, the CDI, which I designed myself.
CDI equals one minus valence, multiplied by one plus rain bonus plus cloud bonus plus humidity bonus.
Valence comes from the music data: 0 means sad, 1 means happy.
Rain adds 0.3 to the multiplier, clouds add up to 0.2, humidity adds up to 0.1.
So if it rains, the CDI roughly doubles.

ZH: 项目的核心是 City Depression Index，CDI，是我自己设计的。
CDI 等于 1 减 valence，乘以 1 加雨天加成加云量加成加湿度加成。
Valence 来自音乐数据：0 是悲伤，1 是快乐。
下雨加 0.3，云量最多加 0.2，湿度最多加 0.1。所以下雨天 CDI 大约翻倍。

### [2:20-3:20] Kibana Dashboard

EN: Now the dashboard. This is what it looks like with all 390 records loaded.
World map: each circle is a city. Bigger and redder means higher CDI.
Bar chart ranks cities by average CDI. Line chart shows the 39-day trend.
Heatmap calendar is probably my favourite: you can see which cities had a bad week at a glance.
Rain vs CDI chart overlays rainfall and CDI on the same timeline, and the peaks match almost perfectly.

ZH: 现在看仪表盘。这是加载了全部 390 条记录的效果。
世界地图：每个圆圈是一个城市。越大越红就是 CDI 越高。
柱状图按平均 CDI 排名。折线图展示 39 天趋势。
热力图日历是我最喜欢的：一眼就能看出哪个城市这周比较丧。
降雨 vs CDI 图把降雨量和 CDI 叠加在一起，峰值几乎完美重合。

[ACTION: Scroll through dashboard panels]

### [3:20-4:00] Results

EN: So what did I find? Rainy day CDI averaged 0.88 versus 0.51 for sunny days.
That is a 1.74x difference. The t-test gave p less than 0.001, so it is statistically solid.
Weather alone explains 48% of CDI variance according to the linear regression model.
Pearson correlation: humidity and clouds both above 0.55, rainfall at 0.49.
The hypothesis holds: weather does correlate with musical mood.

ZH: 那么我发现了什么？雨天 CDI 平均值 0.88，晴天 0.51，相差 1.74 倍。
t 检验 p 值小于 0.001，统计上很扎实。
线性回归显示天气单独就能解释 48% 的 CDI 变异。
皮尔逊相关：湿度和云量都在 0.55 以上，降雨量 0.49。
假设成立：天气确实和音乐情绪相关。

### [4:00-4:40] Bonus Features

EN: I added five bonus features. Spark versions for formatting and combination.
S3 distributed storage using LocalStack. Airflow DAG for orchestration.
A blog post explaining the whole project. And the self-invented CDI metric itself.

[ACTION: Show bonus code files in VS Code]

ZH: 我加了五项加分功能。Spark 版本的格式化和合并。
使用 LocalStack 的 S3 分布式存储。Airflow DAG 编排。
一篇解释整个项目的博客文章。还有自创的 CDI 指标本身。

[ACTION: 在 VS Code 中展示加分文件]

### [4:40-5:00] Closing

EN: That is it. This project took two APIs, built a proper Data Lake, invented a new metric,
and proved a real correlation with statistical rigour. Thank you. Any questions?

ZH: 以上就是我的项目。用了两个 API，搭建了规范的 Data Lake，自创了一个指标，
并用统计方法验证了真实相关性。谢谢。有什么问题吗？
