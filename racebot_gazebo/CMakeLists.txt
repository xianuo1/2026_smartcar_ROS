cmake_minimum_required(VERSION 3.8)
project(racebot_gazebo)

# check if we have any cpp code, if not, we only need rclpy and messages.
# The user mentioned roscpp but I see scripts only.
# I will use ament_cmake for general ROS 2 structure.

find_package(ament_cmake REQUIRED)
find_package(gazebo_ros_pkgs REQUIRED)

# Install directories
install(DIRECTORY launch config map model worlds
  DESTINATION share/${PROJECT_NAME}
)

# Install programs (scripts)
install(PROGRAMS
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
