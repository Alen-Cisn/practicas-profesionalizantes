"""
HTML Test Report Generator for E2E Tests
Generates comprehensive HTML reports with screenshots and logs

T067: HTML report generator with screenshots and logs
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json


class TestReportGenerator:
    """Generate HTML test reports with screenshots and execution logs"""
    
    def __init__(self, output_dir: str = "tests/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(
        self,
        test_results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        screenshots_dir: str = "tests/screenshots",
        videos_dir: str = "tests/videos"
    ) -> Path:
        """
        Generate HTML report from test results.
        
        Args:
            test_results: List of test result dictionaries
            summary: Test suite summary statistics
            screenshots_dir: Directory containing test screenshots
            videos_dir: Directory containing test videos
            
        Returns:
            Path to generated HTML report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"test_report_{timestamp}.html"
        
        html_content = self._build_html(test_results, summary, screenshots_dir, videos_dir)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _build_html(
        self,
        test_results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        screenshots_dir: str,
        videos_dir: str
    ) -> str:
        """Build complete HTML report"""
        
        # Calculate statistics
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get('passed', False))
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Build test result rows
        result_rows = []
        for result in test_results:
            status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
            status_class = "pass" if result.get('passed', False) else "fail"
            
            screenshot_link = ""
            if result.get('screenshot_path'):
                screenshot_link = f'<a href="{result["screenshot_path"]}" target="_blank">View</a>'
            
            video_link = ""
            if result.get('video_path'):
                video_link = f'<a href="{result["video_path"]}" target="_blank">View</a>'
            
            error_msg = result.get('error_message', '-')
            if error_msg and len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            
            result_rows.append(f'''
                <tr class="{status_class}">
                    <td>{result.get('test_name', 'Unknown')}</td>
                    <td class="status">{status}</td>
                    <td>{result.get('execution_time', 0):.2f}s</td>
                    <td>{error_msg}</td>
                    <td>{screenshot_link}</td>
                    <td>{video_link}</td>
                </tr>
            ''')
        
        # Build HTML
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2E Test Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .metric {{
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #6c757d;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric.pass .metric-value {{ color: #28a745; }}
        .metric.fail .metric-value {{ color: #dc3545; }}
        .metric.rate .metric-value {{ color: #667eea; }}
        
        .results {{
            padding: 30px;
        }}
        
        .results h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #f8f9fa;
        }}
        
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        tr.pass {{
            background: #f0fff4;
        }}
        
        tr.fail {{
            background: #fff5f5;
        }}
        
        tr:hover {{
            background: #f1f3f5;
        }}
        
        .status {{
            font-weight: 600;
        }}
        
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 E2E Test Report</h1>
            <div class="subtitle">Historical Term Analyzer - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
        
        <div class="summary">
            <div class="metric pass">
                <div class="metric-value">{passed}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric fail">
                <div class="metric-value">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Total</div>
            </div>
            <div class="metric rate">
                <div class="metric-value">{pass_rate:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
        </div>
        
        <div class="results">
            <h2>Test Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Error Message</th>
                        <th>Screenshot</th>
                        <th>Video</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(result_rows)}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            Generated by Historical Term Analyzer E2E Test Suite
        </div>
    </div>
</body>
</html>'''
        
        return html


def generate_test_report(results_json_path: str, output_dir: str = "tests/reports") -> Path:
    """
    Convenience function to generate report from JSON results file.
    
    Args:
        results_json_path: Path to test results JSON file
        output_dir: Output directory for HTML report
        
    Returns:
        Path to generated HTML report
    """
    with open(results_json_path, 'r') as f:
        data = json.load(f)
    
    generator = TestReportGenerator(output_dir)
    return generator.generate_report(
        test_results=data.get('results', []),
        summary=data.get('summary', {})
    )


if __name__ == "__main__":
    # Example usage
    sample_results = [
        {
            "test_name": "test_complete_analysis_workflow",
            "passed": True,
            "execution_time": 45.2,
            "screenshot_path": "tests/screenshots/test_1.png"
        },
        {
            "test_name": "test_concurrent_analyses",
            "passed": False,
            "execution_time": 120.5,
            "error_message": "Timeout waiting for second analysis",
            "screenshot_path": "tests/screenshots/test_2.png",
            "video_path": "tests/videos/test_2.webm"
        }
    ]
    
    generator = TestReportGenerator()
    report_path = generator.generate_report(sample_results, {})
    print(f"Sample report generated: {report_path}")
