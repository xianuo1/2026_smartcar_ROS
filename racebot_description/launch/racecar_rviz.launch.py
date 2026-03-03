import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('racebot_description')
    
    # Locate the Rviz configuration file
    rviz_config_file = os.path.join(pkg_share, 'rviz_config', 'racecar.rviz')
    
    # Locate the URDF/Xacro file
    # Note: The original launch used urdf/racebot.urdf, but the prompt asked to use Command to process xacro.
    # Checking existing file list, there is a urdf folder.
    # Typically it's xacro file. Let's assume urdf/ackermann/racecar.xacro based on gazebo launch file usage
    # or just urdf/racebot.urdf if it is a pure urdf but user asked for xacro command.
    # Accessing the previous read file content of racebot_gazebo launch file: 
    # <param name="robot_description" command="$(find xacro)/xacro --inorder '$(find racebot_description)/urdf/ackermann/racecar.xacro'"/>
    # So the main xacro seems to be urdf/ackermann/racecar.xacro
    
    xacro_file = os.path.join(pkg_share, 'urdf', 'ackermann', 'racecar.xacro')

    robot_description = {'robot_description': Command(['xacro ', xacro_file])}

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[robot_description]
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        )
    ])
