#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SpawnEntity
from geometry_msgs.msg import Pose
import os

class SpawnModelNode(Node):
    def __init__(self):
        super().__init__('spawn_model_node')
        self.cli = self.create_client(SpawnEntity, '/spawn_entity')
        # Wait for service
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service /spawn_entity not available, waiting again...')
        
        self.req = SpawnEntity.Request()

    def send_request(self):
        # We need to find the model path. 
        # In ROS 2, if installed, we should look in share.
        # But this script seems to rely on relative SRC path in original code.
        # "src/PutModel/model/construction_cone_red/model.sdf"
        
        # We'll try to find it relative to current execution or properly located.
        # Assuming we run this from workspace root or where src is visible?
        # A better way is to use ament_index_python but let's try to be robust.
        
        model_path = "src/RosRaceCar/putModel/model/construction_cone_red/model.sdf"
        # Check if file exists, if not try absolute path or share
        if not os.path.exists(model_path):
             # Try share directory if installed
             from ament_index_python.packages import get_package_share_directory
             try:
                 pkg_share = get_package_share_directory('putModel')
                 model_path = os.path.join(pkg_share, 'model', 'construction_cone_red', 'model.sdf')
             except:
                 self.get_logger().error("Could not find model file")
                 return
        
        try:
            with open(model_path, "r") as f:
                model_xml = f.read()
        except FileNotFoundError:
            self.get_logger().error(f"Model file not found at {model_path}")
            return

        self.req.name = "my_model"
        self.req.xml = model_xml
        self.req.robot_namespace = ""
        self.req.initial_pose = Pose()
        self.req.initial_pose.position.x = 1.0
        self.req.initial_pose.position.y = 0.0
        self.req.initial_pose.position.z = 0.0
        
        # Async call
        self.future = self.cli.call_async(self.req)

def main(args=None):
    rclpy.init(args=args)
    spawn_model_node = SpawnModelNode()
    
    spawn_model_node.send_request()

    while rclpy.ok():
        rclpy.spin_once(spawn_model_node)
        if spawn_model_node.future.done():
            try:
                response = spawn_model_node.future.result()
            except Exception as e:
                spawn_model_node.get_logger().info(
                    'Service call failed %r' % (e,))
            else:
                spawn_model_node.get_logger().info(
                    f'Spawn status: {response.status_message}')
            break

    spawn_model_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
