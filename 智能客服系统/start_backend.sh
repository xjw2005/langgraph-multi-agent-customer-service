#!/bin/bash

# 母婴智能客服系统 - 快速启动脚本

echo "🍼 母婴智能客服系统 - 快速启动"
echo "================================"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python 3.8+"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，从示例文件复制..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已创建.env文件"
        echo "📝 请编辑.env文件，填入你的OpenAI API Key"
        echo "   OPENAI_API_KEY=your_api_key_here"
        echo ""
        read -p "按回车键继续..."
    else
        echo "❌ .env.example文件不存在"
        exit 1
    fi
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔧 创建Python虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements_new.txt

# 创建数据目录
mkdir -p data

# 初始化数据
echo "📊 初始化系统数据..."
python init_knowledge.py
python init_products.py

# 启动后端服务
echo "🚀 启动后端服务..."
echo "📱 后端API地址: http://localhost:8000"
echo "📊 API文档地址: http://localhost:8000/docs"
echo ""
echo "💡 提示: 按 Ctrl+C 停止服务"
echo ""

python main.py