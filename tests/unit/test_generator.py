import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/telemetry-generator'))

from main import generate_telemetry_data, REGIONS

class TestTelemetryGenerator:
    
    def test_generate_telemetry_data_structure(self):
        """Test that generated telemetry data has correct structure"""
        data = generate_telemetry_data()
        
        # Check required fields
        assert 'sat_id' in data
        assert 'orbit' in data
        assert 'region' in data
        assert 'link_stats' in data
        assert 'battery' in data
        assert 'timestamp' in data
        
        # Check data types
        assert isinstance(data['sat_id'], str)
        assert isinstance(data['orbit'], int)
        assert isinstance(data['region'], str)
        assert isinstance(data['link_stats'], dict)
        assert isinstance(data['battery'], float)
        assert isinstance(data['timestamp'], str)
        
    def test_generate_telemetry_data_values(self):
        """Test that generated values are within expected ranges"""
        data = generate_telemetry_data()
        
        # Check orbit range
        assert 100 <= data['orbit'] <= 999
        
        # Check region is valid
        assert data['region'] in REGIONS
        
        # Check battery range
        assert 0.0 <= data['battery'] <= 100.0
        
        # Check link stats
        link_stats = data['link_stats']
        assert 'latency_ms' in link_stats
        assert 'packet_loss_pct' in link_stats
        assert 'uplink_mbps' in link_stats
        assert 'downlink_mbps' in link_stats
        
        # Check latency range
        assert 1 <= link_stats['latency_ms'] <= 1000
        
        # Check packet loss range
        assert 0.0 <= link_stats['packet_loss_pct'] <= 10.0
        
        # Check bandwidth ranges
        assert 1.0 <= link_stats['uplink_mbps'] <= 1000.0
        assert 1.0 <= link_stats['downlink_mbps'] <= 1000.0
        
    def test_generate_telemetry_data_unique_satellites(self):
        """Test that different calls generate different satellite IDs"""
        data1 = generate_telemetry_data()
        data2 = generate_telemetry_data()
        
        # Satellite IDs should be different (with high probability)
        assert data1['sat_id'] != data2['sat_id']
        
    def test_generate_telemetry_data_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        data = generate_telemetry_data()
        timestamp = data['timestamp']
        
        # Check ISO format (YYYY-MM-DDTHH:MM:SS)
        import re
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        assert re.match(iso_pattern, timestamp)
        
    @patch('main.random.choice')
    def test_generate_telemetry_data_region_selection(self, mock_choice):
        """Test that region selection works correctly"""
        mock_choice.return_value = 'RU'
        data = generate_telemetry_data()
        
        assert data['region'] == 'RU'
        
    def test_generate_telemetry_data_json_serializable(self):
        """Test that generated data can be serialized to JSON"""
        data = generate_telemetry_data()
        
        # Should not raise exception
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        
        # Should be able to deserialize
        parsed_data = json.loads(json_str)
        assert parsed_data == data

if __name__ == '__main__':
    pytest.main([__file__])
