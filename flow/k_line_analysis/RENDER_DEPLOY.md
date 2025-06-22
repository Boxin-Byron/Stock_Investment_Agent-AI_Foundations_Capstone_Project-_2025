# Render 部署指南

#### 本地访问
- URL: `http://localhost:8000`
- 健康检查: `http://localhost:8000/healthz`
- API文档: `http://localhost:8000/docs`

#### Render 部署后访问
- URL: `https://stock-investment-agent-ai-foundations.onrender.com`
- 健康检查: `https://stock-investment-agent-ai-foundations.onrender.com/healthz`
- API文档: `https://stock-investment-agent-ai-foundations.onrender.com/docs`

### 5. API 使用示例

```bash
# 健康检查
curl https://stock-investment-agent-ai-foundations.onrender.com/healthz

# 分析股票数据
curl -X POST "https://stock-investment-agent-ai-foundations.onrender.com/analyze" \
     -H "Content-Type: application/json" \
     -d '{"stock_code": "600519"}'
```

### 6. 注意事项

1. **免费计划限制**：
   - Render 免费计划在无活动时会休眠
   - 首次请求可能需要等待服务启动（~30秒）

2. **环境变量安全**：
   - 敏感信息（API密钥）已标记为 `sync: false`
   - 不会在构建日志中显示

3. **依赖安装**：
   - 构建时会自动安装系统依赖（gcc, build-essential等）
   - 这些是编译某些Python包所必需的

4. **健康检查**：
   - Render 会定期访问 `/healthz` 端点检查服务状态
   - 如果连续失败，服务会自动重启

### 7. 故障排除

如果部署失败，请检查：
1. 环境变量是否正确设置
2. requirements.txt 是否包含所有依赖
3. 构建日志中的错误信息
4. API密钥是否有效且有足够权限
