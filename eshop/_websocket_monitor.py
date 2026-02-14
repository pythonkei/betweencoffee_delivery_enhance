# eshop/websocket_monitor.py
"""
WebSocket連接監控和健康檢查
"""
import logging
import time
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class WebSocketMonitor:
    """WebSocket連接監控器"""
    
    def __init__(self):
        self.connections = {}
        self.last_cleanup = timezone.now()
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'errors': 0,
        }
    
    def register_connection(self, connection_id, channel_name, user_type='staff'):
        """註冊新連接"""
        self.connections[connection_id] = {
            'channel_name': channel_name,
            'user_type': user_type,
            'connected_at': timezone.now(),
            'last_activity': timezone.now(),
            'message_count': 0,
            'status': 'active'
        }
        self.stats['total_connections'] += 1
        self.stats['active_connections'] += 1
        logger.info(f"WebSocket連接註冊: {connection_id} ({user_type})")
    
    def update_activity(self, connection_id):
        """更新連接活動時間"""
        if connection_id in self.connections:
            self.connections[connection_id]['last_activity'] = timezone.now()
            self.connections[connection_id]['message_count'] += 1
    
    def disconnect(self, connection_id):
        """處理連接斷開"""
        if connection_id in self.connections:
            self.connections[connection_id]['status'] = 'disconnected'
            self.connections[connection_id]['disconnected_at'] = timezone.now()
            self.stats['active_connections'] -= 1
            logger.info(f"WebSocket連接斷開: {connection_id}")
    
    def cleanup_inactive(self, timeout_minutes=30):
        """清理不活動的連接"""
        now = timezone.now()
        timeout = now - timezone.timedelta(minutes=timeout_minutes)
        
        inactive_ids = []
        for conn_id, conn_data in self.connections.items():
            if conn_data['status'] == 'active' and conn_data['last_activity'] < timeout:
                inactive_ids.append(conn_id)
        
        for conn_id in inactive_ids:
            self.disconnect(conn_id)
        
        if inactive_ids:
            logger.info(f"清理了 {len(inactive_ids)} 個不活動連接")
    
    def get_stats(self):
        """獲取統計信息"""
        return {
            **self.stats,
            'connection_details': {
                'total': len(self.connections),
                'active': sum(1 for c in self.connections.values() if c['status'] == 'active'),
                'staff': sum(1 for c in self.connections.values() if c['user_type'] == 'staff'),
                'customer': sum(1 for c in self.connections.values() if c['user_type'] == 'customer'),
            },
            'last_cleanup': self.last_cleanup,
        }
    
    def send_heartbeat(self):
        """發送心跳包到所有活動連接"""
        try:
            channel_layer = get_channel_layer()
            
            for conn_id, conn_data in self.connections.items():
                if conn_data['status'] == 'active':
                    try:
                        async_to_sync(channel_layer.send)(
                            conn_data['channel_name'],
                            {
                                'type': 'heartbeat',
                                'message': 'ping',
                                'timestamp': timezone.now().isoformat()
                            }
                        )
                    except Exception as e:
                        logger.error(f"發送心跳到 {conn_id} 失敗: {str(e)}")
                        self.disconnect(conn_id)
            
            logger.debug(f"發送心跳包到 {self.stats['active_connections']} 個活動連接")
            
        except Exception as e:
            logger.error(f"發送心跳包失敗: {str(e)}")

# 全局監控器實例
monitor = WebSocketMonitor()