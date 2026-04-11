import subprocess
import sys
import time
import os
import urllib.request
import urllib.error

def wait_for_backend(url="http://127.0.0.1:8000/openapi.json", timeout=120):
    
    start_time = time.time()
    while True:
        try:
            response = urllib.request.urlopen(url, timeout=1)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, ConnectionResetError, TimeoutError):
            pass
        
        if time.time() - start_time > timeout:
            return False
            
        time.sleep(1)

def start_services():
    print("===================================================")
    print(" 正在启动日本发票智能录入系统")
    print("===================================================")
    
    os.makedirs("data", exist_ok=True)
    
    # 步骤 1: 启动 FastAPI 后端
    print("\n [1/2] 正在拉起后端 API，加载 AI 模型至显存中...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # 开始智能等待后端就绪
    is_ready = wait_for_backend()
    
    if not is_ready:
        print("\n 错误：后端启动超时！请检查终端中是否有模型报错信息。")
        backend_process.terminate()
        sys.exit(1)
        
    print("后端服务已完全就绪！")
    
    # 步骤 2: 启动 Streamlit 前端 (确保在后端就绪后执行)
    print("\n [2/2] 正在启动前端 Web 界面...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    print("\n 系统全部启动完毕！")
    print(" 请在自动弹出的浏览器窗口中进行操作。")
    print(" 如需彻底退出系统，请在当前终端按下 [Ctrl + C]。\n")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n 接收到退出指令，正在安全释放显存并关闭所有服务...")
        backend_process.terminate()
        frontend_process.terminate()
        print(" 服务已完全清理，安全关闭。")

if __name__ == "__main__":
    start_services()