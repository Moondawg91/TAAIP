"""
Integration Configuration
Stores connection settings for Army systems
"""

import os
from typing import Optional

# CAC Certificate path (Common Access Card for authentication)
CAC_CERT_PATH = os.getenv('CAC_CERT_PATH', None)

# System configurations
SYSTEMS = {
    'ikrome': {
        'enabled': True,
        'base_url': 'https://ikrome.usaas.army.mil',
        'cert_required': True,
        'description': 'iKrome recruiting system'
    },
    'emm_portal': {
        'enabled': True,
        'base_url': 'https://emm.usaac.army.mil/EMMPortal',
        'cert_required': True,
        'description': 'Event Management Module Portal'
    },
    'vantage': {
        'enabled': True,
        'base_url': 'https://vantage.army.mil',
        'cert_required': True,
        'description': 'Army Vantage analytics platform'
    },
    'bizone': {
        'enabled': True,
        'base_url': 'https://bizone-prod.usarec.army.mil',
        'cert_required': True,
        'description': 'BIZone business intelligence'
    },
    'sharepoint': {
        'enabled': True,
        'base_url': 'https://army.sharepoint-mil.us/teams/TR-USREC-G2-ReportZone',
        'cert_required': True,
        'description': 'G2 Report Zone SharePoint'
    }
}

# Data refresh intervals (in seconds)
REFRESH_INTERVALS = {
    'real_time': 60,        # 1 minute for critical metrics
    'high_frequency': 300,   # 5 minutes for dashboards
    'medium_frequency': 1800, # 30 minutes for reports
    'low_frequency': 3600    # 1 hour for analytics
}

# API endpoint mappings (these would need to be updated with actual endpoints)
API_ENDPOINTS = {
    'ikrome': {
        'recruiters': '/api/recruiters',
        'leads': '/api/leads',
        'enlistments': '/api/enlistments',
        'mission': '/api/mission'
    },
    'vantage': {
        'analytics': '/api/analytics',
        'market_potential': '/api/market-potential',
        'performance': '/api/performance',
        'dashboards': '/api/dashboards'
    },
    'bizone': {
        'reports': '/api/reports',
        'funnel': '/api/funnel',
        'conversions': '/api/conversions',
        'kpi': '/api/kpi-dashboard',
        'trends': '/api/trends'
    },
    'emm_portal': {
        'events': '/api/events',
        'calendar': '/api/calendar'
    },
    'sharepoint': {
        'reports': '/_api/web/lists/getbytitle(\'Reports\')/items'
    }
}

# Cache settings
CACHE_ENABLED = True
CACHE_TTL = {
    'real_time': 60,
    'high_frequency': 300,
    'medium_frequency': 1800,
    'low_frequency': 3600
}
