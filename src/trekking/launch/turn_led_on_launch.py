import rclpy
from rclpy.node import Node
from action_msgs.msg import GoalStatusArray, GoalStatus
import gpiod
import time
import threading

GPIO_CHIP = 'gpiochip4'
LED_PIN = 22

class GoalStatusMonitorNode(Node):
    def __init__(self):
        super().__init__('goal_status_monitor_node')
        # self.get_logger().info('Monitor de Status do Nav2 - Iniciado')
        self.processed_goal_ids = set()
        self.lock = threading.Lock()

        try:
            self.chip = gpiod.Chip(GPIO_CHIP)
            self.led_line = self.chip.get_line(LED_PIN)
            self.led_line.request(consumer="nav_status_led", type=gpiod.LINE_REQ_DIR_OUT)
            self.led_line.set_value(0)
            # self.get_logger().info(f'GPIO {LED_PIN} no chip {GPIO_CHIP} inicializado.')
        except Exception as e:
            # self.get_logger().error(f"Falha ao inicializar GPIO: {e}")
            self.led_line = None

        self.status_subscriber = self.create_subscription(
            GoalStatusArray,
            '/navigate_to_pose/_action/status',
            self.status_callback,
            10)

    def status_callback(self, msg: GoalStatusArray):
        if not self.led_line:
            return

        with self.lock:
            for goal_status in msg.status_list:
                goal_id = tuple(goal_status.goal_info.goal_id.uuid)

                self.processed_goal_ids.add(goal_id)

                if not self.led_is_blinking:
                    threading.Thread(target=self.blink_led).start()

    def blink_led(self):
        self.led_line.set_value(1)
        time.sleep(5)
        self.led_line.set_value(0)

    def format_goal_id(self, goal_id_tuple):
        return ''.join(f'{b:02x}' for b in goal_id_tuple)[:8]

def main(args=None):
    rclpy.init(args=args)
    
    node = GoalStatusMonitorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()