"""
Vantage Data Connector
Pulls analytics and performance data from https://vantage.army.mil
"""

from .base_connector import BaseArmyConnector
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VantageConnector(BaseArmyConnector):
    """Connector for Army Vantage system"""
    
    def __init__(self, cert_path: Optional[str] = None):
        super().__init__(
            base_url="https://vantage.army.mil",
            cert_path=cert_path,
            verify_ssl=True
        )
    
    def get_analytics_data(self, report_type: str, 
                          date_range: Dict[str, str]) -> Dict[str, Any]:
        """
        Get analytics report data from Vantage
        
        Args:
            report_type: Type of report (e.g., 'recruiting', 'market', 'performance')
            date_range: Dictionary with 'start' and 'end' dates
            
        Returns:
            Dictionary with analytics data
        """
        params = {
            'report_type': report_type,
            'start_date': date_range.get('start'),
            'end_date': date_range.get('end')
        }
        
        return self._make_request('api/analytics', params=params)
    
    def get_market_potential(self, zipcode: Optional[str] = None,
                            cbsa: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market potential data by geography
        
        Args:
            zipcode: ZIP code filter
            cbsa: CBSA (Core Based Statistical Area) filter
            
        Returns:
            Dictionary with market potential data
        """
        params = {}
        if zipcode:
            params['zipcode'] = zipcode
        if cbsa:
            params['cbsa'] = cbsa
        
        return self._make_request('api/market-potential', params=params)
    
    def get_performance_metrics(self, unit_type: str, unit_id: str) -> Dict[str, Any]:
        """
        Get unit performance metrics
        
        Args:
            unit_type: Type of unit ('brigade', 'battalion', 'company', 'station')
            unit_id: Unit identifier
            
        Returns:
            Dictionary with performance metrics
        """
        params = {
            'unit_type': unit_type,
            'unit_id': unit_id
        }
        
        return self._make_request('api/performance', params=params)
    
    def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Any]:
        """
        Get pre-configured dashboard data
        
        Args:
            dashboard_name: Name of dashboard
            
        Returns:
            Dictionary with dashboard data
        """
        return self._make_request(f'api/dashboards/{dashboard_name}')
