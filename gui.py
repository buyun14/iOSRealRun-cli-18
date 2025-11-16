import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import asyncio
import os
import signal
import logging
import coloredlogs
import json
from pathlib import Path
from datetime import datetime

from init import init
from init import tunnel
from init import route
import run
import config
from route_manager import RouteManager, RouteManagerGUI

# 设置 CustomTkinter 外观模式
ctk.set_appearance_mode("dark")  # 可选: "light", "dark", "system"
ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"

# 定义两套配色方案
THEME_COLORS = {
    "dark": {
        "bg": "#1a1a1a",
        "fg": "#2b2b2b",
        "border": "#3a3a3a",
        "text": "#ffffff",
        "text_secondary": "#b0b0b0",
        "accent": "#1f6aa5",
        "success": "#2fa572",
        "danger": "#d32f2f",
        "card_bg": "#242424",
        "card_border": "#3a3a3a"
    },
    "light": {
        "bg": "#f0f0f0",
        "fg": "#ffffff",
        "border": "#d0d0d0",
        "text": "#1a1a1a",
        "text_secondary": "#666666",
        "accent": "#1f6aa5",
        "success": "#2fa572",
        "danger": "#d32f2f",
        "card_bg": "#ffffff",
        "card_border": "#d0d0d0"
    }
}


class iOSRealRunGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("iOS Real Run - 跑步模拟器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 运行状态
        self.is_running = False
        self.tunnel_process = None
        self.tunnel_address = None
        self.tunnel_port = None
        
        # 主题状态
        self.current_theme = "dark"
        self.theme_colors = THEME_COLORS["dark"]
        
        # 路径管理器
        self.route_manager = RouteManager()
        self.route_manager_gui = RouteManagerGUI(root)
        
        # 自动保存定时器
        self.auto_save_timer = None
        
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
        """创建GUI组件 - 使用卡片式布局"""
        # 主容器
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 顶部标题栏
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🏃 iOS Real Run - 跑步模拟器",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left")
        
        # 状态指示器和主题切换（右侧）
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.pack(side="right")
        
        # 主题切换按钮
        current_mode = ctk.get_appearance_mode()
        theme_icon = "☀️" if current_mode == "dark" else "🌙"
        self.theme_button = ctk.CTkButton(
            status_frame,
            text=theme_icon,
            command=self.toggle_theme,
            width=40,
            height=30,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=("gray70", "gray30")
        )
        self.theme_button.pack(side="left", padx=(0, 15))
        
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.status_indicator.pack(side="left", padx=(0, 10))
        
        self.status_var = ctk.StringVar(value="就绪")
        self.status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left")
        
        # 主要内容区域 - 使用两列布局
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # 左列：配置卡片
        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 路径配置卡片（增强边框）
        route_card = ctk.CTkFrame(left_column, border_width=2, border_color=THEME_COLORS[self.current_theme]["card_border"])
        route_card.pack(fill="x", pady=(0, 15))
        self.route_card = route_card  # 保存引用以便主题切换时更新
        
        ctk.CTkLabel(
            route_card,
            text="📍 路径配置",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(15, 10), padx=20)
        
        # 路径文件选择
        route_input_frame = ctk.CTkFrame(route_card, fg_color="transparent")
        route_input_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.route_file_var = ctk.StringVar()
        self.route_file_entry = ctk.CTkEntry(
            route_input_frame,
            textvariable=self.route_file_var,
            placeholder_text="选择路径文件...",
            height=35
        )
        self.route_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        route_button_frame = ctk.CTkFrame(route_input_frame, fg_color="transparent")
        route_button_frame.pack(side="right")
        
        ctk.CTkButton(
            route_button_frame,
            text="浏览",
            command=self.browse_route_file,
            width=80,
            height=35
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            route_button_frame,
            text="管理",
            command=self.open_route_manager,
            width=80,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side="left")
        
        # 速度设置卡片（可折叠，增强边框）
        speed_card = ctk.CTkFrame(left_column, border_width=2, border_color=THEME_COLORS[self.current_theme]["card_border"])
        speed_card.pack(fill="x", pady=(0, 15))
        self.speed_card = speed_card  # 保存引用以便主题切换时更新
        
        # 速度设置标题栏（可点击折叠）
        speed_header = ctk.CTkFrame(speed_card, fg_color="transparent")
        speed_header.pack(fill="x", padx=20, pady=(15, 0))
        
        self.speed_expanded = ctk.BooleanVar(value=False)  # 默认折叠
        
        speed_title_frame = ctk.CTkFrame(speed_header, fg_color="transparent")
        speed_title_frame.pack(side="left", fill="x", expand=True)
        
        speed_title_frame.bind("<Button-1>", lambda e: self.toggle_speed_settings())
        for widget in speed_title_frame.winfo_children():
            widget.bind("<Button-1>", lambda e: self.toggle_speed_settings())
        
        self.speed_toggle_label = ctk.CTkLabel(
            speed_title_frame,
            text="▶ ⚡ 速度设置",  # 默认折叠，显示▶
            font=ctk.CTkFont(size=16, weight="bold"),
            cursor="hand2"
        )
        self.speed_toggle_label.pack(side="left")
        self.speed_toggle_label.bind("<Button-1>", lambda e: self.toggle_speed_settings())
        
        # 速度设置内容区域（可折叠，默认隐藏）
        self.speed_content_frame = ctk.CTkFrame(speed_card, fg_color="transparent")
        # 默认不显示（折叠状态）
        
        # 跑步速度
        speed_setting_frame = ctk.CTkFrame(self.speed_content_frame, fg_color="transparent")
        speed_setting_frame.pack(fill="x", pady=(0, 10))
        
        speed_label_frame = ctk.CTkFrame(speed_setting_frame, fg_color="transparent")
        speed_label_frame.pack(fill="x", pady=(0, 6))
        
        ctk.CTkLabel(
            speed_label_frame,
            text="跑步速度:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left")
        
        self.speed_var = ctk.DoubleVar(value=4.2)
        self.speed_value_label = ctk.CTkLabel(
            speed_label_frame,
            text="4.2 m/s",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1f6aa5"
        )
        self.speed_value_label.pack(side="right")
        
        self.speed_slider = ctk.CTkSlider(
            speed_setting_frame,
            from_=1.0,
            to=10.0,
            variable=self.speed_var,
            command=self.update_speed_label,
            height=18
        )
        self.speed_slider.pack(fill="x")
        
        speed_range_frame = ctk.CTkFrame(speed_setting_frame, fg_color="transparent")
        speed_range_frame.pack(fill="x", pady=(3, 0))
        
        ctk.CTkLabel(
            speed_range_frame,
            text="1.0",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        ).pack(side="left")
        
        ctk.CTkLabel(
            speed_range_frame,
            text="10.0",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        ).pack(side="right")
        
        # 速度变化范围
        variation_setting_frame = ctk.CTkFrame(self.speed_content_frame, fg_color="transparent")
        variation_setting_frame.pack(fill="x", pady=(0, 0))
        
        variation_label_frame = ctk.CTkFrame(variation_setting_frame, fg_color="transparent")
        variation_label_frame.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            variation_label_frame,
            text="速度变化范围:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left")
        
        self.speed_variation_var = ctk.IntVar(value=15)
        self.variation_value_label = ctk.CTkLabel(
            variation_label_frame,
            text="15%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1f6aa5"
        )
        self.variation_value_label.pack(side="right")
        
        self.variation_slider = ctk.CTkSlider(
            variation_setting_frame,
            from_=0,
            to=50,
            variable=self.speed_variation_var,
            command=self.update_variation_label,
            height=18
        )
        self.variation_slider.pack(fill="x")
        
        variation_range_frame = ctk.CTkFrame(variation_setting_frame, fg_color="transparent")
        variation_range_frame.pack(fill="x", pady=(3, 0))
        
        ctk.CTkLabel(
            variation_range_frame,
            text="0%",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        ).pack(side="left")
        
        ctk.CTkLabel(
            variation_range_frame,
            text="50%",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        ).pack(side="right")
        
        # 右列：控制按钮
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=False, padx=(10, 0))
        
        # 控制按钮卡片（增强边框）
        control_card = ctk.CTkFrame(right_column, border_width=2, border_color=THEME_COLORS[self.current_theme]["card_border"])
        control_card.pack(fill="x", pady=(0, 15))
        self.control_card = control_card  # 保存引用以便主题切换时更新
        
        ctk.CTkLabel(
            control_card,
            text="🎮 控制面板",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(15, 10), padx=20)
        
        # 主要控制按钮 - 2x2 网格布局
        button_container = ctk.CTkFrame(control_card, fg_color="transparent")
        button_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # 配置网格权重
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        button_container.grid_rowconfigure(0, weight=1)
        button_container.grid_rowconfigure(1, weight=1)
        
        # 第一行：开始和停止按钮
        self.start_button = ctk.CTkButton(
            button_container,
            text="▶ 开始",
            command=self.start_running,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2fa572",
            hover_color="#228b63"
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky="nsew")
        
        self.stop_button = ctk.CTkButton(
            button_container,
            text="⏹ 停止",
            command=self.stop_running,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(5, 0), pady=(0, 5), sticky="nsew")
        
        # 第二行：保存配置和路径管理按钮
        save_button = ctk.CTkButton(
            button_container,
            text="💾 保存",
            command=self.save_config,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="darkgray"
        )
        save_button.grid(row=1, column=0, padx=(0, 5), pady=(5, 0), sticky="nsew")
        
        route_button = ctk.CTkButton(
            button_container,
            text="📁 管理",
            command=self.open_route_manager,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="darkgray"
        )
        route_button.grid(row=1, column=1, padx=(5, 0), pady=(5, 0), sticky="nsew")
        
        # 底部日志区域（增大占比，增强边框）
        log_card = ctk.CTkFrame(main_container, border_width=2, border_color=THEME_COLORS[self.current_theme]["card_border"])
        log_card.pack(fill="both", expand=True, pady=(15, 0))
        self.log_card = log_card  # 保存引用以便主题切换时更新
        
        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            log_header,
            text="📋 运行日志",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # 日志文本框（增大高度）
        log_container = ctk.CTkFrame(log_card, fg_color="transparent")
        log_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.log_text = ctk.CTkTextbox(
            log_container,
            height=300,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        
    def update_speed_label(self, value):
        """更新速度标签"""
        speed = float(value)
        self.speed_value_label.configure(text=f"{speed:.1f} m/s")
        # 自动保存配置（延迟保存，避免频繁写入）
        self.auto_save_config()
        
    def update_variation_label(self, value):
        """更新变化范围标签"""
        variation = int(float(value))
        self.variation_value_label.configure(text=f"{variation}%")
        # 自动保存配置（延迟保存，避免频繁写入）
        self.auto_save_config()
        
    def toggle_speed_settings(self):
        """切换速度设置区域的显示/隐藏"""
        if self.speed_expanded.get():
            self.speed_content_frame.pack_forget()
            self.speed_toggle_label.configure(text="▶ ⚡ 速度设置")
            self.speed_expanded.set(False)
        else:
            self.speed_content_frame.pack(fill="x", padx=20, pady=(10, 15))
            self.speed_toggle_label.configure(text="▼ ⚡ 速度设置")
            self.speed_expanded.set(True)
            
    def toggle_theme(self):
        """切换亮暗模式 - 手动实现配色切换"""
        if self.current_theme == "dark":
            self.current_theme = "light"
            new_icon = "🌙"
        else:
            self.current_theme = "dark"
            new_icon = "☀️"
        
        # 更新主题颜色
        self.theme_colors = THEME_COLORS[self.current_theme]
        
        # 设置 CustomTkinter 主题
        ctk.set_appearance_mode(self.current_theme)
        
        # 更新按钮图标
        self.theme_button.configure(text=new_icon)
        
        # 更新所有卡片的边框颜色
        self._update_theme_colors()
        
        # 强制更新所有窗口
        self.root.update_idletasks()
        self.root.update()
        
    def _update_theme_colors(self):
        """更新所有组件的主题颜色"""
        # 更新所有卡片的边框颜色
        border_color = self.theme_colors["card_border"]
        if hasattr(self, 'route_card'):
            self.route_card.configure(border_color=border_color)
        if hasattr(self, 'speed_card'):
            self.speed_card.configure(border_color=border_color)
        if hasattr(self, 'control_card'):
            self.control_card.configure(border_color=border_color)
        if hasattr(self, 'log_card'):
            self.log_card.configure(border_color=border_color)
        
    def browse_route_file(self):
        """浏览路径文件"""
        filetypes = [
            ("所有支持的文件", "*.txt;*.json"),
            ("文本文件", "*.txt"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        try:
            filename = filedialog.askopenfilename(
                title="选择路径文件",
                filetypes=filetypes,
                initialdir=os.getcwd()
            )
            if filename:
                self.route_file_var.set(filename)
                self.log_message(f"已选择路径文件: {Path(filename).name}")
                # 自动保存配置
                self.auto_save_config()
        except Exception as e:
            self.log_message(f"选择文件时出错: {e}")
            messagebox.showerror("错误", f"选择文件时出错: {e}")
            
    def open_route_manager(self):
        """打开路径管理器"""
        self.route_manager_gui.show_route_manager()
        
    def _get_current_time(self):
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
                self.update_speed_label(config.config.v)
                
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
            
    def save_config(self, silent=False):
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
                
            if not silent:
                self.log_message("配置已保存")
                messagebox.showinfo("成功", "配置已保存到 config.yaml")
            else:
                self.log_message("配置已自动保存")
            
        except Exception as e:
            self.log_message(f"保存配置失败: {e}")
            if not silent:
                messagebox.showerror("错误", f"保存配置失败: {e}")
                
    def auto_save_config(self):
        """自动保存配置（延迟保存，避免频繁写入）"""
        # 取消之前的定时器
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
        
        # 设置新的定时器，1秒后保存
        self.auto_save_timer = self.root.after(1000, lambda: self.save_config(silent=True))
            
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()
        
    def update_status(self, status, color="gray"):
        """更新状态显示"""
        self.status_var.set(status)
        self.status_indicator.configure(text_color=color)
        
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
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.update_status("正在启动...", "orange")
        
        # 在新线程中运行
        self.running_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.running_thread.start()
        
    def stop_running(self):
        """停止跑步模拟"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.update_status("正在停止...", "orange")
        
        # 终止隧道进程
        if self.tunnel_process and self.tunnel_process.is_alive():
            self.tunnel_process.terminate()
            self.log_message("隧道进程已终止")
            
        # 更新UI状态
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_status("已停止", "red")
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
                # 传统txt格式 - 自动转换为JSON
                self.log_message(f"检测到TXT格式路径文件，正在自动转换...")
                try:
                    # 读取TXT文件内容
                    with open(route_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    # 解析坐标
                    from util.route import parse_route
                    coordinates = parse_route(content)
                    
                    # 生成JSON文件名
                    txt_path = Path(route_file)
                    json_name = f"{txt_path.stem}_converted"
                    json_path = self.route_manager.routes_dir / f"{json_name}.json"
                    
                    # 计算距离
                    distance = self.route_manager.calculate_route_distance(coordinates)
                    
                    # 创建元数据
                    metadata = {
                        "description": f"从 {txt_path.name} 自动转换",
                        "distance": distance,
                        "created": self._get_current_time(),
                        "source": str(route_file),
                        "format": "json"
                    }
                    
                    # 保存为JSON
                    route_data = {
                        "name": json_name,
                        "coordinates": coordinates,
                        "metadata": metadata
                    }
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(route_data, f, indent=2, ensure_ascii=False)
                    
                    self.log_message(f"已自动转换为JSON格式: {json_path.name}")
                    self.log_message(f"路径距离: {distance:.1f}米")
                    
                    # 使用转换后的JSON文件
                    loc = coordinates
                    
                except Exception as e:
                    self.log_message(f"自动转换失败，使用原始TXT格式: {e}")
                    # 回退到原始方式
                    original_route_config = config.config.routeConfig
                    config.config.routeConfig = route_file
                    
                    loc = route.get_route()
                    self.log_message(f"从TXT文件 {route_file} 获取路径")
                    
                    # 恢复原始配置
                    config.config.routeConfig = original_route_config
            
            # 更新状态
            self.update_status("正在跑步...", "green")
            self.log_message(f"已开始模拟跑步，速度大约为 {self.speed_var.get()} m/s")
            self.log_message("会无限循环，点击停止按钮退出")
            self.log_message("请勿直接关闭窗口，否则无法还原正常定位")
            
            # 运行模拟
            speed_variation = self.speed_variation_var.get()
            asyncio.run(self.run_async(loc, self.speed_var.get(), speed_variation))
            
        except Exception as e:
            self.log_message(f"运行出错: {e}")
            self.update_status("运行出错", "red")
        finally:
            # 清理
            if self.tunnel_process and self.tunnel_process.is_alive():
                self.tunnel_process.terminate()
                self.log_message("隧道进程已终止")
                
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.update_status("已停止", "red")
            
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
    root = ctk.CTk()
    
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
