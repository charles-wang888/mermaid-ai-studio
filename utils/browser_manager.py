"""浏览器管理器 - 单例模式 + 对象池模式"""
import threading
import sys
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Playwright


class BrowserManager:
    """浏览器管理器 - 单例模式，管理浏览器实例池"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化浏览器管理器"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._playwright: Optional[Playwright] = None
        self._playwright_lock = threading.Lock()
        self._initialized = True
    
    def _ensure_playwright(self):
        """确保Playwright已初始化"""
        if self._playwright is None:
            with self._playwright_lock:
                if self._playwright is None:
                    # Windows上需要设置事件循环策略
                    if sys.platform == 'win32':
                        import asyncio
                        try:
                            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                        except:
                            pass
                    
                    try:
                        from playwright.sync_api import sync_playwright
                        self._playwright = sync_playwright().start()
                    except ImportError:
                        raise ImportError(
                            "Playwright未安装。请运行以下命令安装：\n"
                            "pip install playwright\n"
                            "playwright install chromium"
                        ) from None
    
    def get_browser(self) -> Browser:
        """获取浏览器实例（每次都创建新的，避免线程问题）
        
        Returns:
            Browser实例
        """
        self._ensure_playwright()
        return self._playwright.chromium.launch(headless=True)
    
    def cleanup(self):
        """清理资源"""
        if self._playwright:
            try:
                self._playwright.stop()
                self._playwright = None
            except:
                pass
    
    def __del__(self):
        """析构函数"""
        self.cleanup()

