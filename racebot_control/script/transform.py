#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist

class Transform(Node):
    def __init__(self):
        super().__init__('nav_sim')
        self.pub = self.create_publisher(AckermannDriveStamped, "/ackermann_cmd_mux/output", 1)
        self.create_subscription(Twist, 'cmd_vel', self.callback, 1)

    def callback(self, data):
        speed = data.linear.x 
        turn = data.angular.z

        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        msg.drive.speed = speed
        msg.drive.acceleration = 1.0
        msg.drive.jerk = 1.0
        msg.drive.steering_angle = turn
        msg.drive.steering_angle_velocity = 1.0

        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = Transform()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        pass
