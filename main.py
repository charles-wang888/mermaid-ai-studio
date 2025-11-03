"""主程序入口"""
import subprocess
import sys
import os


def main():
    """启动Streamlit应用"""
    print("=" * 60)
    print("🎨 架构设计图生成工具")
    print("=" * 60)
    print("\n正在启动应用...")
    print("浏览器将自动打开 http://localhost:8501\n")
    print("提示: 按 Ctrl+C 停止应用\n")
    print("-" * 60)
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_file = os.path.join(script_dir, "app.py")
    
    # 检查app.py是否存在
    if not os.path.exists(app_file):
        print(f"错误: 找不到 app.py 文件")
        print(f"路径: {app_file}")
        sys.exit(1)
    
    # 运行Streamlit应用
    try:
        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run", app_file,
                "--server.headless", "false",
                "--browser.gatherUsageStats", "false",
                "--server.fileWatcherType", "auto"
            ],
            cwd=script_dir,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("应用已关闭")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n启动失败: {e}")
        print("\n请确保已安装所有依赖:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except FileNotFoundError:
        print("\n错误: 找不到 streamlit 模块")
        print("请先安装 Streamlit:")
        print("pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n请确保已安装所有依赖:")
        print("pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()




