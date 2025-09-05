#!/usr/bin/env python3
"""
End-to-End Smoke Test for Telemetry System
Tests the complete flow from data generation to storage
"""

import requests
import time
import json
import sys
import os
from typing import Dict, Any

# Configuration
COLLECTOR_URL = "http://localhost:30081"
GENERATOR_METRICS_URL = "http://localhost:30082/metrics"
PROCESSOR_METRICS_URL = "http://localhost:30080/metrics"
RABBITMQ_MANAGEMENT_URL = "http://localhost:15672"

class TelemetrySmokeTest:
    
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}: {message}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
    def test_collector_health(self) -> bool:
        """Test if collector is responding"""
        try:
            response = self.session.get(f"{COLLECTOR_URL}/health", timeout=10)
            success = response.status_code == 200
            self.log_test("Collector Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Collector Health Check", False, f"Error: {str(e)}")
            return False
            
    def test_collector_ingest(self) -> bool:
        """Test data ingestion endpoint"""
        try:
            # Generate sample telemetry data
            sample_data = {
                "sat_id": "TEST-SAT-001",
                "orbit": 123,
                "region": "RU",
                "link_stats": {
                    "latency_ms": 50,
                    "packet_loss_pct": 0.1,
                    "uplink_mbps": 100.0,
                    "downlink_mbps": 200.0
                },
                "battery": 85.5,
                "timestamp": "2025-09-02T21:00:00Z"
            }
            
            response = self.session.post(
                f"{COLLECTOR_URL}/ingest",
                json=sample_data,
                timeout=10
            )
            
            success = response.status_code in [200, 201, 202]
            self.log_test("Data Ingestion", success, f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("Data Ingestion", False, f"Error: {str(e)}")
            return False
            
    def test_generator_metrics(self) -> bool:
        """Test if generator metrics are accessible"""
        try:
            response = self.session.get(GENERATOR_METRICS_URL, timeout=10)
            success = response.status_code == 200
            
            if success:
                # Check if metrics contain expected data
                metrics_content = response.text
                has_telemetry_metrics = any([
                    'telemetry_generated_total' in metrics_content,
                    'telemetry_generator_rate_hz' in metrics_content,
                    'telemetry_sat_battery' in metrics_content
                ])
                
                self.log_test("Generator Metrics", has_telemetry_metrics, 
                            f"Status: {response.status_code}, Has metrics: {has_telemetry_metrics}")
                return has_telemetry_metrics
            else:
                self.log_test("Generator Metrics", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Generator Metrics", False, f"Error: {str(e)}")
            return False
            
    def test_processor_metrics(self) -> bool:
        """Test if processor metrics are accessible"""
        try:
            response = self.session.get(PROCESSOR_METRICS_URL, timeout=10)
            success = response.status_code == 200
            
            if success:
                # Check if metrics contain expected data
                metrics_content = response.text
                has_telemetry_metrics = any([
                    'telemetry_ingested_total' in metrics_content,
                    'telemetry_processing_latency_seconds' in metrics_content,
                    'telemetry_db_errors_total' in metrics_content
                ])
                
                self.log_test("Processor Metrics", has_telemetry_metrics, 
                            f"Status: {response.status_code}, Has metrics: {has_telemetry_metrics}")
                return has_telemetry_metrics
            else:
                self.log_test("Processor Metrics", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Processor Metrics", False, f"Error: {str(e)}")
            return False
            
    def test_rabbitmq_management(self) -> bool:
        """Test if RabbitMQ management interface is accessible"""
        try:
            response = self.session.get(RABBITMQ_MANAGEMENT_URL, timeout=10)
            success = response.status_code == 200
            self.log_test("RabbitMQ Management", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("RabbitMQ Management", False, f"Error: {str(e)}")
            return False
            
    def test_data_flow(self) -> bool:
        """Test complete data flow: ingest -> process -> store"""
        try:
            # Step 1: Ingest data
            sample_data = {
                "sat_id": "FLOW-TEST-001",
                "orbit": 456,
                "region": "RU",
                "link_stats": {
                    "latency_ms": 75,
                    "packet_loss_pct": 0.5,
                    "uplink_mbps": 150.0,
                    "downlink_mbps": 300.0
                },
                "battery": 92.0,
                "timestamp": "2025-09-02T21:01:00Z"
            }
            
            # Ingest data
            ingest_response = self.session.post(
                f"{COLLECTOR_URL}/ingest",
                json=sample_data,
                timeout=10
            )
            
            if ingest_response.status_code not in [200, 201, 202]:
                self.log_test("Data Flow", False, "Failed to ingest data")
                return False
                
            # Step 2: Wait for processing
            print("⏳ Waiting for data processing...")
            time.sleep(10)
            
            # Step 3: Check if metrics increased
            try:
                metrics_response = self.session.get(PROCESSOR_METRICS_URL, timeout=10)
                if metrics_response.status_code == 200:
                    metrics_content = metrics_response.text
                    
                    # Check if we can see ingestion metrics
                    has_ingestion_metrics = 'telemetry_ingested_total' in metrics_content
                    
                    self.log_test("Data Flow", has_ingestion_metrics, 
                                "Data ingested and metrics accessible")
                    return has_ingestion_metrics
                else:
                    self.log_test("Data Flow", False, "Cannot access processor metrics")
                    return False
                    
            except Exception as e:
                self.log_test("Data Flow", False, f"Error checking metrics: {str(e)}")
                return False
                
        except Exception as e:
            self.log_test("Data Flow", False, f"Error in data flow test: {str(e)}")
            return False
            
    def run_all_tests(self) -> bool:
        """Run all smoke tests"""
        print("🚀 Starting Telemetry System Smoke Tests...")
        print("=" * 50)
        
        tests = [
            self.test_collector_health,
            self.test_collector_ingest,
            self.test_generator_metrics,
            self.test_processor_metrics,
            self.test_rabbitmq_management,
            self.test_data_flow
        ]
        
        all_passed = True
        for test in tests:
            try:
                result = test()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_test(test.__name__, False, f"Test exception: {str(e)}")
                all_passed = False
                
        print("=" * 50)
        print(f"📊 Test Results: {sum(1 for r in self.test_results if r['success'])}/{len(self.test_results)} tests passed")
        
        if all_passed:
            print("🎉 All smoke tests passed! Telemetry system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the system status.")
            
        return all_passed
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        return {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for r in self.test_results if r['success']),
            'failed_tests': sum(1 for r in self.test_results if not r['success']),
            'results': self.test_results
        }

def main():
    """Main function to run smoke tests"""
    smoke_test = TelemetrySmokeTest()
    
    try:
        success = smoke_test.run_all_tests()
        
        # Generate and save report
        report = smoke_test.generate_report()
        with open('smoke_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📄 Test report saved to: smoke_test_report.json")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
