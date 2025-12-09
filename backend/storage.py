"""
Storage Abstraction Layer
Supports HDFS (via WebHDFS) with automatic fallback to local filesystem
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import json
import io

try:
    from hdfs import InsecureClient as HdfsClient
    HDFS_AVAILABLE = True
except ImportError:
    HdfsClient = None
    HDFS_AVAILABLE = False


class StorageAdapter(ABC):
    """Abstract storage interface"""
    
    @abstractmethod
    def write_record(self, record: Dict[str, Any]) -> None:
        """Write a single weather record"""
        pass
    
    @abstractmethod
    def read_records(self, city: Optional[str] = None, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read records, optionally filtered by city and date"""
        pass
    
    @abstractmethod
    def get_storage_type(self) -> str:
        """Return storage type identifier"""
        pass
    
    @abstractmethod
    def list_cities(self) -> List[str]:
        """List all unique city names from available data files"""
        pass
    
    @abstractmethod
    def list_cities(self) -> List[str]:
        """List all unique city names from available data files"""
        pass


class HDFSAdapter(StorageAdapter):
    """HDFS storage adapter using WebHDFS"""
    
    def __init__(self, namenode: str, user: str, base_path: str):
        self.namenode = namenode
        self.user = user
        self.base_path = base_path.rstrip("/")
        self.client = HdfsClient(namenode, user=user, root=base_path)
        self._ensure_base_path()
    
    def _ensure_base_path(self):
        """Ensure base path exists in HDFS"""
        try:
            if not self.client.status(".", strict=False):
                self.client.makedirs(".")
        except Exception:
            pass
    
    def _get_partition_path(self, record: Dict[str, Any]) -> str:
        """Get HDFS path with date partitioning: ingest/date=YYYY-MM-DD/"""
        timestamp_str = record.get("timestamp", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now()
        
        date_str = dt.strftime("%Y-%m-%d")
        partition = f"date={date_str}"
        return f"ingest/{partition}"
    
    def _get_file_path(self, record: Dict[str, Any]) -> str:
        """Get full file path for a record (relative to client root)"""
        partition = self._get_partition_path(record)
        city = record.get("city", "unknown").lower()
        return f"{partition}/{city}.jsonl"
    
    def write_record(self, record: Dict[str, Any]) -> None:
        """Write record to HDFS with date partitioning"""
        file_path = self._get_file_path(record)
        line = json.dumps(record, default=str) + "\n"
        
        try:
            # Create partition directory if needed
            partition = self._get_partition_path(record)
            if not self.client.status(partition, strict=False):
                self.client.makedirs(partition)
            
            # Append to file (create if doesn't exist)
            if self.client.status(file_path, strict=False):
                self.client.write(file_path, data=line.encode("utf-8"), append=True)
            else:
                self.client.write(file_path, data=line.encode("utf-8"), overwrite=True)
        except Exception as e:
            raise Exception(f"HDFS write failed: {e}")
    
    def read_records(self, city: Optional[str] = None, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read records from HDFS, scanning date partitions"""
        records = []
        base_partition = "ingest"
        
        try:
            # List all date partitions
            if not self.client.status(base_partition, strict=False):
                return []
            
            partitions = []
            try:
                for item in self.client.list(base_partition):
                    if item.startswith("date="):
                        partitions.append(f"{base_partition}/{item}")
            except Exception:
                pass
            
            # Read from each partition
            for partition in partitions:
                try:
                    files = self.client.list(partition)
                    for filename in files:
                        if not filename.endswith(".jsonl"):
                            continue
                        
                        file_city = filename.replace(".jsonl", "")
                        if city and file_city != city.lower():
                            continue
                        
                        file_path = f"{partition}/{filename}"
                        with self.client.read(file_path) as reader:
                            data = io.TextIOWrapper(reader, encoding="utf-8")
                            for line in data:
                                try:
                                    record = json.loads(line.strip())
                                    if record:
                                        # Filter by date if specified
                                        if since:
                                            record_ts = record.get("timestamp")
                                            if record_ts:
                                                try:
                                                    record_dt = datetime.fromisoformat(
                                                        record_ts.replace("Z", "+00:00")
                                                    )
                                                    if record_dt < since:
                                                        continue
                                                except Exception:
                                                    pass
                                        records.append(record)
                                except Exception:
                                    continue
                except Exception:
                    continue
        except Exception as e:
            raise Exception(f"HDFS read failed: {e}")
        
        return records
    
    def list_cities(self) -> List[str]:
        """List all unique city names from HDFS filenames, with fallback to local filesystem"""
        cities = set()
        base_partition = "ingest"
        
        # Try HDFS first
        try:
            if self.client.status(base_partition, strict=False):
                partitions = []
                try:
                    for item in self.client.list(base_partition):
                        if item.startswith("date="):
                            partitions.append(f"{base_partition}/{item}")
                except Exception:
                    pass
                
                for partition in partitions:
                    try:
                        files = self.client.list(partition)
                        for filename in files:
                            if filename.endswith(".jsonl"):
                                city = filename.replace(".jsonl", "").lower()
                                if city:
                                    cities.add(city)
                    except Exception:
                        continue
        except Exception:
            pass
        
        # Always check local filesystem as fallback (HDFS might not have all data)
        # This ensures we get all cities from the mounted data directory
        # Try multiple possible local paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
            os.getenv("DATA_DIR", "/app/data"),
            "/app/data",  # Docker mount point
        ]
        for local_dir in possible_paths:
            local_base = os.path.join(local_dir, "apps", "weather", "ingest")
            if os.path.exists(local_base):
                try:
                    for item in os.listdir(local_base):
                        if item.startswith("date="):
                            partition = os.path.join(local_base, item)
                            if os.path.isdir(partition):
                                for filename in os.listdir(partition):
                                    if filename.endswith(".jsonl"):
                                        city = filename.replace(".jsonl", "").lower()
                                        if city:
                                            cities.add(city)
                except Exception:
                    continue
                if cities:  # If we found cities, stop trying other paths
                    break
        
        return sorted(list(cities))
    
    def get_storage_type(self) -> str:
        return "hdfs"


class LocalAdapter(StorageAdapter):
    """Local filesystem storage adapter with date partitioning"""
    
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _get_partition_path(self, record: Dict[str, Any]) -> str:
        """Get local path with date partitioning"""
        timestamp_str = record.get("timestamp", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now()
        
        date_str = dt.strftime("%Y-%m-%d")
        partition = f"date={date_str}"
        return os.path.join(self.base_dir, "apps", "weather", "ingest", partition)
    
    def _get_file_path(self, record: Dict[str, Any]) -> str:
        """Get full file path for a record"""
        partition = self._get_partition_path(record)
        city = record.get("city", "unknown").lower()
        return os.path.join(partition, f"{city}.jsonl")
    
    def write_record(self, record: Dict[str, Any]) -> None:
        """Write record to local filesystem with date partitioning"""
        file_path = self._get_file_path(record)
        partition_dir = os.path.dirname(file_path)
        os.makedirs(partition_dir, exist_ok=True)
        
        line = json.dumps(record, default=str) + "\n"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(line)
    
    def read_records(self, city: Optional[str] = None, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read records from local filesystem, scanning date partitions"""
        records = []
        base_partition = os.path.join(self.base_dir, "apps", "weather", "ingest") 
        
        if not os.path.exists(base_partition):
            return []
        
        # List all date partitions
        partitions = []
        try:
            for item in os.listdir(base_partition):
                if item.startswith("date="):
                    partitions.append(os.path.join(base_partition, item))
        except Exception:
            pass
        
        # Read from each partition
        for partition in partitions:
            try:
                if not os.path.isdir(partition):
                    continue
                
                for filename in os.listdir(partition):
                    if not filename.endswith(".jsonl"):
                        continue
                    
                    file_city = filename.replace(".jsonl", "")
                    if city and file_city != city.lower():
                        continue
                    
                    file_path = os.path.join(partition, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                record = json.loads(line.strip())
                                if record:
                                    # Filter by date if specified
                                    if since:
                                        record_ts = record.get("timestamp")
                                        if record_ts:
                                            try:
                                                record_dt = datetime.fromisoformat(
                                                    record_ts.replace("Z", "+00:00")
                                                )
                                                if record_dt < since:
                                                    continue
                                            except Exception:
                                                pass
                                    records.append(record)
                            except Exception:
                                continue
            except Exception:
                continue
        
        return records
    
    def list_cities(self) -> List[str]:
        """List all unique city names from local filesystem filenames"""
        cities = set()
        base_partition = os.path.join(self.base_dir, "apps", "weather", "ingest")
        
        if not os.path.exists(base_partition):
            return []
        
        partitions = []
        try:
            for item in os.listdir(base_partition):
                if item.startswith("date="):
                    partitions.append(os.path.join(base_partition, item))
        except Exception:
            pass
        
        for partition in partitions:
            try:
                if not os.path.isdir(partition):
                    continue
                
                for filename in os.listdir(partition):
                    if filename.endswith(".jsonl"):
                        city = filename.replace(".jsonl", "").lower()
                        if city:
                            cities.add(city)
            except Exception:
                continue
        
        return sorted(list(cities))
    
    def get_storage_type(self) -> str:
        return "local"


def get_storage_adapter() -> StorageAdapter:
    """
    Factory function to get storage adapter
    Tries HDFS first, falls back to local filesystem
    """
    # Try HDFS configuration
    namenode = os.getenv("HDFS_NAMENODE", "http://localhost:9870")
    # Avoid os.getlogin() in containers without a TTY; default to "hadoop".
    hdfs_user = os.getenv("HDFS_USER") or "hadoop"
    hdfs_base = os.getenv("HDFS_BASE_DIR", "/apps/weather")
    
    if HDFS_AVAILABLE:
        try:
            client = HdfsClient(namenode, user=hdfs_user, root=hdfs_base)
            # Test connection
            client.status(".", strict=False)
            print(f"[OK] Using HDFS storage: {namenode}{hdfs_base}")
            return HDFSAdapter(namenode, hdfs_user, hdfs_base)
        except Exception as e:
            print(f"[WARN] HDFS unavailable ({e}), falling back to local storage")
    
    # Fallback to local
    local_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    print(f"[OK] Using local storage: {local_dir}")
    return LocalAdapter(local_dir)

