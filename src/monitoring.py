"""
Health Check and Monitoring utilities for RunPod Translation Models
"""

import os
import json
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
import threading
from collections import deque
from loguru import logger


class PerformanceMonitor:
    """Monitor system and model performance metrics"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.request_times = deque(maxlen=window_size)
        self.error_count = 0
        self.success_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()

    def record_request(self, duration: float, success: bool = True):
        """Record a request's performance metrics"""
        with self.lock:
            self.request_times.append(duration)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self.lock:
            total_requests = self.success_count + self.error_count
            uptime = time.time() - self.start_time

            # Calculate response time statistics
            if self.request_times:
                avg_response_time = sum(self.request_times) / len(self.request_times)
                min_response_time = min(self.request_times)
                max_response_time = max(self.request_times)
                p95_response_time = sorted(self.request_times)[
                    int(0.95 * len(self.request_times))
                ]
            else:
                avg_response_time = min_response_time = max_response_time = (
                    p95_response_time
                ) = 0

            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # GPU metrics (if available)
            gpu_info = self._get_gpu_info()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime,
                "requests": {
                    "total": total_requests,
                    "success": self.success_count,
                    "errors": self.error_count,
                    "success_rate": (
                        self.success_count / total_requests if total_requests > 0 else 0
                    ),
                    "requests_per_minute": (
                        total_requests / (uptime / 60) if uptime > 0 else 0
                    ),
                },
                "response_time": {
                    "avg_ms": avg_response_time * 1000,
                    "min_ms": min_response_time * 1000,
                    "max_ms": max_response_time * 1000,
                    "p95_ms": p95_response_time * 1000,
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "used_gb": memory.used / (1024**3),
                        "available_gb": memory.available / (1024**3),
                        "percent": memory.percent,
                    },
                    "disk": {
                        "used_gb": disk.used / (1024**3),
                        "free_gb": disk.free / (1024**3),
                        "percent": (disk.used / disk.total) * 100,
                    },
                },
                "gpu": gpu_info,
            }

    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information if available"""
        try:
            import torch

            if torch.cuda.is_available():
                gpu_info = {}
                for i in range(torch.cuda.device_count()):
                    gpu_info[f"gpu_{i}"] = {
                        "name": torch.cuda.get_device_name(i),
                        "memory_used_gb": torch.cuda.memory_allocated(i) / (1024**3),
                        "memory_cached_gb": torch.cuda.memory_reserved(i) / (1024**3),
                        "utilization": (
                            torch.cuda.utilization(i)
                            if hasattr(torch.cuda, "utilization")
                            else None
                        ),
                    }
                return gpu_info
            return {"available": False}
        except ImportError:
            return {"error": "torch not available"}
        except Exception as e:
            return {"error": str(e)}


class HealthChecker:
    """Comprehensive health check system"""

    def __init__(self, models: Dict[str, Any]):
        self.models = models
        self.last_health_check = None
        self.health_status = "unknown"

    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        self.last_health_check = datetime.utcnow()

        health_report = {
            "timestamp": self.last_health_check.isoformat(),
            "status": "healthy",
            "checks": {},
        }

        # Check models
        model_checks = self._check_models()
        health_report["checks"]["models"] = model_checks

        # Check system resources
        system_checks = self._check_system_resources()
        health_report["checks"]["system"] = system_checks

        # Check environment variables
        env_checks = self._check_environment()
        health_report["checks"]["environment"] = env_checks

        # Check disk space
        disk_checks = self._check_disk_space()
        health_report["checks"]["disk"] = disk_checks

        # Determine overall health
        all_checks = [model_checks, system_checks, env_checks, disk_checks]
        if any(not check["healthy"] for check in all_checks):
            health_report["status"] = "unhealthy"
            self.health_status = "unhealthy"
        else:
            self.health_status = "healthy"

        return health_report

    def _check_models(self) -> Dict[str, Any]:
        """Check if models are loaded and functioning"""
        checks = {"healthy": True, "details": {}}

        for model_name, model_instance in self.models.items():
            try:
                if model_instance is None:
                    checks["details"][model_name] = {
                        "loaded": False,
                        "error": "Model not loaded",
                    }
                    checks["healthy"] = False
                else:
                    checks["details"][model_name] = {
                        "loaded": True,
                        "type": type(model_instance).__name__,
                    }
            except Exception as e:
                checks["details"][model_name] = {"loaded": False, "error": str(e)}
                checks["healthy"] = False

        return checks

    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        checks = {"healthy": True, "details": {}}

        # Check memory
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        checks["details"]["memory"] = {
            "usage_percent": memory_usage,
            "available_gb": memory.available / (1024**3),
        }

        if memory_usage > 90:
            checks["healthy"] = False
            checks["details"]["memory"]["warning"] = "High memory usage"

        # Check CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        checks["details"]["cpu"] = {"usage_percent": cpu_usage}

        if cpu_usage > 95:
            checks["healthy"] = False
            checks["details"]["cpu"]["warning"] = "High CPU usage"

        return checks

    def _check_environment(self) -> Dict[str, Any]:
        """No required environment variables anymore"""
        return {"healthy": True, "details": {}}

    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        checks = {"healthy": True, "details": {}}

        disk = psutil.disk_usage("/")
        usage_percent = (disk.used / disk.total) * 100
        free_gb = disk.free / (1024**3)

        checks["details"]["usage_percent"] = usage_percent
        checks["details"]["free_gb"] = free_gb

        if usage_percent > 90 or free_gb < 2:
            checks["healthy"] = False
            checks["details"]["warning"] = "Low disk space"

        return checks


# Global instances
performance_monitor = PerformanceMonitor()
health_checker = None


def initialize_monitoring(models: Dict[str, Any]):
    """Initialize monitoring with model references"""
    global health_checker
    health_checker = HealthChecker(models)


def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    if health_checker is None:
        return {
            "status": "not_initialized",
            "message": "Health checker not initialized",
        }

    return health_checker.check_health()


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics"""
    return performance_monitor.get_metrics()


def record_request_performance(duration: float, success: bool = True):
    """Record a request's performance for monitoring"""
    performance_monitor.record_request(duration, success)
