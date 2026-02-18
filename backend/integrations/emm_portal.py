"""
EMM Portal Connector
Pulls event management data from https://emm.usaac.army.mil/EMMPortal
"""

from .base_connector import BaseArmyConnector
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class EMMPortalConnector(BaseArmyConnector):
    """Connector for EMM (Event Management Module) Portal"""
    
    def __init__(self, cert_path: Optional[str] = None):
        super().__init__(
            base_url="https://emm.usaac.army.mil/EMMPortal",
            cert_path=cert_path,
            verify_ssl=True
        )
    
    def get_events(self, date_from: str, date_to: str,
                  event_type: Optional[str] = None,
                  rsid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get scheduled events
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            event_type: Event type filter
            rsid: Recruiting Station ID filter
            
        Returns:
            Dictionary with event data
        """
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        if event_type:
            params['event_type'] = event_type
        if rsid:
            params['rsid'] = rsid
        
        return self._make_request('api/events', params=params)
    
    def get_event_performance(self, event_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for specific event
        
        Args:
            event_id: Event identifier
            
        Returns:
            Dictionary with event performance data
        """
        return self._make_request(f'api/events/{event_id}/performance')
    
    def get_event_attendance(self, event_id: str) -> Dict[str, Any]:
        """
        Get attendance data for event
        
        Args:
            event_id: Event identifier
            
        Returns:
            Dictionary with attendance data
        """
        return self._make_request(f'api/events/{event_id}/attendance')
    
    def get_event_leads(self, event_id: str) -> Dict[str, Any]:
        """
        Get leads generated from event
        
        Args:
            event_id: Event identifier
            
        Returns:
            Dictionary with lead data
        """
        return self._make_request(f'api/events/{event_id}/leads')
    
    def get_event_roi(self, event_id: str) -> Dict[str, Any]:
        """
        Get ROI metrics for event
        
        Args:
            event_id: Event identifier
            
        Returns:
            Dictionary with ROI data
        """
        return self._make_request(f'api/events/{event_id}/roi')
    
    def get_event_calendar(self, rsid: Optional[str] = None,
                          fiscal_year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get event calendar
        
        Args:
            rsid: Recruiting Station ID filter
            fiscal_year: Fiscal year filter
            
        Returns:
            Dictionary with calendar data
        """
        params = {}
        if rsid:
            params['rsid'] = rsid
        if fiscal_year:
            params['fiscal_year'] = fiscal_year
        
        return self._make_request('api/calendar', params=params)
