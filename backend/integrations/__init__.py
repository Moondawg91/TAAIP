"""
TAAIP Data Integration Framework
Connects to Army recruiting systems for real-time data
"""

from .ikrome import iKromeConnector
from .emm_portal import EMMPortalConnector
from .vantage import VantageConnector
from .bizone import BIZoneConnector
from .sharepoint import SharePointConnector

__all__ = [
    'iKromeConnector',
    'EMMPortalConnector',
    'VantageConnector',
    'BIZoneConnector',
    'SharePointConnector'
]
