# Stock Investment Agent - AI Foundations Capstone Project 2025

## 项目简介

这是一个基于AI的智能股票投资分析系统，集成了K线技术分析、新闻情绪分析等功能，为用户提供全面的股票投资决策支持。

## 功能特性

- 📈 **K线技术分析**：集成Dify工作流进行专业K线分析
- 📰 **新闻情绪分析**：基于最新新闻进行市场情绪评估
- 🤖 **AI智能推荐**：综合多维度数据提供投资建议
- 🎨 **友好界面**：基于Gradio的现代化Web界面
- 🐳 **容器化部署**：使用Docker Compose一键部署

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gradio App    │    │  Monitor API    │    │  Dify Workflow  │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│  (AI Analysis)  │
│   Port: 7860    │    │   Port: 5001    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 前置要求

- Docker Desktop
- Docker Compose
- Windows 10/11 或 macOS/Linux

### 环境配置

1. **克隆项目**
```bash
git clone https://github.com/Boxin-Byron/Stock_Investment_Agent-AI_Foundations_Capstone_Project-_2025.git
cd Stock_Investment_Agent-AI_Foundations_Capstone_Project-_2025
```

2. **配置环境变量**
创建 `.env` 文件并配置以下变量：
```env
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_KLINE_FLOW_ID=your_kline_flow_id
DIFY_NEWS_FLOW_ID=your_news_flow_id
DIFY_KLINE_API_KEY=your_kline_api_key
DIFY_NEWS_API_KEY=your_news_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 🐳 Docker 部署

### 首次部署（构建并启动）

```bash
# 构建并启动所有服务
docker-compose -p stock-investment-agent up -d --build
```

这个命令会：
- 🔨 构建 monitor 和 app 服务的 Docker 镜像
- 🚀 启动服务容器
- 🌐 配置网络连接
- 📦 挂载数据卷

### 查看服务状态

```bash
# 查看所有服务状态
docker-compose -p stock-investment-agent ps

# 查看服务日志
docker-compose -p stock-investment-agent logs -f

# 查看特定服务日志
docker-compose -p stock-investment-agent logs -f monitor
docker-compose -p stock-investment-agent logs -f app
```

### 停止服务

```bash
# 停止所有服务但保留容器
docker-compose -p stock-investment-agent stop

# 停止并删除容器（保留镜像和数据卷）
docker-compose -p stock-investment-agent down

# 停止并删除容器、网络、镜像（谨慎使用）
docker-compose -p stock-investment-agent down --rmi all
```

### 重新启动服务

如果服务已经构建过，可以直接启动：

```bash
# 启动现有容器
docker-compose -p stock-investment-agent start

# 或重新创建并启动容器
docker-compose -p stock-investment-agent up -d

# 如果需要重新构建镜像
docker-compose -p stock-investment-agent up -d --build
```

## 🔧 常用管理命令

### 服务管理

```bash
# 重启特定服务
docker-compose -p stock-investment-agent restart monitor
docker-compose -p stock-investment-agent restart app

# 强制重新创建服务
docker-compose -p stock-investment-agent up -d --force-recreate

# 仅重新构建特定服务
docker-compose -p stock-investment-agent build monitor
docker-compose -p stock-investment-agent build app
```

### 调试和维护

```bash
# 进入容器进行调试
docker-compose -p stock-investment-agent exec monitor bash
docker-compose -p stock-investment-agent exec app bash

# 查看容器资源使用情况
docker stats

# 清理未使用的资源
docker system prune -f

# 查看镜像大小
docker images | grep stock-investment-agent
```

## 🌐 服务访问

服务启动后，可以通过以下地址访问：

- **主应用界面**: http://localhost:7860
- **Monitor API**: http://localhost:5001
- **健康检查**: http://localhost:5001/health
- **API文档**: http://localhost:5001/docs

## 🧪 功能测试

### 测试 Monitor API

```bash
# 健康检查
curl http://localhost:5001/health

# 测试股票评估
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600519"
```

### 测试主应用

1. 打开浏览器访问 http://localhost:7860
2. 在输入框中输入股票代码（如：600519）或股票名称（如：贵州茅台）
3. 点击"🔍 立即分析"按钮
4. 查看K线分析、情绪分析和投资建议结果

## 🔧 API接口测试详细说明

本系统提供了完整的RESTful API接口，以下是在Linux和Windows环境下的详细测试方法。

### API接口列表

- **健康检查**: `GET /health`
- **网络测试**: `GET /api/network_test`
- **用户偏好查询**: `GET /api/user_preferences/{user_id}`
- **用户决策记录**: `POST /api/user_decision`
- **股票分析评估**: `POST /api/stock_eval`

### Linux环境下的API测试

#### 1. 健康检查接口 (Linux)

```bash
# 基础健康检查
curl -X GET "http://localhost:5001/health"

# 查看响应头信息
curl -i -X GET "http://localhost:5001/health"

# 预期响应
# {"status": "healthy", "timestamp": "2025-01-21T10:30:00Z"}
```

#### 2. 网络测试接口 (Linux)

```bash
# 测试网络连通性
curl -X GET "http://localhost:5001/api/network_test"

# 预期响应
# {
#   "status": "success",
#   "results": {
#     "baidu.com": {"status": "success", "response_time": 0.123},
#     "tencent.com": {"status": "success", "response_time": 0.098}
#   },
#   "timestamp": "2025-01-21T10:30:00Z"
# }
```

#### 3. 用户偏好查询接口 (Linux)

```bash
# 查询用户偏好
curl -X GET "http://localhost:5001/api/user_preferences/user123"

# 预期响应
# {
#   "user_id": "user123",
#   "preferences": {...},
#   "timestamp": "2025-01-21T10:30:00Z"
# }
```

#### 4. 用户决策记录接口 (Linux)

```bash
# 记录用户决策（JSON格式）
curl -X POST "http://localhost:5001/api/user_decision" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "stock_code": "600519",
    "decision": "buy",
    "confidence": 0.8,
    "reason": "技术分析显示上涨趋势"
  }'

# 记录用户决策（查询参数格式）
curl -X POST "http://localhost:5001/api/user_decision?user_id=user123&stock_code=600519&decision=buy&confidence=0.8&reason=看好长期发展"

# 预期响应
# {
#   "status": "success",
#   "message": "用户决策已记录",
#   "decision_id": "dec_123456",
#   "timestamp": "2025-01-21T10:30:00Z"
# }
```

#### 5. 股票分析评估接口 (Linux)

```bash
# 分析单只股票（推荐方式）
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600519"

# 分析股票并指定用户ID
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=000001&user_id=user123"

# 使用JSON格式请求
curl -X POST "http://localhost:5001/api/stock_eval" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "user_id": "user123"
  }'

# 预期响应
# {
#   "stock_code": "600519",
#   "analysis_result": {
#     "kline_analysis": {...},
#     "news_sentiment": {...},
#     "recommendation": "买入"
#   },
#   "timestamp": "2025-01-21T10:30:00Z"
# }
```

### Windows环境下的API测试

#### 使用PowerShell进行测试

#### 1. 健康检查接口 (Windows)

```powershell
# 基础健康检查
Invoke-RestMethod -Uri "http://localhost:5001/health" -Method GET

# 查看详细信息
Invoke-WebRequest -Uri "http://localhost:5001/health" -Method GET
```

#### 2. 网络测试接口 (Windows)

```powershell
# 测试网络连通性
Invoke-RestMethod -Uri "http://localhost:5001/api/network_test" -Method GET

# 格式化输出
$response = Invoke-RestMethod -Uri "http://localhost:5001/api/network_test" -Method GET
$response | ConvertTo-Json -Depth 10
```

#### 3. 用户偏好查询接口 (Windows)

```powershell
# 查询用户偏好
Invoke-RestMethod -Uri "http://localhost:5001/api/user_preferences/user123" -Method GET
```

#### 4. 用户决策记录接口 (Windows)

```powershell
# 记录用户决策（JSON格式）
$body = @{
    user_id = "user123"
    stock_code = "600519"
    decision = "buy"
    confidence = 0.8
    reason = "技术分析显示上涨趋势"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/api/user_decision" -Method POST -Body $body -ContentType "application/json"

# 记录用户决策（查询参数格式）
Invoke-RestMethod -Uri "http://localhost:5001/api/user_decision?user_id=user123&stock_code=600519&decision=buy&confidence=0.8&reason=看好长期发展" -Method POST
```

#### 5. 股票分析评估接口 (Windows)

```powershell
# 分析单只股票
Invoke-RestMethod -Uri "http://localhost:5001/api/stock_eval?stock_code=600519" -Method POST

# 使用JSON格式请求
$body = @{
    stock_code = "600519"
    user_id = "user123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/api/stock_eval" -Method POST -Body $body -ContentType "application/json"

# 保存响应到文件
$response = Invoke-RestMethod -Uri "http://localhost:5001/api/stock_eval?stock_code=600519" -Method POST
$response | ConvertTo-Json -Depth 10 | Out-File -FilePath "stock_analysis_result.json" -Encoding UTF8
```

#### 使用curl for Windows进行测试

如果您的Windows系统安装了curl（Windows 10 1803+默认包含），也可以使用与Linux相同的命令：

```cmd
REM 健康检查
curl -X GET "http://localhost:5001/health"

REM 网络测试
curl -X GET "http://localhost:5001/api/network_test"

REM 股票分析
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600519"

REM 用户决策记录
curl -X POST "http://localhost:5001/api/user_decision" ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"user123\",\"stock_code\":\"600519\",\"decision\":\"buy\",\"confidence\":0.8,\"reason\":\"看好长期发展\"}"
```

### Docker容器环境下的测试

#### 从容器内部测试

```bash
# 进入monitor容器
docker-compose -p stock-investment-agent exec monitor bash

# 在容器内测试本地接口
curl -X GET "http://localhost:5001/health"
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600519"

# 退出容器
exit
```

#### 从宿主机测试容器服务

```bash
# Linux/macOS
curl -X GET "http://localhost:5001/health"

# Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:5001/health" -Method GET
```

### 批量测试脚本

#### Linux批量测试脚本

创建测试脚本 `test_apis.sh`：

```bash
#!/bin/bash

BASE_URL="http://localhost:5001"
echo "=== Stock Investment Agent API 测试 ==="

echo "1. 健康检查..."
curl -s -X GET "$BASE_URL/health" | jq .

echo -e "\n2. 网络测试..."
curl -s -X GET "$BASE_URL/api/network_test" | jq .

echo -e "\n3. 用户偏好查询..."
curl -s -X GET "$BASE_URL/api/user_preferences/test_user" | jq .

echo -e "\n4. 股票分析（贵州茅台）..."
curl -s -X POST "$BASE_URL/api/stock_eval?stock_code=600519" | jq .

echo -e "\n5. 用户决策记录..."
curl -s -X POST "$BASE_URL/api/user_decision?user_id=test_user&stock_code=600519&decision=buy&confidence=0.8&reason=测试" | jq .

echo -e "\n=== 测试完成 ==="
```

运行测试：
```bash
chmod +x test_apis.sh
./test_apis.sh
```

#### Windows PowerShell批量测试脚本

创建测试脚本 `test_apis.ps1`：

```powershell
$BASE_URL = "http://localhost:5001"
Write-Host "=== Stock Investment Agent API 测试 ===" -ForegroundColor Green

Write-Host "1. 健康检查..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/health" -Method GET
$response | ConvertTo-Json

Write-Host "`n2. 网络测试..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/api/network_test" -Method GET
$response | ConvertTo-Json

Write-Host "`n3. 用户偏好查询..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/api/user_preferences/test_user" -Method GET
$response | ConvertTo-Json

Write-Host "`n4. 股票分析（贵州茅台）..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/api/stock_eval?stock_code=600519" -Method POST
$response | ConvertTo-Json -Depth 10

Write-Host "`n5. 用户决策记录..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$BASE_URL/api/user_decision?user_id=test_user&stock_code=600519&decision=buy&confidence=0.8&reason=测试" -Method POST
$response | ConvertTo-Json

Write-Host "`n=== 测试完成 ===" -ForegroundColor Green
```

运行测试：
```powershell
# 设置执行策略（如果需要）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 运行测试脚本
.\test_apis.ps1
```

### 常见股票代码测试示例

```bash
# 测试热门股票
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600519"  # 贵州茅台
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=000001"  # 平安银行
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=000002"  # 万科A
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600036"  # 招商银行
curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600000"  # 浦发银行
```

### API响应格式说明

所有API接口均返回JSON格式数据，通用字段包括：

- `status`: 请求状态（success/error）
- `timestamp`: 响应时间戳
- `message`: 状态描述信息
- `data`: 具体业务数据

错误响应格式：
```json
{
  "status": "error",
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-21T10:30:00Z"
}
```

### 性能测试

#### 使用Apache Bench (ab)

```bash
# 安装ab工具
sudo apt-get install apache2-utils  # Ubuntu/Debian
brew install httpie  # macOS

# 健康检查接口压力测试
ab -n 100 -c 10 http://localhost:5001/health

# 股票分析接口性能测试
ab -n 50 -c 5 -p post_data.json -T application/json http://localhost:5001/api/stock_eval
```

#### 使用PowerShell进行简单性能测试

```powershell
# 测试响应时间
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:5001/health" -Method GET
$stopwatch.Stop()
Write-Host "响应时间: $($stopwatch.ElapsedMilliseconds) ms"
```

## 📁 项目结构

```
├── app/                    # Gradio前端应用
│   ├── app.py             # 主应用文件
│   ├── Dockerfile         # 应用容器配置
│   ├── requirements.txt   # Python依赖
│   └── fonts/             # 中文字体文件
├── monitor/               # FastAPI后端服务
│   ├── monitor.py         # API服务文件
│   ├── Dockerfile         # 服务容器配置
│   └── requirements.txt   # Python依赖
├── flow/                  # Dify工作流配置
│   ├── k_line_analysis/   # K线分析工作流
│   └── news_sentiment/    # 新闻情绪分析工作流
├── data/                  # 数据处理脚本
├── docker-compose.yml     # Docker编排配置
└── README.md             # 项目说明文档
```

## 🔍 K线分析集成验证

本项目的核心功能是K线分析，通过以下方式验证集成：

1. **Monitor服务集成**：
   - `monitor.py` 中的 `call_kline_flow()` 函数调用Dify K线分析工作流
   - `/api/stock_eval` 接口返回K线分析结果

2. **App应用集成**：
   - `app.py` 中的 `call_stock_eval_api()` 函数调用Monitor API
   - `analyze_stock()` 函数整合K线分析结果并展示

3. **验证步骤**：
   ```bash
   # 检查服务状态
   docker-compose -p stock-investment-agent ps
   
   # 测试K线分析API
   curl -X POST "http://localhost:5001/api/stock_eval?stock_code=600519"
   
   # 在Web界面测试完整流程
   # 访问 http://localhost:7860 并输入股票代码
   ```

## ⚠️ 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -ano | findstr :5001
   netstat -ano | findstr :7860
   ```

2. **Docker网络问题**
   ```bash
   # 重置Docker网络
   docker network prune -f
   docker-compose -p stock-investment-agent down
   docker-compose -p stock-investment-agent up -d
   ```

3. **镜像构建失败**
   ```bash
   # 清理构建缓存
   docker builder prune -f
   # 重新构建
   docker-compose -p stock-investment-agent build --no-cache
   ```

4. **API连接问题**
   ```bash
   # 检查环境变量配置
   docker-compose -p stock-investment-agent exec monitor env | grep DIFY
   ```

### 日志调试

```bash
# 查看详细启动日志
docker-compose -p stock-investment-agent up --no-detach

# 查看错误日志
docker-compose -p stock-investment-agent logs --tail=50 monitor
docker-compose -p stock-investment-agent logs --tail=50 app
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至项目维护者
- 查看项目 Wiki 获取更多文档

---

🎯 **项目目标**：通过AI技术提升股票投资决策的科学性和准确性，为投资者提供专业的技术分析和市场洞察。