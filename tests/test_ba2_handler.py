"""Tests for BA2 handler"""

import pytest
from ba2_manager.core.ba2_handler import BA2Handler


class TestBA2Handler:
    """Test BA2Handler class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = BA2Handler()
    
    def test_init(self):
        """Test handler initialization"""
        assert self.handler.current_file is None
    
    def test_list_contents_empty(self):
        """Test listing contents with no file loaded"""
        contents = self.handler.list_contents()
        assert contents == []
