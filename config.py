# 尚米 — 商家数据一键导出工具
# 配置文件
#
# 使用说明：
# 1. 把下面空着的 API Key 填上你的
# 2. 运行 python run.py 启动服务
# 3. 打开浏览器访问 http://localhost:8000

# === 高德地图 API ===
# 申请地址：https://lbs.amap.com → 控制台 → 应用管理
# 创建应用，添加「Web服务API」类型的 Key
GAODE_API_KEY = "a0039a0464bec5b88b03819b4c056f95"

# === 百度地图 API ===
# 申请地址：https://lbsyun.baidu.com → 控制台 → 创建应用
# 应用类型选「服务端」，勾选「地点检索V2.0」
BAIDU_API_KEY = "tTHnAqig4U4yZAGmbVxuD8jBrGNifZHc"

# === 服务设置 ===
HOST = "0.0.0.0"       # 监听地址（0.0.0.0=允许局域网访问）
PORT = 8000             # 端口号
