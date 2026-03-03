import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('racebot_control') # Not used yet but good to have

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    servo_commands_node = Node(
        package='racebot_control',
        executable='servo_commands.py',
        name='servo_commands',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    transform_node = Node(
        package='racebot_control',
        executable='transform.py',
        name='transform',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # Wheel Odometry Node (Computes coarse odom from wheel encoders)
    wheel_odom_node = Node(
        package='racebot_control',
        executable='wheel_odom.py',
        name='wheel_odometry_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # Robot Localization EKF Node (Fuses Wheel Odom + IMU -> Odom TF)
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf.yaml')
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            ekf_config_path, 
            {'use_sim_time': use_sim_time}
        ],
        remappings=[('odometry/filtered', 'odom')]
    )

    ld = LaunchDescription()
    ld.add_action(servo_commands_node)
    ld.add_action(transform_node)
    ld.add_action(wheel_odom_node)
    ld.add_action(ekf_node)
    
    return ld
