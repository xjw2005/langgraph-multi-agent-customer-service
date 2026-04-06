# 🍼 母婴智能客服系统 - 部署指南

## 📋 系统概述

这是一个基于 LangGraph + FastAPI + React 的母婴智能客服系统，提供专业的母婴产品咨询和推荐服务。

## 🚀 快速部署

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

### 一键部署

```bash
# 1. 克隆项目（如果还没有）
git clone <your-repo-url>
cd 智能客服系统

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key

# 3. 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 手动部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps
```

## 🔧 配置说明

### 环境变量 (.env)

```env
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 数据库配置
DATABASE_PATH=./data/customer_service.db

# 系统配置
DEBUG=false
LOG_LEVEL=info
```

## 📱 访问地址

- **前端界面**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🛠️ 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 数据管理

```bash
# 备份数据
docker-compose exec backend cp /app/data/customer_service.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# 清理数据
docker-compose down
sudo rm -rf data/*
docker-compose up -d
```

## 🔍 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 修改 docker-compose.yml 中的端口映射
   ports:
     - "8080:80"  # 前端改为8080端口
     - "8001:8000"  # 后端改为8001端口
   ```

2. **内存不足**
   ```bash
   # 检查系统资源
   docker system df
   docker system prune -a
   ```

3. **API Key 错误**
   ```bash
   # 检查环境变量
   docker-compose exec backend env | grep OPENAI
   
   # 重新设置环境变量
   vim .env
   docker-compose restart
   ```

### 日志分析

```bash
# 查看详细错误日志
docker-compose logs --tail=100 backend

# 实时监控日志
docker-compose logs -f --tail=50

# 导出日志到文件
docker-compose logs > system.log 2>&1
```

## 📊 性能监控

### 系统状态检查

```bash
# 检查容器资源使用
docker stats

# 检查服务健康状态
curl http://localhost:8000/health
curl http://localhost:80

# 检查API响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/system/stats
```

### 性能优化

1. **增加内存限制**
   ```yaml
   # 在 docker-compose.yml 中添加
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

2. **启用缓存**
   ```bash
   # 添加Redis缓存（可选）
   docker run -d --name redis -p 6379:6379 redis:alpine
   ```

## 🔒 安全配置

### 生产环境建议

1. **使用HTTPS**
   ```nginx
   # 在 nginx.conf 中配置SSL
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

2. **限制CORS**
   ```python
   # 在 main.py 中修改
   allow_origins=["https://yourdomain.com"]
   ```

3. **环境变量安全**
   ```bash
   # 设置文件权限
   chmod 600 .env
   ```

## 📈 扩展部署

### 多实例部署

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

### 负载均衡

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

## 📞 技术支持

如遇到问题，请：

1. 查看日志文件
2. 检查系统资源
3. 验证配置文件
4. 提交Issue到项目仓库

---

**🍼 专为高端母婴市场打造的智能客服解决方案**

*让每一位妈妈都能获得专业、贴心、可信赖的育儿指导*