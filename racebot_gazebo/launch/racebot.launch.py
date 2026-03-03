import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node

def generate_launch_description():
    pkg_racebot_gazebo = get_package_share_directory('racebot_gazebo')
    pkg_racebot_description = get_package_share_directory('racebot_description')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_put_model = get_package_share_directory('put_model')

    # Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pos = LaunchConfiguration('x_pos', default='3.0')
    y_pos = LaunchConfiguration('y_pos', default='-2.3')
    z_pos = LaunchConfiguration('z_pos', default='0.0')
    yaw = LaunchConfiguration('yaw', default='0.0')
    
    # World
    world_path = os.path.join(pkg_racebot_gazebo, 'worlds', 'race.world')

    # Add model path to env
    install_dir = get_package_share_directory('racebot_description')
    gazebo_model_path = os.path.dirname(install_dir)
    put_model_path = os.path.join(pkg_put_model, 'model')
    
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += ":" + os.path.join(pkg_racebot_gazebo, 'model') + ":" + gazebo_model_path + ":" + put_model_path
    else:
        os.environ['GAZEBO_MODEL_PATH'] = os.path.join(pkg_racebot_gazebo, 'model') + ":" + gazebo_model_path + ":" + put_model_path
        
    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_path}.items()
    )

    # Robot Description
    xacro_file = os.path.join(pkg_racebot_description, 'urdf', 'ackermann', 'racecar.xacro')
    robot_description = {'robot_description': Command(['xacro ', xacro_file])}

    # Spawn Entity
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'racebot',
            '-x', x_pos,
            '-y', y_pos,
            '-z', z_pos,
            '-Y', yaw
        ],
        output='screen'
    )
    
    # Robot State Publisher (Essential for Gazebo to know the robot structure via /robot_description)
    # The original racebot.launch did not explicitly run robot_state_publisher but it loaded robot_description.
    # In ROS 2, it is common to run RSP to publish the description to the topic.
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': use_sim_time}]
    )

    # Joint State Publisher
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Load controllers
    load_joint_state_broadcaster = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'joint_state_broadcaster'],
        output='screen'
    )

    load_left_rear_wheel_velocity_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'left_rear_wheel_velocity_controller'],
        output='screen'
    )

    load_right_rear_wheel_velocity_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'right_rear_wheel_velocity_controller'],
        output='screen'
    )

    load_left_front_wheel_velocity_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'left_front_wheel_velocity_controller'],
        output='screen'
    )

    load_right_front_wheel_velocity_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'right_front_wheel_velocity_controller'],
        output='screen'
    )

    load_left_steering_hinge_position_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'left_steering_hinge_position_controller'],
        output='screen'
    )

    load_right_steering_hinge_position_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'right_steering_hinge_position_controller'],
        output='screen'
    )

    # Racebot Control: bring up servo, cmd_vel->ackermann transform, and gazebo odometry (publishes /odom and TF)
    racebot_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('racebot_control'), 'launch', 'racebot_control.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )


    # RViz
    # rviz_config_file = os.path.join(pkg_racebot_description, 'rviz_config', 'racecar.rviz')
    # rviz_node = Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     name='rviz2',
    #     arguments=['-d', rviz_config_file],
    #     output='screen'
    # )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        joint_state_publisher,
        spawn_entity,
        load_joint_state_broadcaster,
        load_left_rear_wheel_velocity_controller,
        load_right_rear_wheel_velocity_controller,
        load_left_front_wheel_velocity_controller,
        load_right_front_wheel_velocity_controller,
        load_left_steering_hinge_position_controller,
        load_right_steering_hinge_position_controller,
        racebot_control_launch,
        # rviz_node
    ])
