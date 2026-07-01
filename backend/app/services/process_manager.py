"""Process Manager & Port Diagnostics

Manages backend processes, ports, and self-healing:
- Detect port conflicts and stale processes
- Force-cleanup stuck processes
- Port availability checking
- Auto-restart with port rotation
- Network diagnostics
- Self-awareness (system state inspection)

Usage:
    from app.services.process_manager import ProcessManager
    pm = ProcessManager()
    
    # Check if port is available
    if pm.is_port_available(8484):
        print("Port available")
    
    # Get process info
    info = pm.get_process_info()
    
    # Kill stale processes
    killed = pm.cleanup_stale_processes()
"""

import os
import sys
import json
import socket
import psutil
import logging
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

log = logging.getLogger("process_manager")

# ─── Data Models ──────────────────────────────────────────────────


@dataclass
class ProcessInfo:
    """Information about a running process"""
    pid: int
    name: str
    status: str  # running, zombie, stopped
    cpu_percent: float
    memory_mb: float
    port: Optional[int] = None
    cmdline: str = ""
    age_seconds: float = 0


@dataclass
class PortInfo:
    """Information about a port"""
    port: int
    available: bool
    process_name: Optional[str] = None
    process_pid: Optional[int] = None
    process_user: Optional[str] = None


# ─── Process Manager ──────────────────────────────────────────────


class ProcessManager:
    """Manage backend processes and ports"""
    
    def __init__(self):
        self.backend_ports = [8484, 8485, 8486]  # Port rotation fallback
        self.frontend_ports = [5173, 5174, 5175]
        self.ollama_ports = [11434, 11435, 11436]
    
    def is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result != 0
        except Exception as e:
            log.warning(f"Port check failed for {port}: {e}")
            return False
    
    def get_port_info(self, port: int) -> PortInfo:
        """Get detailed information about a port"""
        available = self.is_port_available(port)
        
        if available:
            return PortInfo(port=port, available=True)
        
        # Find process using this port
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == "LISTEN":
                    proc = psutil.Process(conn.pid)
                    return PortInfo(
                        port=port,
                        available=False,
                        process_name=proc.name(),
                        process_pid=conn.pid,
                        process_user=proc.username(),
                    )
        except Exception as e:
            log.warning(f"Failed to get port info for {port}: {e}")
        
        return PortInfo(port=port, available=False)
    
    def find_available_port(self, preferred: int, fallback_list: List[int]) -> Tuple[int, bool]:
        """Find an available port, trying preferred first"""
        if self.is_port_available(preferred):
            return preferred, True
        
        for port in fallback_list:
            if self.is_port_available(port):
                log.info(f"Preferred port {preferred} in use, using fallback {port}")
                return port, True
        
        log.error(f"No ports available in {[preferred] + fallback_list}")
        return preferred, False
    
    def get_process_info(self, pid: Optional[int] = None) -> Optional[ProcessInfo]:
        """Get information about a process"""
        try:
            if pid is None:
                pid = os.getpid()
            
            proc = psutil.Process(pid)
            
            try:
                create_time = proc.create_time()
                age = datetime.now(timezone.utc).timestamp() - create_time
            except Exception:
                age = 0
            
            return ProcessInfo(
                pid=pid,
                name=proc.name(),
                status=proc.status(),
                cpu_percent=proc.cpu_percent(interval=0.1),
                memory_mb=proc.memory_info().rss / 1024 / 1024,
                cmdline=" ".join(proc.cmdline()),
                age_seconds=age,
            )
        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            log.error(f"Failed to get process info: {e}")
            return None
    
    def find_process_by_port(self, port: int) -> Optional[ProcessInfo]:
        """Find process using a specific port"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == "LISTEN":
                    return self.get_process_info(conn.pid)
        except Exception as e:
            log.warning(f"Failed to find process on port {port}: {e}")
        
        return None
    
    def find_processes_by_name(self, name: str) -> List[ProcessInfo]:
        """Find all processes with a given name"""
        processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if name.lower() in proc.info["name"].lower():
                    info = self.get_process_info(proc.info["pid"])
                    if info:
                        processes.append(info)
        except Exception as e:
            log.warning(f"Failed to find processes by name '{name}': {e}")
        
        return processes
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kill a process gracefully or forcefully"""
        try:
            proc = psutil.Process(pid)
            
            if force:
                proc.kill()
                log.info(f"Force killed process {pid}")
                return True
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                    log.info(f"Terminated process {pid}")
                    return True
                except psutil.TimeoutExpired:
                    log.warning(f"Process {pid} did not terminate, force killing")
                    proc.kill()
                    return True
        except psutil.NoSuchProcess:
            return True  # Already dead
        except Exception as e:
            log.error(f"Failed to kill process {pid}: {e}")
            return False
    
    def cleanup_stale_processes(self, patterns: List[str] = None) -> int:
        """Kill stale/zombie processes matching patterns"""
        if patterns is None:
            patterns = ["python3", "node", "ollama"]
        
        killed = 0
        try:
            for pattern in patterns:
                processes = self.find_processes_by_name(pattern)
                
                for proc_info in processes:
                    # Skip current process
                    if proc_info.pid == os.getpid():
                        continue
                    
                    # Kill zombies
                    if proc_info.status == "zombie":
                        if self.kill_process(proc_info.pid, force=True):
                            killed += 1
                    
                    # Kill old orphaned processes
                    if proc_info.age_seconds > 86400:  # 24 hours
                        log.info(f"Killing old process {proc_info.pid} (age: {proc_info.age_seconds}s)")
                        if self.kill_process(proc_info.pid):
                            killed += 1
        except Exception as e:
            log.error(f"Cleanup failed: {e}")
        
        return killed
    
    def cleanup_port(self, port: int, force: bool = True) -> bool:
        """Kill process using a specific port"""
        proc_info = self.find_process_by_port(port)
        
        if proc_info is None:
            log.info(f"No process found on port {port}")
            return True
        
        log.warning(f"Killing process {proc_info.pid} on port {port}: {proc_info.name}")
        return self.kill_process(proc_info.pid, force=force)
    
    def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics"""
        try:
            current_proc = self.get_process_info()
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_process": asdict(current_proc) if current_proc else None,
                "ports": {
                    "backend": self.get_port_info(8484).__dict__,
                    "frontend": self.get_port_info(5174).__dict__,
                    "ollama": self.get_port_info(11434).__dict__,
                },
                "processes": {
                    "python": [p.__dict__ for p in self.find_processes_by_name("python")[:5]],
                    "node": [p.__dict__ for p in self.find_processes_by_name("node")[:5]],
                    "ollama": [p.__dict__ for p in self.find_processes_by_name("ollama")[:2]],
                },
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage("/").percent,
                },
            }
        except Exception as e:
            log.error(f"Failed to get diagnostics: {e}")
            return {"error": str(e)}
    
    def get_port_conflict_report(self) -> Dict[str, Any]:
        """Identify port conflicts and suggest solutions"""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conflicts": [],
            "recommendations": [],
        }
        
        # Check main ports
        for name, ports in [("backend", self.backend_ports), ("frontend", self.frontend_ports)]:
            primary = ports[0]
            info = self.get_port_info(primary)
            
            if not info.available:
                report["conflicts"].append({
                    "service": name,
                    "port": primary,
                    "process": info.process_name,
                    "pid": info.process_pid,
                })
                
                # Find available fallback
                for fallback in ports[1:]:
                    if self.is_port_available(fallback):
                        report["recommendations"].append({
                            "service": name,
                            "action": "use_fallback_port",
                            "fallback_port": fallback,
                            "reason": f"{primary} in use by {info.process_name}",
                        })
                        break
                else:
                    report["recommendations"].append({
                        "service": name,
                        "action": "kill_process",
                        "pid": info.process_pid,
                        "reason": f"All ports for {name} in use",
                    })
        
        return report


# ─── Global Instance ──────────────────────────────────────────────

_process_manager: Optional[ProcessManager] = None


def get_process_manager() -> ProcessManager:
    """Get or create global process manager"""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager


if __name__ == "__main__":
    # CLI for testing
    pm = get_process_manager()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "status":
            info = pm.get_process_info()
            print(json.dumps(asdict(info), indent=2))
        
        elif cmd == "diagnostics":
            diag = pm.get_system_diagnostics()
            print(json.dumps(diag, indent=2, default=str))
        
        elif cmd == "ports":
            report = pm.get_port_conflict_report()
            print(json.dumps(report, indent=2))
        
        elif cmd == "cleanup":
            killed = pm.cleanup_stale_processes()
            print(f"Cleaned up {killed} stale processes")
        
        else:
            print(f"Usage: {sys.argv[0]} [status|diagnostics|ports|cleanup]")
    else:
        # Default: show diagnostics
        diag = pm.get_system_diagnostics()
        print(json.dumps(diag, indent=2, default=str))
