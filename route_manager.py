import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class RouteManager:
    """路径管理器，支持多种格式的路径文件"""
    
    def __init__(self, routes_dir: str = "routes"):
        self.routes_dir = Path(routes_dir)
        self.routes_dir.mkdir(exist_ok=True)
        
    def save_route_json(self, route_name: str, coordinates: List[Dict], 
                       metadata: Optional[Dict] = None) -> str:
        """
        保存路径为JSON格式
        
        Args:
            route_name: 路径名称
            coordinates: 坐标列表 [{"lat": float, "lng": float}, ...]
            metadata: 元数据 {"description": str, "distance": float, "created": str}
            
        Returns:
            保存的文件路径
        """
        if not metadata:
            metadata = {}
            
        route_data = {
            "name": route_name,
            "coordinates": coordinates,
            "metadata": {
                "description": metadata.get("description", ""),
                "distance": metadata.get("distance", 0),
                "created": metadata.get("created", ""),
                "format": "json"
            }
        }
        
        # 确保路径名称安全（处理中文字符）
        safe_name = self._make_safe_filename(route_name)
        file_path = self.routes_dir / f"{safe_name}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(route_data, f, indent=2, ensure_ascii=False)
            
        return str(file_path)
        
    def load_route_json(self, file_path: str) -> Dict:
        """
        从JSON文件加载路径
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            路径数据字典
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def convert_txt_to_json(self, txt_file_path: str, route_name: str, 
                           description: str = "") -> str:
        """
        将现有的txt格式路径文件转换为JSON格式
        
        Args:
            txt_file_path: 原始txt文件路径
            route_name: 新路径名称
            description: 路径描述
            
        Returns:
            新JSON文件路径
        """
        # 读取原始txt文件
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # 解析坐标
        from util.route import parse_route
        coordinates = parse_route(content)
        
        # 计算距离
        distance = self.calculate_route_distance(coordinates)
        
        # 保存为JSON
        metadata = {
            "description": description,
            "distance": distance,
            "created": self._get_current_time(),
            "source": txt_file_path
        }
        
        return self.save_route_json(route_name, coordinates, metadata)
        
    def calculate_route_distance(self, coordinates: List[Dict]) -> float:
        """
        计算路径总距离（米）
        
        Args:
            coordinates: 坐标列表
            
        Returns:
            总距离（米）
        """
        if len(coordinates) < 2:
            return 0.0
            
        from geopy.distance import geodesic
        total_distance = 0.0
        
        for i in range(len(coordinates)):
            current = coordinates[i]
            next_coord = coordinates[(i + 1) % len(coordinates)]
            distance = geodesic((current["lat"], current["lng"]), 
                              (next_coord["lat"], next_coord["lng"])).meters
            total_distance += distance
            
        return total_distance
        
    def get_route_list(self) -> List[Dict]:
        """
        获取所有可用路径的列表
        
        Returns:
            路径信息列表
        """
        routes = []
        
        # 扫描JSON文件
        for json_file in self.routes_dir.glob("*.json"):
            try:
                route_data = self.load_route_json(str(json_file))
                routes.append({
                    "name": route_data["name"],
                    "file_path": str(json_file),
                    "format": "json",
                    "description": route_data["metadata"].get("description", ""),
                    "distance": route_data["metadata"].get("distance", 0),
                    "created": route_data["metadata"].get("created", ""),
                    "coordinates_count": len(route_data["coordinates"])
                })
            except Exception as e:
                print(f"加载路径文件 {json_file} 失败: {e}")
                
        # 扫描txt文件
        for txt_file in self.routes_dir.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                from util.route import parse_route
                coordinates = parse_route(content)
                distance = self.calculate_route_distance(coordinates)
                
                routes.append({
                    "name": txt_file.stem,
                    "file_path": str(txt_file),
                    "format": "txt",
                    "description": "传统格式路径文件",
                    "distance": distance,
                    "created": "",
                    "coordinates_count": len(coordinates)
                })
            except Exception as e:
                print(f"加载路径文件 {txt_file} 失败: {e}")
                
        return sorted(routes, key=lambda x: x["name"])
        
    def delete_route(self, file_path: str) -> bool:
        """
        删除路径文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否删除成功
        """
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"删除文件 {file_path} 失败: {e}")
            return False
            
    def export_route(self, file_path: str, export_path: str, format: str = "json") -> bool:
        """
        导出路径文件
        
        Args:
            file_path: 源文件路径
            export_path: 导出路径
            format: 导出格式 ("json" 或 "txt")
            
        Returns:
            是否导出成功
        """
        try:
            if file_path.endswith('.json'):
                route_data = self.load_route_json(file_path)
                coordinates = route_data["coordinates"]
            else:
                # txt格式
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                from util.route import parse_route
                coordinates = parse_route(content)
                
            if format == "json":
                if not file_path.endswith('.json'):
                    # 需要转换
                    route_name = Path(file_path).stem
                    metadata = {"description": "导出的路径", "created": self._get_current_time()}
                    route_data = {
                        "name": route_name,
                        "coordinates": coordinates,
                        "metadata": metadata
                    }
                else:
                    route_data = self.load_route_json(file_path)
                    
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(route_data, f, indent=2, ensure_ascii=False)
            else:
                # 导出为txt格式
                content = ""
                for coord in coordinates:
                    content += f'{{"lng":"{coord["lng"]}","lat":"{coord["lat"]}"}},'
                content = content.rstrip(',')
                
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            return True
        except Exception as e:
            print(f"导出文件失败: {e}")
            return False
            
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _make_safe_filename(self, filename: str) -> str:
        """创建安全的文件名，支持中文字符"""
        import re
        # 移除或替换不安全的字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 确保文件名不为空
        if not safe_name.strip():
            safe_name = "untitled"
        return safe_name


class RouteManagerGUI:
    """路径管理器GUI界面"""
    
    def __init__(self, parent=None):
        self.route_manager = RouteManager()
        self.parent = parent
        
    def show_route_manager(self):
        """显示路径管理器窗口"""
        if self.parent:
            window = tk.Toplevel(self.parent)
        else:
            window = tk.Tk()
            
        window.title("路径管理器")
        window.geometry("800x600")
        
        # 创建主框架
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="路径管理器", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_route_list).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="导入路径", command=self.import_route).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="转换格式", command=self.convert_format).pack(side=tk.LEFT, padx=(0, 10))
        
        # 路径列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("名称", "格式", "描述", "距离", "坐标数", "创建时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "描述":
                self.tree.column(col, width=200)
            elif col == "距离":
                self.tree.column(col, width=100)
            elif col == "坐标数":
                self.tree.column(col, width=80)
            elif col == "创建时间":
                self.tree.column(col, width=150)
            else:
                self.tree.column(col, width=120)
                
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self.context_menu = tk.Menu(window, tearoff=0)
        self.context_menu.add_command(label="删除", command=self.delete_selected_route)
        self.context_menu.add_command(label="导出", command=self.export_selected_route)
        self.context_menu.add_command(label="查看详情", command=self.view_route_details)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.select_route)
        
        # 加载路径列表
        self.refresh_route_list()
        
        return window
        
    def refresh_route_list(self):
        """刷新路径列表"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 加载路径
        routes = self.route_manager.get_route_list()
        for route in routes:
            distance_text = f"{route['distance']:.1f}m" if route['distance'] > 0 else "未知"
            created_text = route['created'] if route['created'] else "未知"
            
            self.tree.insert("", tk.END, values=(
                route['name'],
                route['format'].upper(),
                route['description'],
                distance_text,
                route['coordinates_count'],
                created_text
            ), tags=(route['file_path'],))
            
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.context_menu.post(event.x_root, event.y_root)
            
    def delete_selected_route(self):
        """删除选中的路径"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.tree.item(item, "tags")[0]
        route_name = self.tree.item(item, "values")[0]
        
        if messagebox.askyesno("确认删除", f"确定要删除路径 '{route_name}' 吗？"):
            if self.route_manager.delete_route(file_path):
                messagebox.showinfo("成功", "路径已删除")
                self.refresh_route_list()
            else:
                messagebox.showerror("错误", "删除失败")
                
    def export_selected_route(self):
        """导出选中的路径"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.tree.item(item, "tags")[0]
        route_name = self.tree.item(item, "values")[0]
        
        # 选择导出格式
        format_dialog = tk.Toplevel()
        format_dialog.title("选择导出格式")
        format_dialog.geometry("300x150")
        format_dialog.transient()
        format_dialog.grab_set()
        
        ttk.Label(format_dialog, text="选择导出格式:").pack(pady=10)
        
        format_var = tk.StringVar(value="json")
        ttk.Radiobutton(format_dialog, text="JSON格式", variable=format_var, value="json").pack()
        ttk.Radiobutton(format_dialog, text="TXT格式", variable=format_var, value="txt").pack()
        
        def do_export():
            format_dialog.destroy()
            filetypes = [("JSON文件", "*.json"), ("文本文件", "*.txt")] if format_var.get() == "json" else [("文本文件", "*.txt"), ("JSON文件", "*.json")]
            export_path = filedialog.asksaveasfilename(
                title="保存路径文件",
                defaultextension=f".{format_var.get()}",
                filetypes=filetypes,
                initialvalue=f"{route_name}.{format_var.get()}"
            )
            if export_path:
                if self.route_manager.export_route(file_path, export_path, format_var.get()):
                    messagebox.showinfo("成功", "路径已导出")
                else:
                    messagebox.showerror("错误", "导出失败")
                    
        ttk.Button(format_dialog, text="导出", command=do_export).pack(pady=10)
        
    def view_route_details(self):
        """查看路径详情"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.tree.item(item, "tags")[0]
        
        try:
            if file_path.endswith('.json'):
                route_data = self.route_manager.load_route_json(file_path)
                details = f"名称: {route_data['name']}\n"
                details += f"坐标数量: {len(route_data['coordinates'])}\n"
                details += f"描述: {route_data['metadata'].get('description', '无')}\n"
                details += f"距离: {route_data['metadata'].get('distance', 0):.1f}米\n"
                details += f"创建时间: {route_data['metadata'].get('created', '未知')}\n"
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                from util.route import parse_route
                coordinates = parse_route(content)
                distance = self.route_manager.calculate_route_distance(coordinates)
                details = f"名称: {Path(file_path).stem}\n"
                details += f"坐标数量: {len(coordinates)}\n"
                details += f"距离: {distance:.1f}米\n"
                details += f"格式: 传统TXT格式\n"
                
            messagebox.showinfo("路径详情", details)
        except Exception as e:
            messagebox.showerror("错误", f"读取路径详情失败: {e}")
            
    def select_route(self, event):
        """选择路径（双击）"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.tree.item(item, "tags")[0]
        
        # 如果有关联的父窗口，设置路径文件
        if self.parent and hasattr(self.parent, 'route_file_var'):
            self.parent.route_file_var.set(file_path)
            messagebox.showinfo("成功", f"已选择路径: {Path(file_path).name}")
            
    def import_route(self):
        """导入路径文件"""
        filetypes = [
            ("所有支持的文件", "*.txt;*.json"),
            ("文本文件", "*.txt"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择要导入的路径文件",
            filetypes=filetypes
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    # JSON文件直接复制
                    route_data = self.route_manager.load_route_json(file_path)
                    route_name = route_data['name']
                    new_path = self.route_manager.routes_dir / f"{route_name}.json"
                    
                    import shutil
                    shutil.copy2(file_path, new_path)
                    messagebox.showinfo("成功", f"路径 '{route_name}' 已导入")
                else:
                    # TXT文件转换为JSON
                    route_name = Path(file_path).stem
                    description = f"从 {Path(file_path).name} 导入"
                    new_path = self.route_manager.convert_txt_to_json(file_path, route_name, description)
                    messagebox.showinfo("成功", f"路径 '{route_name}' 已导入并转换为JSON格式")
                    
                self.refresh_route_list()
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")
                
    def convert_format(self):
        """转换格式"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个路径")
            return
            
        item = selection[0]
        file_path = self.tree.item(item, "tags")[0]
        route_name = self.tree.item(item, "values")[0]
        
        if file_path.endswith('.json'):
            # JSON转TXT
            export_path = filedialog.asksaveasfilename(
                title="保存为TXT格式",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt")],
                initialvalue=f"{route_name}.txt"
            )
            if export_path:
                if self.route_manager.export_route(file_path, export_path, "txt"):
                    messagebox.showinfo("成功", "已转换为TXT格式")
                else:
                    messagebox.showerror("错误", "转换失败")
        else:
            # TXT转JSON
            description = f"从 {Path(file_path).name} 转换"
            new_path = self.route_manager.convert_txt_to_json(file_path, route_name, description)
            messagebox.showinfo("成功", f"已转换为JSON格式: {Path(new_path).name}")
            self.refresh_route_list()


if __name__ == "__main__":
    # 测试路径管理器
    manager = RouteManager()
    
    # 转换现有文件
    if os.path.exists("YQroute.txt"):
        new_path = manager.convert_txt_to_json("YQroute.txt", "YQ_route", "YQ跑步路径")
        print(f"已转换: {new_path}")
        
    # 显示路径列表
    routes = manager.get_route_list()
    print("可用路径:")
    for route in routes:
        print(f"  {route['name']} ({route['format']}) - {route['distance']:.1f}m")
