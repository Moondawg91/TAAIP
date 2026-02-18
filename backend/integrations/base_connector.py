"""
Base Connector for Army Systems
Handles common authentication and data retrieval patterns
"""

import requests
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class BaseArmyConnector:
    """Base class for Army system connectors"""
    
    def __init__(self, base_url: str, cert_path: Optional[str] = None, 
                 verify_ssl: bool = True):
        self.base_url = base_url
        self.cert_path = cert_path
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        
        # Configure session for CAC authentication if cert provided
        if cert_path:
            self.session.cert = cert_path
        
        self.session.verify = verify_ssl
        
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Army system"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"Making {method} request to {url}")
            
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return {
                    'success': True,
                    'data': response.json(),
                    'timestamp': datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'data': response.text,
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_connection(self) -> bool:
        """Test if connection to system is working"""
        try:
            response = self.session.head(self.base_url, timeout=10)
            return response.status_code < 500
        except:
            return False
    
    def close(self):
        """Close the session"""
        self.session.close()
