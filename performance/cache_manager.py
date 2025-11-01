"""
Cache Manager Module

Implements multi-level LRU caching for HTML parsing and term extraction
to reduce redundant processing.
"""

from typing import Any, Optional, Dict
from datetime import datetime
import hashlib
from functools import lru_cache
from performance.models import CacheEntry


class CacheManager:
    """
    Manages multi-level caching for parsed HTML and extracted terms.
    
    Uses in-memory caching with LRU eviction policy. Tracks cache statistics
    including hit/miss rates and memory usage.
    """
    
    def __init__(self, max_size_mb: int = 450):
        """
        Initialize cache manager.
        
        Args:
            max_size_mb: Maximum cache size in megabytes (default 450MB)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._cache: Dict[tuple, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0
        self._current_size_bytes = 0
    
    def get(self, cache_key: str, cache_type: str) -> Optional[Any]:
        """
        Retrieve cached data by key and type.
        
        Args:
            cache_key: Unique identifier (content hash)
            cache_type: Type of cached data
        
        Returns:
            Cached data if found and valid, None otherwise
        
        Side Effects:
            Updates last_accessed timestamp and increments access_count
        """
        key = (cache_key, cache_type)
        
        if key in self._cache:
            entry = self._cache[key]
            
            # Check expiration
            if entry.expires_at and datetime.now() > entry.expires_at:
                self.invalidate(cache_key, cache_type)
                self._miss_count += 1
                return None
            
            # Update access tracking
            entry.accessed()
            self._hit_count += 1
            return entry.cached_data
        
        self._miss_count += 1
        return None
    
    def put(self, cache_key: str, cache_type: str, data: Any, size_bytes: int) -> bool:
        """
        Store data in cache with LRU management.
        
        Args:
            cache_key: Unique identifier for cached content
            cache_type: Type of cached data
            data: The actual content to cache
            size_bytes: Memory footprint estimate
        
        Returns:
            True if successfully cached, False if cache is full
        
        Constraints:
            - Total cache size must not exceed max_size_bytes
            - Individual entry size must not exceed 10MB
        """
        # Check individual entry size limit
        if size_bytes > 10 * 1024 * 1024:  # 10MB limit
            return False
        
        # Evict LRU entries if needed
        while self._current_size_bytes + size_bytes > self.max_size_bytes:
            if not self._evict_lru():
                return False  # Cache full, couldn't evict
        
        # Create cache entry
        key = (cache_key, cache_type)
        content_hash = hashlib.sha256(str(data).encode()).hexdigest()
        
        entry = CacheEntry(
            cache_key=cache_key,
            cache_type=cache_type,
            content_hash=content_hash,
            cached_data=data,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
            size_bytes=size_bytes
        )
        
        self._cache[key] = entry
        self._current_size_bytes += size_bytes
        return True
    
    def invalidate(self, cache_key: str, cache_type: str) -> bool:
        """
        Remove specific cache entry.
        
        Args:
            cache_key: Key to invalidate
            cache_type: Type of cache
        
        Returns:
            True if entry was found and removed, False otherwise
        """
        key = (cache_key, cache_type)
        
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size_bytes -= entry.size_bytes
            return True
        
        return False
    
    def clear(self, cache_type: Optional[str] = None) -> int:
        """
        Clear all or specific type of cache entries.
        
        Args:
            cache_type: If provided, only clears this type
        
        Returns:
            Number of entries cleared
        """
        if cache_type is None:
            # Clear all
            count = len(self._cache)
            self._cache.clear()
            self._current_size_bytes = 0
            return count
        else:
            # Clear specific type
            keys_to_remove = [k for k in self._cache.keys() if k[1] == cache_type]
            for key in keys_to_remove:
                entry = self._cache.pop(key)
                self._current_size_bytes -= entry.size_bytes
            return len(keys_to_remove)
    
    def get_statistics(self) -> Dict:
        """
        Returns current cache statistics.
        
        Returns:
            Dictionary with cache metrics including hit rate, size, and per-type breakdown
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0.0
        
        # Calculate per-type statistics
        by_type = {}
        for (_, cache_type), entry in self._cache.items():
            if cache_type not in by_type:
                by_type[cache_type] = {'entries': 0, 'size_bytes': 0}
            by_type[cache_type]['entries'] += 1
            by_type[cache_type]['size_bytes'] += entry.size_bytes
        
        return {
            'total_entries': len(self._cache),
            'total_size_bytes': self._current_size_bytes,
            'total_size_mb': self._current_size_bytes / (1024 * 1024),
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate_percent': round(hit_rate, 2),
            'by_type': by_type
        }
    
    def _evict_lru(self) -> bool:
        """
        Evict least recently used entry.
        
        Returns:
            True if an entry was evicted, False if cache is empty
        """
        if not self._cache:
            return False
        
        # Find LRU entry (oldest last_accessed, excluding recently accessed)
        now = datetime.now()
        lru_key = None
        lru_time = now
        
        for key, entry in self._cache.items():
            # Don't evict entries accessed in last 60 seconds
            if (now - entry.last_accessed).total_seconds() < 60:
                continue
            
            if entry.last_accessed < lru_time:
                lru_time = entry.last_accessed
                lru_key = key
        
        if lru_key:
            entry = self._cache.pop(lru_key)
            self._current_size_bytes -= entry.size_bytes
            return True
        
        return False


# Global cache manager instance (singleton pattern)
_cache_manager_instance = None

def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance
