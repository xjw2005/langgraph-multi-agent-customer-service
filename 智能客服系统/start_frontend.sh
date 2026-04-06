#!/bin/bash

# 母婴智能客服系统 - 前端启动脚本

echo "🍼 母婴智能客服系统 - 前端启动"
echo "================================"

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js 16+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm未安装，请先安装npm"
    exit 1
fi

# 进入前端目录
cd frontend

# 安装依赖
echo "📦 安装前端依赖..."
npm install

# 启动开发服务器
echo "🚀 启动前端开发服务器..."
echo "📱 前端地址: http://localhost:3000"
echo ""
echo "💡 提示: 按 Ctrl+C 停止服务"
echo "💡 确保后端服务已在 http://localhost:8000 运行"
echo ""

npm start