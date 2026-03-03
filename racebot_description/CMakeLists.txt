cmake_minimum_required(VERSION 3.8)
project(racebot_description)

find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)

# Install directories
install(DIRECTORY launch meshes rviz_config urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
