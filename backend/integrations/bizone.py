"""
BIZone Data Connector  
Pulls business intelligence data from https://bizone-prod.usarec.army.mil
"""

from .base_connector import BaseArmyConnector
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BIZoneConnector(BaseArmyConnector):
    """Connector for BIZone Production system"""
    
    def __init__(self, cert_path: Optional[str] = None):
        super().__init__(
            base_url="https://bizone-prod.usarec.army.mil",
            cert_path=cert_path,
            verify_ssl=True
        )
    
    def get_bi_report(self, report_id: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get Business Intelligence report
        
        Args:
            report_id: Report identifier
            parameters: Optional report parameters
            
        Returns:
            Dictionary with report data
        """
        params = parameters or {}
        return self._make_request(f'api/reports/{report_id}', params=params)
    
    def get_recruiting_funnel_data(self, rsid: Optional[str] = None,
                                  fiscal_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get recruiting funnel metrics
        
        Args:
            rsid: Recruiting Station ID filter
            fiscal_year: Fiscal year filter
            
        Returns:
            Dictionary with funnel data
        """
        params = {}
        if rsid:
            params['rsid'] = rsid
        if fiscal_year:
            params['fiscal_year'] = fiscal_year
        
        return self._make_request('api/funnel', params=params)
    
    def get_conversion_rates(self, stage_from: str, stage_to: str,
                            date_range: Dict[str, str]) -> Dict[str, Any]:
        """
        Get conversion rates between funnel stages
        
        Args:
            stage_from: Starting stage
            stage_to: Ending stage
            date_range: Dictionary with 'start' and 'end' dates
            
        Returns:
            Dictionary with conversion data
        """
        params = {
            'stage_from': stage_from,
            'stage_to': stage_to,
            'start_date': date_range.get('start'),
            'end_date': date_range.get('end')
        }
        
        return self._make_request('api/conversions', params=params)
    
    def get_kpi_dashboard(self, dashboard_type: str = 'executive') -> Dict[str, Any]:
        """
        Get KPI dashboard data
        
        Args:
            dashboard_type: Type of dashboard ('executive', 'tactical', 'operational')
            
        Returns:
            Dictionary with KPI data
        """
        params = {'type': dashboard_type}
        return self._make_request('api/kpi-dashboard', params=params)
    
    def get_historical_trends(self, metric: str, periods: int = 12) -> Dict[str, Any]:
        """
        Get historical trend data
        
        Args:
            metric: Metric name (e.g., 'enlistments', 'leads', 'contracts')
            periods: Number of periods to retrieve
            
        Returns:
            Dictionary with trend data
        """
        params = {
            'metric': metric,
            'periods': periods
        }
        
        return self._make_request('api/trends', params=params)
