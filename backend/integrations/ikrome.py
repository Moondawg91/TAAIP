"""
iKrome Data Connector
Pulls data from https://ikrome.usaas.army.mil and recruiter zone
"""

from .base_connector import BaseArmyConnector
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class iKromeConnector(BaseArmyConnector):
    """Connector for iKrome system"""
    
    def __init__(self, cert_path: Optional[str] = None):
        super().__init__(
            base_url="https://ikrome.usaas.army.mil",
            cert_path=cert_path,
            verify_ssl=True
        )
        self.recruiter_zone_url = "https://ikrome.ussaac.army.mil/group.recruiterzone"
    
    def get_recruiter_data(self, rsid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recruiter performance data
        
        Args:
            rsid: Recruiting Station ID filter
            
        Returns:
            Dictionary with recruiter data
        """
        params = {}
        if rsid:
            params['rsid'] = rsid
        
        return self._make_request('api/recruiters', params=params)
    
    def get_lead_data(self, date_from: str, date_to: str, 
                      rsid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get lead tracking data
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            rsid: Recruiting Station ID filter
            
        Returns:
            Dictionary with lead data
        """
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        if rsid:
            params['rsid'] = rsid
        
        return self._make_request('api/leads', params=params)
    
    def get_enlistment_data(self, fiscal_year: int, 
                           rsid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get enlistment contracts data
        
        Args:
            fiscal_year: Fiscal year (e.g., 2025)
            rsid: Recruiting Station ID filter
            
        Returns:
            Dictionary with enlistment data
        """
        params = {'fiscal_year': fiscal_year}
        if rsid:
            params['rsid'] = rsid
        
        return self._make_request('api/enlistments', params=params)
    
    def get_mission_data(self, fiscal_year: int, month: Optional[int] = None,
                        rsid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get mission goals and achievements
        
        Args:
            fiscal_year: Fiscal year
            month: Month number (1-12) for specific month, None for YTD
            rsid: Recruiting Station ID filter
            
        Returns:
            Dictionary with mission data
        """
        params = {'fiscal_year': fiscal_year}
        if month:
            params['month'] = month
        if rsid:
            params['rsid'] = rsid
        
        return self._make_request('api/mission', params=params)
    
    def get_recruiter_zone_updates(self) -> Dict[str, Any]:
        """
        Get latest updates from Recruiter Zone
        
        Returns:
            Dictionary with zone updates and announcements
        """
        # This would need specific endpoint info from recruiter zone
        return {
            'success': True,
            'data': {
                'message': 'Recruiter Zone integration pending - needs specific API endpoints'
            }
        }
