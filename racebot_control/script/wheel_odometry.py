#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistWithCovarianceStamped
from sensor_msgs.msg import JointState
import math

class WheelOdometryNode(Node):
    def __init__(self):
        super().__init__('wheel_odometry_node')
        
        # Parameters
        self.wheel_radius = 0.033 # From URDF
        # Distance between rear wheels could be approximated
        self.track_width = 0.13 # Approximate from URDF visual/joint origins

        self.last_time = self.get_clock().now()
        
        self.pub_ohm = self.create_publisher(TwistWithCovarianceStamped, '/wheel/odom', 10)
        self.sub_joint = self.create_subscription(JointState, '/racebot/joint_states', self.joint_callback, 10)

        # To store verify velocity indices
        self.left_rear_idx = -1
        self.right_rear_idx = -1

    def joint_callback(self, msg):
        try:
            if self.left_rear_idx == -1 or self.right_rear_idx == -1:
                if 'left_rear_wheel_joint' in msg.name and 'right_rear_wheel_joint' in msg.name:
                     self.left_rear_idx = msg.name.index('left_rear_wheel_joint')
                     self.right_rear_idx = msg.name.index('right_rear_wheel_joint')
                else: 
                     return

            # Read wheel velocities (rad/s)
            wl = msg.velocity[self.left_rear_idx]
            wr = msg.velocity[self.right_rear_idx]

            # Compute linear velocity v = (vl + vr)/2 * r
            v_linear = (wl + wr) / 2.0 * self.wheel_radius
            
            # Compute angular velocity w = (vr - vl) * r / width
            v_angular = (wr - wl) * self.wheel_radius / self.track_width

            # Publish Twist (Odom Source)
            odom_msg = TwistWithCovarianceStamped()
            odom_msg.header.stamp = self.get_clock().now().to_msg()
            odom_msg.header.frame_id = 'base_footprint'
            
            # Linear X
            odom_msg.twist.twist.linear.x = v_linear
            # Angular Z
            odom_msg.twist.twist.angular.z = v_angular

            # Covariance (diagonal) - crucial for EKF
            # x, y, z, r, p, yw
            odom_msg.twist.covariance[0] = 0.001  # x velocity covariance
            odom_msg.twist.covariance[35] = 0.001 # yaw velocity covariance

            self.pub_ohm.publish(odom_msg)

        except Exception as e:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = WheelOdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
