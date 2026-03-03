#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistWithCovarianceStamped
from sensor_msgs.msg import JointState
import math

class WheelOdometryNode(Node):
    def __init__(self):
        super().__init__('wheel_odometry_node')
        
        # 你的车轮半径和轮距 (需要根据 URDF 核对)
        self.wheel_radius = 0.033 
        self.track_width = 0.26   # 两个后轮之间的距离

        self.create_subscription(JointState, '/joint_states', self.joint_callback, 10)
        self.pub_twist = self.create_publisher(TwistWithCovarianceStamped, '/wheel/odom', 10)

    def joint_callback(self, msg):
        try:
            # 找到后轮索引
            if 'left_rear_wheel_joint' in msg.name and 'right_rear_wheel_joint' in msg.name:
                idx_l = msg.name.index('left_rear_wheel_joint')
                idx_r = msg.name.index('right_rear_wheel_joint')
                
                if len(msg.velocity) <= idx_l or len(msg.velocity) <= idx_r:
                    return

                # 获取角速度 rad/s
                vel_l = msg.velocity[idx_l]
                vel_r = msg.velocity[idx_r]
                
                # 阿克曼/差速模型近似计算线速度和角速度
                v = (vel_l + vel_r) * self.wheel_radius / 2.0
                w = (vel_r - vel_l) * self.wheel_radius / self.track_width

                # 构建消息
                out = TwistWithCovarianceStamped()
                out.header.stamp = self.get_clock().now().to_msg()
                out.header.frame_id = "base_footprint" 

                out.twist.twist.linear.x = v
                out.twist.twist.angular.z = w
                
                # 给个默认协方差，EKF需要
                out.twist.covariance[0] = 0.01   # x
                out.twist.covariance[35] = 0.01  # yaw

                self.pub_twist.publish(out)
        except ValueError:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = WheelOdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
