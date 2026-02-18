"""
Integration Manager
Orchestrates data pulls from all Army systems
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .ikrome import iKromeConnector
from .emm_portal import EMMPortalConnector
from .vantage import VantageConnector
from .bizone import BIZoneConnector
from .sharepoint import SharePointConnector
from .config import CAC_CERT_PATH, SYSTEMS

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Manages all Army system integrations"""
    
    def __init__(self, cert_path: Optional[str] = None):
        self.cert_path = cert_path or CAC_CERT_PATH
        self.connectors = {}
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize all enabled connectors"""
        try:
            if SYSTEMS['ikrome']['enabled']:
                self.connectors['ikrome'] = iKromeConnector(self.cert_path)
                logger.info("iKrome connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize iKrome: {e}")
        
        try:
            if SYSTEMS['emm_portal']['enabled']:
                self.connectors['emm_portal'] = EMMPortalConnector(self.cert_path)
                logger.info("EMM Portal connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize EMM Portal: {e}")
        
        try:
            if SYSTEMS['vantage']['enabled']:
                self.connectors['vantage'] = VantageConnector(self.cert_path)
                logger.info("Vantage connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Vantage: {e}")
        
        try:
            if SYSTEMS['bizone']['enabled']:
                self.connectors['bizone'] = BIZoneConnector(self.cert_path)
                logger.info("BIZone connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize BIZone: {e}")
        
        try:
            if SYSTEMS['sharepoint']['enabled']:
                self.connectors['sharepoint'] = SharePointConnector(self.cert_path)
                logger.info("SharePoint connector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SharePoint: {e}")
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test connectivity to all systems"""
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = connector.test_connection()
                logger.info(f"{name}: {'Connected' if results[name] else 'Failed'}")
            except Exception as e:
                results[name] = False
                logger.error(f"{name} connection test failed: {e}")
        return results
    
    async def get_dashboard_data(self, dashboard_type: str, 
                                 filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data from all relevant systems
        
        Args:
            dashboard_type: Type of dashboard ('recruiting', 'analytics', 'events', etc.)
            filters: Optional filters (rsid, date_range, etc.)
            
        Returns:
            Aggregated dashboard data from multiple sources
        """
        filters = filters or {}
        data = {
            'dashboard_type': dashboard_type,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # Fetch data based on dashboard type
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            if dashboard_type == 'recruiting_funnel':
                if 'bizone' in self.connectors:
                    future = executor.submit(
                        self.connectors['bizone'].get_recruiting_funnel_data,
                        filters.get('rsid'),
                        filters.get('fiscal_year')
                    )
                    futures.append(('bizone_funnel', future))
            
            elif dashboard_type == 'analytics':
                if 'vantage' in self.connectors:
                    future = executor.submit(
                        self.connectors['vantage'].get_analytics_data,
                        'recruiting',
                        filters.get('date_range', {})
                    )
                    futures.append(('vantage_analytics', future))
            
            elif dashboard_type == 'events':
                if 'emm_portal' in self.connectors:
                    future = executor.submit(
                        self.connectors['emm_portal'].get_events,
                        filters.get('date_from', '2025-01-01'),
                        filters.get('date_to', '2025-12-31'),
                        filters.get('event_type'),
                        filters.get('rsid')
                    )
                    futures.append(('emm_events', future))
            
            # Collect results
            for source_name, future in futures:
                try:
                    result = future.result(timeout=30)
                    data['sources'][source_name] = result
                except Exception as e:
                    logger.error(f"Failed to fetch {source_name}: {e}")
                    data['sources'][source_name] = {'success': False, 'error': str(e)}
        
        return data
    
    def get_enlistment_data(self, fiscal_year: int, rsid: Optional[str] = None) -> Dict[str, Any]:
        """Get enlistment data from iKrome"""
        if 'ikrome' not in self.connectors:
            return {'success': False, 'error': 'iKrome not available'}
        
        return self.connectors['ikrome'].get_enlistment_data(fiscal_year, rsid)
    
    def get_mission_data(self, fiscal_year: int, rsid: Optional[str] = None) -> Dict[str, Any]:
        """Get mission data from iKrome"""
        if 'ikrome' not in self.connectors:
            return {'success': False, 'error': 'iKrome not available'}
        
        return self.connectors['ikrome'].get_mission_data(fiscal_year, None, rsid)
    
    def get_market_data(self, zipcode: Optional[str] = None, cbsa: Optional[str] = None) -> Dict[str, Any]:
        """Get market potential from Vantage"""
        if 'vantage' not in self.connectors:
            return {'success': False, 'error': 'Vantage not available'}
        
        return self.connectors['vantage'].get_market_potential(zipcode, cbsa)
    
    def get_latest_reports(self) -> Dict[str, Any]:
        """Get latest reports from SharePoint"""
        if 'sharepoint' not in self.connectors:
            return {'success': False, 'error': 'SharePoint not available'}
        
        return self.connectors['sharepoint'].get_latest_sitrep()
    
    def close_all(self):
        """Close all connector sessions"""
        for connector in self.connectors.values():
            try:
                connector.close()
            except:
                pass


# Singleton instance
_integration_manager = None

def get_integration_manager(cert_path: Optional[str] = None) -> IntegrationManager:
    """Get or create integration manager instance"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager(cert_path)
    return _integration_manager
