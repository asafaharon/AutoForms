"""
Performance monitoring for form generation
"""
import time
from typing import Dict, List
from datetime import datetime, timedelta

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[Dict] = []
        self.max_metrics = 100  # Keep last 100 measurements
    
    def record_generation_time(self, operation: str, duration: float, cache_hit: bool = False):
        """Record generation time"""
        self.metrics.append({
            "operation": operation,
            "duration": duration,
            "cache_hit": cache_hit,
            "timestamp": datetime.now()
        })
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.metrics:
            return {"message": "No metrics available"}
        
        recent_metrics = [
            m for m in self.metrics 
            if m["timestamp"] > datetime.now() - timedelta(hours=1)
        ]
        
        if not recent_metrics:
            return {"message": "No recent metrics"}
        
        durations = [m["duration"] for m in recent_metrics]
        cache_hits = [m for m in recent_metrics if m["cache_hit"]]
        
        return {
            "total_requests": len(recent_metrics),
            "cache_hit_rate": len(cache_hits) / len(recent_metrics) * 100,
            "avg_response_time": sum(durations) / len(durations),
            "min_response_time": min(durations),
            "max_response_time": max(durations),
            "under_5_seconds": len([d for d in durations if d < 5.0]),
            "performance_target_met": len([d for d in durations if d < 5.0]) / len(durations) * 100
        }

# Global performance monitor
perf_monitor = PerformanceMonitor()