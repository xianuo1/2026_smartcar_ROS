#!/usr/bin/env python3
#-*-coding:utf-8-*-

import rclpy
from rclpy.node import Node
import math
import tf2_ros
from std_msgs.msg import Float64
from geometry_msgs.msg import Twist, TransformStamped
from sensor_msgs.msg import Imu, JointState
from nav_msgs.msg import Odometry

# Helper function for euler_from_quaternion
def euler_from_quaternion(quaternion):
    """
    Converts quaternion (w in last place) to euler roll, pitch, yaw
    quaternion = [x, y, z, w]
    Bellow should be replaced when porting for ROS 2 Python tf_conversions is done.
    """
    x = quaternion[0]
    y = quaternion[1]
    z = quaternion[2]
    w = quaternion[3]

    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    sinp = 2 * (w * y - z * x)
    pitch = math.asin(sinp)

    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

# Definition of parameters
frame_name  = "odom"
child_frame_name = "base_footprint"
pub_name    = "odom_topic"
imu_name    = "imu_data"
joint_states_name   = "/racebot/joint_states"
# Start coordinates
start_x     = -0.5
start_y     = 0
start_z     = 0

class OdomPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')
        
        self.odom_topic = Odometry()
        self.odom_tf = TransformStamped()
        
        self.yaw_angle = 0.0 # single float yaw
        self.current_yaw = 0.0
        
        # Subscribers
        self.create_subscription(Imu, imu_name, self.callback_imu, 1)
        self.create_subscription(JointState, joint_states_name, self.callback_join, 1)
        
        # Publisher
        self.pub = self.create_publisher(Odometry, pub_name, 1)
        
        # TF Broadcaster
        self.br = tf2_ros.TransformBroadcaster(self)
        
        # Time tracking
        self.now_time_joint = self.get_clock().now().nanoseconds / 1e9
        self.old_time_joint = self.now_time_joint
        
        # Odom init
        self.odom_topic.pose.pose.position.x = float(start_x)
        self.odom_topic.pose.pose.position.y = float(start_y)
        self.odom_topic.pose.pose.position.z = float(start_z)
        self.odom_topic.header.frame_id = frame_name
        self.odom_topic.child_frame_id = child_frame_name
        
        self.odom_tf.header.frame_id = frame_name
        self.odom_tf.child_frame_id = child_frame_name

    def callback_imu(self, data):
        # Calculate yaw
        # data.orientation is geometry_msgs/Quaternion
        quat = [data.orientation.x, data.orientation.y, data.orientation.z, data.orientation.w]
        (_, _, yaw) = euler_from_quaternion(quat)
        self.current_yaw = yaw
        
        # Update orientation in odom
        self.odom_topic.pose.pose.orientation = data.orientation
        
        # Update angular velocity
        self.odom_topic.twist.twist.angular = data.angular_velocity

    def callback_join(self, data):
        # Calculate dt
        now = self.get_clock().now()
        self.now_time_joint = now.nanoseconds / 1e9
        dt = self.now_time_joint - self.old_time_joint
        self.old_time_joint = self.now_time_joint
        
        if dt <= 0:
            return

        # Record time
        self.odom_topic.header.stamp = now.to_msg()
        self.odom_tf.header.stamp = now.to_msg()

        try:
            # Encoder velocity
            # Find index of wheels
            if 'left_rear_wheel' in data.name and 'right_rear_wheel' in data.name:
                lrw_idx = data.name.index('left_rear_wheel')
                rrw_idx = data.name.index('right_rear_wheel')
                
                # Average velocity
                # Note: 13.95348 seems to be a conversion factor? Assuming it is correct from original code.
                v_l = data.velocity[lrw_idx]
                v_r = data.velocity[rrw_idx]
                velocity = (v_l + v_r) / (2 * 13.95348)
                
                # Distance
                distance = velocity * dt
                
                # Update position (x, y)
                # Use current yaw from IMU
                self.odom_topic.pose.pose.position.x += (distance * math.cos(self.current_yaw))
                self.odom_topic.pose.pose.position.y += (distance * math.sin(self.current_yaw))
                
                # Update linear velocity
                # Assume forward/backward based on yaw? 
                # Original logic:
                # if ((self.yaw_angle[2] < 1.52) and (self.yaw_angle[2] > -1.52)):
                #     self.odom_topic.twist.twist.linear.x = velocity*math.cos(self.yaw_angle[2])
                # else :
                #     self.odom_topic.twist.twist.linear.x = -velocity*math.cos(self.yaw_angle[2])
                
                # This logic seems to try to project velocity to global X? 
                # But odom twist should be in base_link frame (child_frame_id).
                # Usually for diff drive, twist.linear.x is just `velocity`.
                # If the original code meant global velocity, then `twist` part of Odometry message is:
                # "The twist should be specified in the coordinate frame given by the child_frame_id" (base_footprint)
                # So if base_footprint moves forward with `velocity`, linear.x = velocity.
                
                # However, the original code does some strange cos projection which suggests it might be filling twist in world frame?
                # But standard ROS usage is twist in child frame.
                # I will stick to standard: linear.x = velocity.
                self.odom_topic.twist.twist.linear.x = velocity
                self.odom_topic.twist.twist.linear.y = 0.0

                # Publish Odom
                self.pub.publish(self.odom_topic)
                
                # Publish TF
                self.odom_tf.transform.translation.x = self.odom_topic.pose.pose.position.x
                self.odom_tf.transform.translation.y = self.odom_topic.pose.pose.position.y
                self.odom_tf.transform.translation.z = self.odom_topic.pose.pose.position.z
                self.odom_tf.transform.rotation = self.odom_topic.pose.pose.orientation
                self.br.sendTransform(self.odom_tf)
                
        except ValueError:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = OdomPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
