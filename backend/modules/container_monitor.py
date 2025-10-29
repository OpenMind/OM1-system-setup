"""Container Monitor Module

Monitors multiple Docker containers and their services.
"""
import subprocess
import requests
from typing import Dict, List, Optional


class ContainerMonitor:
    """Monitors Docker containers and their health status."""
    
    def __init__(self, stream_monitor=None):
        """Initialize container monitor with container definitions."""
        self.stream_monitor = stream_monitor
        self.containers = {
            'video_processor': {
                'name': 'om1_video_processor',
                'display_name': 'Video Processor',
                'description': 'Video/Audio processing and face recognition',
                'health_check': None
            },
            'ros2_sensor': {
                'name': 'om1_sensor',
                'display_name': 'ROS2 Sensor',
                'description': 'Robot sensors and camera streams',
                'health_check': None
            },
            'orchestrator': {
                'name': 'orchestrator',
                'display_name': 'Orchestrator',
                'description': 'Navigation, SLAM and charging controller',
                'health_check': 'http://localhost:5000/status'
            },
            'zenoh_bridge': {
                'name': 'zenoh_bridge',
                'display_name': 'Zenoh Bridge',
                'description': 'ROS2 DDS communication bridge',
                'health_check': None
            },
            'watchdog': {
                'name': 'watchdog',
                'display_name': 'Watchdog',
                'description': 'Sensor monitoring service',
                'health_check': None
            }
        }
    
    def get_container_status(self, container_name: str) -> Dict:
        """
        Get the status of a specific container
        
        Returns:
            Dict with container status information
        """
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, 
                 "--format", "{{.State.Status}}|{{.State.Running}}|{{.State.Health.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    'running': False,
                    'status': 'not_found',
                    'health': 'unknown'
                }
            
            status, running, health = result.stdout.strip().split('|')
            
            return {
                'running': running.lower() == 'true',
                'status': status,
                'health': health if health else 'none'
            }
            
        except Exception as e:
            return {
                'running': False,
                'status': 'error',
                'health': 'unknown',
                'error': str(e)
            }
    
    def get_container_uptime(self, container_name: str) -> Optional[str]:
        """Get container uptime."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name,
                 "--format", "{{.State.StartedAt}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except Exception:
            return None
    
    def check_http_health(self, url: str) -> Dict:
        """Check HTTP endpoint health."""
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'healthy': True,
                        'status_code': 200,
                        'data': data
                    }
                except:
                    return {
                        'healthy': True,
                        'status_code': 200
                    }
            else:
                return {
                    'healthy': False,
                    'status_code': response.status_code
                }
        except requests.exceptions.ConnectionError:
            return {
                'healthy': False,
                'error': 'Connection refused'
            }
        except requests.exceptions.Timeout:
            return {
                'healthy': False,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def get_ros2_camera_streams(self) -> Dict:
        """Get ROS2 camera stream status (front and down cameras) with actual RTSP check."""
        streams = {}
        
        for camera_name in ['front_camera', 'down_camera']:
            stream_info = {
                'name': f'{camera_name.replace("_", " ").title()}',
                'type': 'video',
                'rtsp_path': f'rtsp://localhost:8554/{camera_name}',
                'source': 'ros2',
                'status': 'unknown',
                'streaming': False
            }
            
            # Check actual RTSP stream status if StreamMonitor is available
            if self.stream_monitor:
                rtsp_status = self.stream_monitor.check_local_rtsp_stream(camera_name)
                stream_info['streaming'] = rtsp_status.get('streaming', False)
                stream_info['status'] = 'running' if rtsp_status.get('streaming') else 'stopped'
                if 'error' in rtsp_status:
                    stream_info['error'] = rtsp_status['error']
            
            streams[camera_name] = stream_info
        
        return streams
    
    def get_orchestrator_services(self) -> Optional[Dict]:
        """Get orchestrator service status from its API."""
        health = self.check_http_health('http://localhost:5000/status')
        
        if health.get('healthy') and 'data' in health:
            try:
                import json
                status_data = json.loads(health['data'].get('message', '{}'))
                return {
                    'slam': status_data.get('slam_status', 'unknown'),
                    'nav2': status_data.get('nav2_status', 'unknown'),
                    'base_control': status_data.get('base_control_status', 'unknown'),
                    'charging_dock': status_data.get('charging_dock_status', 'unknown'),
                    'is_charging': status_data.get('is_charging', False),
                    'battery_soc': status_data.get('battery_soc', 0.0)
                }
            except:
                return None
        
        return None
    
    def get_all_containers_status(self) -> Dict:
        """
        Get comprehensive status of all monitored containers
        
        Returns:
            Dict with all container groups and their statuses in list format
        """
        result = {
            'video_processor': {
                'display_name': 'Video Processor',
                'container_name': 'om1_video_processor',
                'container_status': None,
                'local_streams': [],
                'cloud_streams': []
            },
            'ros2_sensor': {
                'display_name': 'ROS2 Sensor',
                'container_name': 'om1_sensor',
                'container_status': None,
                'local_streams': []
            },
            'orchestrator': {
                'display_name': 'Orchestrator',
                'container_name': 'orchestrator',
                'container_status': None,
                'services': {}
            }
        }
        
        if self.stream_monitor:
            container_running_status = self.stream_monitor.get_container_status()
            result['video_processor']['container_status'] = {
                'running': container_running_status.get('running', False),
                'status': 'running' if container_running_status.get('running') else 'stopped',
                'health': 'none'
            }
            all_streams = self.stream_monitor.get_all_streams_status()
        else:
            result['video_processor']['container_status'] = self.get_container_status('om1_video_processor')
            all_streams = {}
        
        # Get all streams if StreamMonitor is available
        if all_streams:
            
            # Video Processor - Local Streams
            if 'audio' in all_streams:
                result['video_processor']['local_streams'].append({
                    'name': 'Audio (Mic Local)',
                    'status': all_streams['audio'].get('status', 'unknown'),
                    'type': 'audio'
                })
            
            if 'top_camera' in all_streams:
                result['video_processor']['local_streams'].append({
                    'name': 'Top Camera Local',
                    'status': all_streams['top_camera'].get('status', 'unknown'),
                    'type': 'video'
                })
            
            # Video Processor - Cloud Streams
            if 'audio_cloud' in all_streams:
                result['video_processor']['cloud_streams'].append({
                    'name': 'Audio Cloud',
                    'status': all_streams['audio_cloud'].get('status', 'unknown'),
                    'type': 'audio'
                })
            
            if 'top_camera_cloud' in all_streams:
                result['video_processor']['cloud_streams'].append({
                    'name': 'Top Camera Cloud',
                    'status': all_streams['top_camera_cloud'].get('status', 'unknown'),
                    'type': 'video'
                })
        
        # ROS2 Sensor
        result['ros2_sensor']['container_status'] = self.get_container_status('om1_sensor')
        ros2_streams = self.get_ros2_camera_streams()
        
        for stream_key, stream_data in ros2_streams.items():
            result['ros2_sensor']['local_streams'].append({
                'name': stream_data['name'],
                'status': stream_data.get('status', 'unknown'),
                'type': 'video',
                'streaming': stream_data.get('streaming', False)
            })
            
            # Also add to Video Processor cloud streams for cloud forwarding
            result['video_processor']['cloud_streams'].append({
                'name': f"{stream_data['name']} Cloud",
                'status': stream_data.get('status', 'unknown'),
                'type': 'video',
                'source': 'ros2'
            })
        
        # Orchestrator
        result['orchestrator']['container_status'] = self.get_container_status('orchestrator')
        orchestrator_services = self.get_orchestrator_services()
        if orchestrator_services:
            result['orchestrator']['services'] = orchestrator_services
        
        return result
