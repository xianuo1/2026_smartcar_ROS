# 2026_smartcar_ROS
## 1. 安装必要依赖

### 1.1 安装 ROS 2 
安装ROS可以通过鱼香ROS一键安装、换源
```bash
wget http://fishros.com/install -O fishros && . fishros
```

### 1.2 安装本工程所需 ROS 依赖

本项目主要依赖如下 ROS 包：

```bash
sudo apt install \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-ackermann-msgs \
  ros-humble-urdf \
  ros-humble-xacro \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-ament-index-python
```



---

## 2. 使用 colcon 编译工作空间

1. 进入工作空间根目录（当前目录就是 `2026_smartcar_ROS`）：

	```bash
	cd ~/2026_smartcar_ROS   # 按实际路径修改
	```

2. 使用 `colcon` 编译整个工作空间：

	```bash
	colcon build 
	```

3. 编译成功后，source 本工作空间的覆盖层环境：

	```bash
	source install/setup.bash
	```


## 3. 启动 Gazebo 仿真

在已经 source 了工作空间环境的终端中（确保第 2 步的 `source install/setup.bash` 已执行），运行：

```bash
ros2 launch racebot_gazebo racebot.launch.py
```


如果需要多终端调试（例如再打开 RViz2 或其他节点），请在新开的每个终端中都执行source：

```bash
source ~/2026_smartcar_ROS/install/setup.bash
```

之后即可根据需要使用 `ros2 topic list`、`ros2 node list` 等命令进行查看和调试。

