#!/usr/bin/env python3

'''
This script makes Gazebo less fail by translating gazebo status messages to odometry data.
Since Gazebo also publishes data faster than normal odom data, this script caps the update to 20hz.
Winter Guerra
'''

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose, Twist, Transform, TransformStamped
from gazebo_msgs.msg import LinkStates
from std_msgs.msg import Header
import math
import tf2_ros
from rclpy.exceptions import ParameterAlreadyDeclaredException

class OdometryNode(Node):
    def __init__(self):
        super().__init__('gazebo_odometry_node')
        # Declare usage of simulation time explicitly
        try:
            # `use_sim_time` may already be declared by rcl/launch parameter overrides.
            self.declare_parameter('use_sim_time', False)
        except ParameterAlreadyDeclaredException:
            pass
        
        # Set publishers
        self.pub_odom = self.create_publisher(Odometry, '/odom', 10)
        self.tf_pub = tf2_ros.TransformBroadcaster(self)

        # Optional fallback: if Gazebo link states are not available, re-broadcast TF from an existing odom topic.
        self.declare_parameter('fallback_to_odom_topic', True)
        self.declare_parameter('fallback_odom_topic', '/odom')
        self._fallback_to_odom_topic = bool(self.get_parameter('fallback_to_odom_topic').value)
        self._fallback_odom_topic = str(self.get_parameter('fallback_odom_topic').value)
        self._latest_odom_msg = None
        self._received_any_odom = False

        # init internals
        self.last_received_pose = Pose()
        self.last_received_twist = Twist()
        self.last_recieved_stamp = None
        self._started_stamp = self.get_clock().now()
        self._received_any_link_states = False

        # Set the update rate
        self.create_timer(0.05, self.timer_callback) # 20hz

        # Set subscribers
        self.create_subscription(LinkStates, '/gazebo/link_states', self.sub_robot_pose_update, 1)
        if self._fallback_to_odom_topic:
            # NOTE: This node also publishes /odom; the fallback is intended for setups where /odom is provided
            # by another source (e.g. Gazebo plugins) and TF is missing.
            self.create_subscription(Odometry, self._fallback_odom_topic, self.sub_odom_update, 10)

    def sub_odom_update(self, msg: Odometry):
        self._latest_odom_msg = msg
        self._received_any_odom = True

    def _broadcast_tf_from_odom_msg(self, msg: Odometry):
        parent_frame = msg.header.frame_id.strip() if msg.header.frame_id else 'odom'
        child_frame = msg.child_frame_id.strip() if msg.child_frame_id else 'base_footprint'

        tf_msg = TransformStamped()
        # Prefer the odom message stamp; if it's unset, use node clock.
        if msg.header.stamp.sec == 0 and msg.header.stamp.nanosec == 0:
            tf_msg.header.stamp = self.get_clock().now().to_msg()
        else:
            tf_msg.header.stamp = msg.header.stamp

        tf_msg.header.frame_id = parent_frame
        tf_msg.child_frame_id = child_frame
        tf_msg.transform.translation.x = msg.pose.pose.position.x
        tf_msg.transform.translation.y = msg.pose.pose.position.y
        tf_msg.transform.translation.z = msg.pose.pose.position.z
        tf_msg.transform.rotation = msg.pose.pose.orientation
        self.tf_pub.sendTransform(tf_msg)

    def sub_robot_pose_update(self, msg):
        self._received_any_link_states = True
        # Find the index of the racecar
        try:
            # Flexible search for base_footprint
            target_name = 'base_footprint'
            arrayIndex = -1
            
            # self.get_logger().info(f"Available links: {msg.name}", throttle_duration_sec=2.0) # Debug print
            
            for i, name in enumerate(msg.name):
                # Check for either 'base_footprint' OR 'base_link' just in case
                if target_name in name or 'base_link' in name:
                    arrayIndex = i
                    break
            
            if arrayIndex == -1:
                # Log this warning so we know why it's failing
                self.get_logger().warn(f"Waiting for link... Available: {msg.name}", throttle_duration_sec=2.0)
                return

        except ValueError as e:
            # Wait for Gazebo to startup
            pass
        else:
            # Extract our current position information
            self.last_received_pose = msg.pose[arrayIndex]
            self.last_received_twist = msg.twist[arrayIndex]
        self.last_recieved_stamp = self.get_clock().now()

    def timer_callback(self):
        try:
            if self.last_recieved_stamp is None:
                # If Gazebo topic is missing or the subscription never receives, TF/odom will never publish.
                # Emit a throttled warning to make this obvious.
                if not self._received_any_link_states:
                    now = self.get_clock().now()
                    if (now - self._started_stamp).nanoseconds > 5_000_000_000:
                        if self._fallback_to_odom_topic and self._received_any_odom and self._latest_odom_msg is not None:
                            self._broadcast_tf_from_odom_msg(self._latest_odom_msg)
                            self.get_logger().warn(
                                f'No /gazebo/link_states received; broadcasting TF from {self._fallback_odom_topic} instead.',
                                throttle_duration_sec=2.0,
                            )
                            return

                        self.get_logger().warn(
                            'No /gazebo/link_states received yet; not publishing /odom TF. '
                            'Check Gazebo is running and the topic exists.',
                            throttle_duration_sec=2.0,
                        )
                return

            now = self.get_clock().now()
            
            cmd = Odometry()
            cmd.header.stamp = now.to_msg()
            cmd.header.frame_id = 'odom'
            cmd.child_frame_id = 'base_footprint'
            cmd.pose.pose = self.last_received_pose
            cmd.twist.twist = self.last_received_twist
            self.pub_odom.publish(cmd)

            tf = TransformStamped()
            tf.header.stamp = now.to_msg()
            tf.header.frame_id = 'odom'
            tf.child_frame_id = 'base_footprint'
            tf.transform.translation.x = self.last_received_pose.position.x
            tf.transform.translation.y = self.last_received_pose.position.y
            tf.transform.translation.z = self.last_received_pose.position.z
            tf.transform.rotation = self.last_received_pose.orientation

            self.tf_pub.sendTransform(tf)
        except Exception as e:
            self.get_logger().error(f"Error in timer_callback: {e}", throttle_duration_sec=1.0)
        # self.get_logger().info(f"Published params: odom->base_footprint at {now.nanoseconds}", throttle_duration_sec=1.0)

def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
