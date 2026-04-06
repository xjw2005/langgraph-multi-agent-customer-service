#!/bin/bash

# 母婴智能客服系统部署脚本

echo "🍼 开始部署母婴智能客服系统..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，从示例文件复制..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已创建.env文件，请编辑其中的配置"
    else
        echo "❌ .env.example文件不存在"
        exit 1
    fi
fi

# 初始化数据
echo "📊 初始化系统数据..."
if [ -f "init_knowledge.py" ] && [ -f "init_products.py" ]; then
    echo "✅ 数据初始化脚本已准备就绪"
else
    echo "⚠️  数据初始化脚本缺失，系统将在启动时自动初始化"
fi

# 构建和启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 检查后端健康状态
echo "🏥 检查后端健康状态..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    docker-compose logs backend
    exit 1
fi

# 检查前端
echo "🌐 检查前端服务..."
if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务启动失败"
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "🎉 部署完成！"
echo "📱 前端访问地址: http://localhost"
echo "🔧 后端API地址: http://localhost:8000"
echo "📊 API文档地址: http://localhost:8000/docs"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"