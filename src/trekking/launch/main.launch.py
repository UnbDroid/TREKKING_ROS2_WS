import os
import xacro
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Use simulation time
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Get package paths
    pkg_path = get_package_share_directory('trekking')
    rf2o_path = get_package_share_directory('rf2o_laser_odometry')
    slam_toolbox_pkg_path = get_package_share_directory('slam_toolbox')
    lidar_pkg_path = get_package_share_directory('sllidar_ros2')

    # Robot State Publisher
    xacro_file = os.path.join(pkg_path, 'description', 'robot_core.urdf.xacro')
    doc = xacro.process_file(xacro_file, mappings={'sim_mode': 'true'})
    robot_description_config = doc.toxml()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_config,
            'use_sim_time': use_sim_time,
            'publish_fixed_joints': 'true'
        }]
    )
    
    # Joint State Publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    # LiDAR Node
    lidar_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lidar_pkg_path, 'launch', 'sllidar_s2_launch.py')
        ),
        launch_arguments={'frame_id': 'laser_frame'}.items()
    )
    
    # rf2o_laser_odometry Node
    rf2o_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rf2o_path, 'launch', 'rf2o_laser_odometry.launch.py')
        ),
        launch_arguments={'use_sim_time': 'false'}.items()
    )
    
    # Nav2 Node
    nav2_params_file = os.path.join(pkg_path, 'config', 'nav2_params.yaml')
    nav2_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={'params_file': nav2_params_file, 'use_sim_time': 'false'}.items()
    )

    # SLAM Toolbox Node
    slam_params_file = os.path.join(pkg_path, 'config', 'mapper_params_online_async.yaml')
    slam_toolbox_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_pkg_path, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={'slam_params_file': slam_params_file}.items()
    )
    
    # Localization Node (amcl stuff)
    amcl_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch', 'localization_launch.py')
        ),
        launch_arguments={
            'namespace': '',
            'map': '/home/caldo/Projects/trekking_test_ws/teste.yaml',
            'use_sim_time': use_sim_time,
            'autostart': 'true',
            'params_file': os.path.join(pkg_path, 'config', 'nav2_params.yaml')
        }.items()
    )

    # Run rviz2
    rviz_config_file = os.path.join(pkg_path, 'config', 'view_bot.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),
        robot_state_publisher_node,
        joint_state_publisher_node,
        lidar_node,
        rf2o_node,
        nav2_node,
        slam_toolbox_node,
        # amcl_node,
        rviz_node
    ])