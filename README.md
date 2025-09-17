# iOSRealRun-cli-18

本项目基于 [iOSRealRun-cli-17](https://github.com/iOSRealRun/iOSRealRun-cli-17) 修改而来，并更新了依赖的 [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)。

如果使用时出现了无法解决的报错可以考虑使用[这个仓库手动启动](https://github.com/BiancoChiu/iOSEasyRun)。

测试环境：
- 操作系统：MacOS，Windows11
- Python版本：3.13
- iOS版本：18.3.1

## 用法简介

### 前置条件

1. 系统是 `Windows` 或 `MacOS`
2. iPhone 或 iPad 系统版本大于等于 18（也许17的一些后期版本也可以用，未经测试）
3. Windows 需要安装 iTunes
4. 已安装 `Python3` 和 `pip3`
5. **重要**: 只能有一台 iPhone 或 iPad 连接到电脑，否则会出问题

### 启动方式

本项目现在支持两种使用方式：

#### 方式一：GUI界面（推荐）

1. 克隆本项目到本地并进入项目目录
2. 安装依赖（建议使用虚拟环境）  
    ```shell
    pip3 install -r requirements.txt
    ```
    如果 `pip3` 无法安装，请使用 `pip` 替代  
    如果提示没有需要的版本，请尝试不适用国内源  

3. 将设备连接到电脑，解锁，如果请求信任的提示框，请点击信任
4. 打开终端（cmd 或 PowerShell），执行以下命令获取DDI
    ```shell
    pymobiledevice3 mounter auto-mount
    ```
5. Windows **以管理员身份** 打开终端（cmd 或 PowerShell），先进入项目目录，然后执行以下命令 
    ```shell
    python start.py --gui
    ```
    或者直接运行：
    ```shell
    python start.py
    ```
    MacOS 打开终端，先进入项目目录，然后执行以下命令  
    ```shell
    sudo python3 start.py --gui
    ```

#### 方式二：命令行界面

1. 按照上述步骤1-4进行准备
2. Windows **以管理员身份** 打开终端，执行：
    ```shell
    python start.py --cli
    ```
    或者直接运行：
    ```shell
    python main.py
    ```
    MacOS 打开终端，执行：
    ```shell
    sudo python3 start.py --cli
    ```

### GUI界面功能

- **路径管理**: 支持导入、导出、转换路径文件格式
- **可视化配置**: 通过滑块调整跑步速度和速度变化范围
- **实时日志**: 显示运行状态和详细日志信息
- **一键操作**: 开始/停止跑步模拟，保存配置
- **路径预览**: 查看路径详情，包括距离、坐标数量等

### 路径文件格式

项目现在支持两种路径文件格式：

1. **传统TXT格式**: 兼容原有格式
2. **JSON格式**: 新增格式，包含更多元数据信息
   ```json
   {
     "name": "路径名称",
     "coordinates": [
       {"lat": 34.03866879243831, "lng": 108.76749520056279},
       {"lat": 34.03879219143184, "lng": 108.76790392956984}
     ],
     "metadata": {
       "description": "路径描述",
       "distance": 1000.5,
       "created": "2025-01-09 12:00:00"
     }
   }
   ```

### 使用步骤

1. 启动程序后，在GUI界面中选择路径文件
2. 调整跑步速度和速度变化范围
3. 点击"开始跑步"按钮
4. 程序会自动初始化设备连接并开始模拟
5. 使用"停止跑步"按钮安全退出
6. 可以通过"路径管理"按钮管理路径文件

### 自定义配置文件

- 若希望修改速度，请在 config.yaml 中修改 v
    - 默认的 `4.2 m/s`，就是大约 `4 min/km` 的水平
- 若需修改配置文件，请在 config.yaml 中修改 routeConfig
