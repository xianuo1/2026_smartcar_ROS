cmake_minimum_required(VERSION 3.8)
project(put_model)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-style=c++17 -Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(gazebo_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

install(DIRECTORY scripts
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY model
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY map_picture
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
