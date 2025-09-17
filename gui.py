import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import asyncio
import os
import signal
import logging
import coloredlogs
from pathlib import Path

from init import init
from init import tunnel
from init import route
import run
import config
from route_manager import RouteManager, RouteManagerGUI


class iOSRealRunGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("iOS Real Run - 跑步模拟器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 运行状态
        self.is_running = False
        self.tunnel_process = None
        self.tunnel_address = None
        self.tunnel_port = None
        
        # 路径管理器
        self.route_manager = RouteManager()
        self.route_manager_gui = RouteManagerGUI(root)
        
        # 设置日志
        self.setup_logging()
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
        
    def setup_logging(self):
        """设置日志系统"""
        self.logger = logging.getLogger(__name__)
        coloredlogs.install(level=logging.INFO)
        self.logger.setLevel(logging.INFO)
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="iOS Real Run - 跑步模拟器", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 路径文件选择
        ttk.Label(main_frame, text="路径文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.route_file_var = tk.StringVar()
        self.route_file_entry = ttk.Entry(main_frame, textvariable=self.route_file_var, width=40)
        self.route_file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_route_file).grid(row=1, column=2, pady=5)
        ttk.Button(main_frame, text="管理", command=self.open_route_manager).grid(row=1, column=3, padx=(5, 0), pady=5)
        
        # 速度设置
        ttk.Label(main_frame, text="跑步速度 (m/s):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.DoubleVar(value=4.2)
        speed_frame = ttk.Frame(main_frame)
        speed_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        speed_frame.columnconfigure(0, weight=1)
        
        self.speed_scale = ttk.Scale(speed_frame, from_=1.0, to=10.0, 
                                   variable=self.speed_var, orient=tk.HORIZONTAL)
        self.speed_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.speed_label = ttk.Label(speed_frame, text="4.2")
        self.speed_label.grid(row=0, column=1, padx=(5, 0))
        
        # 速度变化范围
        ttk.Label(main_frame, text="速度变化范围 (%):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.speed_variation_var = tk.IntVar(value=15)
        variation_frame = ttk.Frame(main_frame)
        variation_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        variation_frame.columnconfigure(0, weight=1)
        
        self.variation_scale = ttk.Scale(variation_frame, from_=0, to=50, 
                                       variable=self.speed_variation_var, orient=tk.HORIZONTAL)
        self.variation_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.variation_label = ttk.Label(variation_frame, text="15")
        self.variation_label.grid(row=0, column=1, padx=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="开始跑步", 
                                     command=self.start_running, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止跑步", 
                                    command=self.stop_running, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_config_button = ttk.Button(button_frame, text="保存配置", 
                                           command=self.save_config)
        self.save_config_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.route_manager_button = ttk.Button(button_frame, text="路径管理", 
                                             command=self.open_route_manager)
        self.route_manager_button.pack(side=tk.LEFT)
        
        # 状态显示
        ttk.Label(main_frame, text="状态:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                    foreground="green")
        self.status_label.grid(row=5, column=1, sticky=tk.W, padx=(5, 0), pady=(10, 5))
        
        # 日志显示区域
        ttk.Label(main_frame, text="运行日志:").grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 绑定事件
        self.speed_scale.configure(command=self.update_speed_label)
        self.variation_scale.configure(command=self.update_variation_label)
        
    def update_speed_label(self, value):
        """更新速度标签"""
        self.speed_label.config(text=f"{float(value):.1f}")
        
    def update_variation_label(self, value):
        """更新变化范围标签"""
        self.variation_label.config(text=f"{int(float(value))}")
        
    def browse_route_file(self):
        """浏览路径文件"""
        filetypes = [
            ("文本文件", "*.txt"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="选择路径文件",
            filetypes=filetypes,
            initialdir=os.getcwd()
        )
        if filename:
            self.route_file_var.set(filename)
            
    def open_route_manager(self):
        """打开路径管理器"""
        self.route_manager_gui.show_route_manager()
        
    def load_config(self):
        """加载配置"""
        try:
            # 加载路径文件配置
            if hasattr(config.config, 'routeConfig'):
                route_config = config.config.routeConfig
                # 检查是否是新的JSON格式
                if route_config.endswith('.json'):
                    try:
                        route_data = self.route_manager.load_route_json(route_config)
                        self.log_message(f"加载JSON路径: {route_data['name']}")
                    except Exception as e:
                        self.log_message(f"加载JSON路径失败: {e}")
                self.route_file_var.set(route_config)
            
            # 加载速度配置
            if hasattr(config.config, 'v'):
                self.speed_var.set(config.config.v)
                self.speed_label.config(text=f"{config.config.v}")
                
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
            
    def save_config(self):
        """保存配置到config.yaml"""
        try:
            config_data = {
                'v': self.speed_var.get(),
                'routeConfig': self.route_file_var.get(),
                'libimobiledeviceDir': getattr(config.config, 'libimobiledeviceDir', 'libimobiledevice'),
                'imageDir': getattr(config.config, 'imageDir', 'DeveloperDiskImage')
            }
            
            import yaml
            with open("config.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                
            self.log_message("配置已保存")
            messagebox.showinfo("成功", "配置已保存到 config.yaml")
            
        except Exception as e:
            self.log_message(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
            
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_running(self):
        """开始跑步模拟"""
        if self.is_running:
            return
            
        # 验证输入
        if not self.route_file_var.get():
            messagebox.showerror("错误", "请选择路径文件")
            return
            
        if not os.path.exists(self.route_file_var.get()):
            messagebox.showerror("错误", "路径文件不存在")
            return
            
        # 更新UI状态
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("正在启动...")
        self.status_label.config(foreground="orange")
        
        # 在新线程中运行
        self.running_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.running_thread.start()
        
    def stop_running(self):
        """停止跑步模拟"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.status_var.set("正在停止...")
        self.status_label.config(foreground="orange")
        
        # 终止隧道进程
        if self.tunnel_process and self.tunnel_process.is_alive():
            self.tunnel_process.terminate()
            self.log_message("隧道进程已终止")
            
        # 更新UI状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        self.status_label.config(foreground="red")
        self.log_message("跑步模拟已停止")
        
    def run_simulation(self):
        """运行模拟的主函数"""
        try:
            self.log_message("开始初始化...")
            
            # 初始化
            init.init()
            self.log_message("初始化完成")
            
            # 启动隧道
            self.log_message("正在启动隧道...")
            # 在GUI模式下，我们不需要信号处理，因为有停止按钮
            self.tunnel_process, self.tunnel_address, self.tunnel_port = tunnel.tunnel()
            
            self.log_message(f"隧道地址: {self.tunnel_address}, 端口: {self.tunnel_port}")
            
            # 获取路径
            route_file = self.route_file_var.get()
            
            # 根据文件格式加载路径
            if route_file.endswith('.json'):
                try:
                    route_data = self.route_manager.load_route_json(route_file)
                    loc = route_data['coordinates']
                    self.log_message(f"从JSON文件 {route_file} 获取路径: {route_data['name']}")
                    if route_data['metadata'].get('distance'):
                        self.log_message(f"路径距离: {route_data['metadata']['distance']:.1f}米")
                except Exception as e:
                    self.log_message(f"加载JSON路径失败: {e}")
                    raise
            else:
                # 传统txt格式
                original_route_config = config.config.routeConfig
                config.config.routeConfig = route_file
                
                loc = route.get_route()
                self.log_message(f"从TXT文件 {route_file} 获取路径")
                
                # 恢复原始配置
                config.config.routeConfig = original_route_config
            
            # 更新状态
            self.status_var.set("正在跑步...")
            self.status_label.config(foreground="green")
            self.log_message(f"已开始模拟跑步，速度大约为 {self.speed_var.get()} m/s")
            self.log_message("会无限循环，点击停止按钮退出")
            self.log_message("请勿直接关闭窗口，否则无法还原正常定位")
            
            # 运行模拟
            speed_variation = self.speed_variation_var.get()
            asyncio.run(self.run_async(loc, self.speed_var.get(), speed_variation))
            
        except Exception as e:
            self.log_message(f"运行出错: {e}")
            self.status_var.set("运行出错")
            self.status_label.config(foreground="red")
        finally:
            # 清理
            if self.tunnel_process and self.tunnel_process.is_alive():
                self.tunnel_process.terminate()
                self.log_message("隧道进程已终止")
                
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("已停止")
            self.status_label.config(foreground="red")
            
    async def run_async(self, loc, speed, speed_variation):
        """异步运行模拟"""
        import random
        import time
        
        from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
        from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
        
        rsd = RemoteServiceDiscoveryService((self.tunnel_address, self.tunnel_port))
        await asyncio.sleep(2)
        await rsd.connect()
        dvt = DvtSecureSocketProxyService(rsd)
        dvt.perform_handshake()
        
        while self.is_running:
            # 计算随机速度
            v_rand = 1000 / (1000 / speed - (2 * random.random() - 1) * speed_variation)
            
            # 运行一圈
            await self.run_one_round(dvt, loc, v_rand)
            
            if self.is_running:
                self.log_message("跑完一圈了")
                
    async def run_one_round(self, dvt, loc, v):
        """运行一圈"""
        import math
        import time
        import random
        
        # 导入必要的模块
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
        from run import bd09Towgs84, geodistance, smooth, randLoc, fixLockT
        
        dt = 0.2
        fixed_loc = fixLockT(loc, v, dt)
        n_list = (5, 6, 7, 8, 9)
        n = n_list[random.randint(0, len(n_list) - 1)]
        fixed_loc = randLoc(fixed_loc, n=n)
        
        clock = time.time()
        for i in fixed_loc:
            if not self.is_running:
                break
            LocationSimulation(dvt).set(*bd09Towgs84(i).values())
            while time.time() - clock < dt and self.is_running:
                await asyncio.sleep(0.01)
            clock = time.time()


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    # 创建应用
    app = iOSRealRunGUI(root)
    
    # 设置关闭事件
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "跑步模拟正在运行，确定要退出吗？"):
                app.stop_running()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行应用
    root.mainloop()


if __name__ == "__main__":
    main()
