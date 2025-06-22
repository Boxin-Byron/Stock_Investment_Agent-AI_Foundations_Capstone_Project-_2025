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