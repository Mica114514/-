# -*- coding: utf-8 -*-
"""
实时人数悬浮小窗
- 始终置顶、无边框、可拖动
- 定时(默认60秒)请求接口, 显示场内实时人数
- 右键 -> 退出   |   双击 -> 立即刷新一次

接口: 超级熊描小程序「场内实时人数」, 已抓包验证无需登录、无需 token。
"""

import json
import threading
import time
import tkinter as tk
import urllib.request

# ==================== 配置区 ====================
URL = "https://app.fitoneapp.com/appV3/3985/mg/admissionRecord/getMobileTodayCheckInCount"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Referer": "https://servicewechat.com/wxfce3b2791d81afc6/2/page-frame.html",
    "xweb_xhr": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF",
}
BODY = "{}"                            # POST 请求体(空对象)
FIELD_PATH = "data.insideMemberCount"  # 场内实时人数
INTERVAL = 60                          # 刷新间隔(秒)
# ================================================


def get_path(obj, path):
    """按 'a.b.0.c' 形式从 JSON 结构里取值(支持字典和列表下标)"""
    if not path:
        return None
    for key in path.split("."):
        key = key.strip()
        if isinstance(obj, list):
            obj = obj[int(key)]
        else:
            obj = obj[key]
    return obj


def fetch_count():
    """请求接口并返回人数字符串; 出错时抛出异常"""
    req = urllib.request.Request(
        URL,
        data=BODY.encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return str(get_path(data, FIELD_PATH))


class FloatingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("实时人数")
        self.root.overrideredirect(True)          # 无边框
        self.root.attributes("-topmost", True)    # 始终置顶
        self.root.configure(bg="#1e1e2e")

        # 拖动
        self._dx = 0
        self._dy = 0
        self.root.bind("<Button-1>", self.on_press)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<Double-Button-1>", lambda e: self.refresh())

        # 右键退出菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="立即刷新", command=self.refresh)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.root.destroy)
        self.root.bind("<Button-3>", self.show_menu)

        # 界面
        tk.Label(self.root, text="场内实时人数", font=("微软雅黑", 10),
                 bg="#1e1e2e", fg="#8888aa").pack(pady=(10, 0))
        self.num = tk.Label(self.root, text="…", font=("Consolas", 32, "bold"),
                            bg="#1e1e2e", fg="#7ef29a")
        self.num.pack(padx=20)
        self.time_lbl = tk.Label(self.root, text="加载中…", font=("微软雅黑", 8),
                                 bg="#1e1e2e", fg="#666677")
        self.time_lbl.pack(pady=(0, 10))

        self.refresh()  # 启动后立即拉一次

    def on_press(self, e):
        self._dx, self._dy = e.x, e.y

    def on_drag(self, e):
        x = self.root.winfo_x() + (e.x - self._dx)
        y = self.root.winfo_y() + (e.y - self._dy)
        self.root.geometry(f"+{x}+{y}")

    def show_menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def refresh(self):
        def work():
            try:
                val = fetch_count()
                self.root.after(0, lambda: self.show_ok(val))
            except Exception as ex:
                self.root.after(0, lambda: self.show_err(ex))
        threading.Thread(target=work, daemon=True).start()
        # 调度下一次
        self.root.after(INTERVAL * 1000, self.refresh)

    def show_ok(self, val):
        self.num.config(text=val, fg="#7ef29a")
        self.time_lbl.config(text="更新于 " + self.now())

    def show_err(self, ex):
        self.num.config(text="获取失败", fg="#ff7a7a")
        self.time_lbl.config(text=f"{ex}  |  {self.now()}")

    @staticmethod
    def now():
        return time.strftime("%H:%M:%S")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    FloatingWindow().run()
