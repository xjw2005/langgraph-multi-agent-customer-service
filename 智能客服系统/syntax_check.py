#!/usr/bin/env python3
"""
语法检查脚本 - 验证所有Python文件的语法正确性
"""

import ast
import os
import sys

def check_python_syntax(file_path):
    """检查单个Python文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # 尝试解析AST
        ast.parse(source, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"语法错误: {e.msg} (行 {e.lineno})"
    except Exception as e:
        return False, f"其他错误: {str(e)}"

def main():
    """主检查函数"""
    print("🔍 Python语法检查")
    print("=" * 50)

    # 要检查的文件列表
    files_to_check = [
        "config/settings.py",
        "config/database.py",
        "core/states.py",
        "core/router.py",
        "core/main_graph.py",
        "agents/base_agent.py",
        "agents/order_agent.py",
        "agents/product_agent.py",
        "services/database_service.py",
        "examples/basic_demo.py",
        "examples/advanced_demo.py"
    ]

    all_passed = True

    for file_path in files_to_check:
        if os.path.exists(file_path):
            success, error = check_python_syntax(file_path)
            if success:
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path}: {error}")
                all_passed = False
        else:
            print(f"⚠️ {file_path}: 文件不存在")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有文件语法检查通过！")
        return True
    else:
        print("❌ 发现语法错误，请修复后重试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)