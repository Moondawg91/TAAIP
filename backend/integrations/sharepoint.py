"""
SharePoint G2 Report Zone Connector
Pulls reports from https://army.sharepoint-mil.us/teams/TR-USREC-G2-ReportZone
"""

from .base_connector import BaseArmyConnector
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class SharePointConnector(BaseArmyConnector):
    """Connector for Army SharePoint G2 Report Zone"""
    
    def __init__(self, cert_path: Optional[str] = None):
        super().__init__(
            base_url="https://army.sharepoint-mil.us/teams/TR-USREC-G2-ReportZone",
            cert_path=cert_path,
            verify_ssl=True
        )
    
    def get_g2_reports(self, report_category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get G2 reports list
        
        Args:
            report_category: Filter by category
            
        Returns:
            Dictionary with reports list
        """
        params = {}
        if report_category:
            params['category'] = report_category
        
        return self._make_request('_api/web/lists/getbytitle(\'Reports\')/items', params=params)
    
    def get_report_content(self, report_id: str) -> Dict[str, Any]:
        """
        Get specific report content
        
        Args:
            report_id: Report identifier
            
        Returns:
            Dictionary with report content
        """
        return self._make_request(f'_api/web/lists/getbytitle(\'Reports\')/items({report_id})')
    
    def get_latest_sitrep(self) -> Dict[str, Any]:
        """
        Get latest SITREP (Situation Report)
        
        Returns:
            Dictionary with SITREP data
        """
        params = {
            '$top': 1,
            '$orderby': 'Created desc',
            '$filter': 'ContentType eq \'SITREP\''
        }
        
        return self._make_request('_api/web/lists/getbytitle(\'Reports\')/items', params=params)
    
    def get_weekly_metrics(self) -> Dict[str, Any]:
        """
        Get weekly recruiting metrics
        
        Returns:
            Dictionary with weekly metrics
        """
        params = {
            '$filter': 'ContentType eq \'Weekly Metrics\'',
            '$orderby': 'Created desc',
            '$top': 1
        }
        
        return self._make_request('_api/web/lists/getbytitle(\'Reports\')/items', params=params)
    
    def get_monthly_summary(self, month: int, year: int) -> Dict[str, Any]:
        """
        Get monthly summary report
        
        Args:
            month: Month number (1-12)
            year: Year
            
        Returns:
            Dictionary with monthly summary
        """
        params = {
            '$filter': f'ContentType eq \'Monthly Summary\' and Month eq {month} and Year eq {year}'
        }
        
        return self._make_request('_api/web/lists/getbytitle(\'Reports\')/items', params=params)
    
    def search_reports(self, query: str) -> Dict[str, Any]:
        """
        Search reports by keyword
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with search results
        """
        params = {
            '$filter': f'substringof(\'{query}\', Title)'
        }
        
        return self._make_request('_api/web/lists/getbytitle(\'Reports\')/items', params=params)
