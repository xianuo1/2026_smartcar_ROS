#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from ackermann_msgs.msg import AckermannDriveStamped

class ServoCommands(Node):
    def __init__(self):
        super().__init__('servo_commands')

        # 输入：Ackermann 高层指令
        self.create_subscription(
            AckermannDriveStamped,
            "/ackermann_cmd_mux/output",
            self.set_throttle_steer,
            1,
        )

        # 输出：ros2_control 期望的 Float64MultiArray /<controller>/commands
        self.pub_vel_left_rear_wheel = self.create_publisher(
            Float64MultiArray, '/left_rear_wheel_velocity_controller/commands', 1
        )
        self.pub_vel_right_rear_wheel = self.create_publisher(
            Float64MultiArray, '/right_rear_wheel_velocity_controller/commands', 1
        )
        self.pub_vel_left_front_wheel = self.create_publisher(
            Float64MultiArray, '/left_front_wheel_velocity_controller/commands', 1
        )
        self.pub_vel_right_front_wheel = self.create_publisher(
            Float64MultiArray, '/right_front_wheel_velocity_controller/commands', 1
        )

        self.pub_pos_left_steering_hinge = self.create_publisher(
            Float64MultiArray, '/left_steering_hinge_position_controller/commands', 1
        )
        self.pub_pos_right_steering_hinge = self.create_publisher(
            Float64MultiArray, '/right_steering_hinge_position_controller/commands', 1
        )

    def set_throttle_steer(self, data):
        throttle = data.drive.speed * 31.25
        steer = data.drive.steering_angle

        # 速度指令
        vel_msg = Float64MultiArray()
        vel_msg.data = [throttle]

        # 转向指令
        steer_msg = Float64MultiArray()
        steer_msg.data = [steer]

        self.pub_vel_left_rear_wheel.publish(vel_msg)
        self.pub_vel_right_rear_wheel.publish(vel_msg)
        self.pub_vel_left_front_wheel.publish(vel_msg)
        self.pub_vel_right_front_wheel.publish(vel_msg)

        self.pub_pos_left_steering_hinge.publish(steer_msg)
        self.pub_pos_right_steering_hinge.publish(steer_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ServoCommands()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        pass
