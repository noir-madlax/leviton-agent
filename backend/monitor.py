# run_phoenix.py
import phoenix as px
import time

print("启动 Phoenix 监控服务...")

# 启动 Phoenix 应用。
# 这会在终端打印出访问 UI 的地址，通常是 http://localhost:6006
app = px.launch_app()

print("\nPhoenix 服务已启动。")
print("请在浏览器中访问上面打印出的 URL。")
print("在当前终端按下 Ctrl+C 可以停止服务。")

# 使用一个循环让脚本保持运行，直到手动中断
try:
    while True:
        time.sleep(86400) # 挂起，等待一天或直到被中断
except KeyboardInterrupt:
    print("\nPhoenix 服务已停止。")
