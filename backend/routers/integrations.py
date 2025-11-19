"""
System Integration API Router
Endpoints for testing and managing Army system connections
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import io

from ..integrations.manager import get_integration_manager
from ..integrations.config import SYSTEMS

router = APIRouter()


class ConnectionTestResponse(BaseModel):
    system: str
    connected: bool
    timestamp: str
    error: Optional[str] = None


class IntegrationRequest(BaseModel):
    system: str
    operation: str
    parameters: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_integration_status():
    """Get status of all Army system integrations"""
    manager = get_integration_manager()
    connection_tests = manager.test_all_connections()
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'systems': []
    }
    
    for system_name, config in SYSTEMS.items():
        system_status = {
            'name': system_name,
            'description': config['description'],
            'base_url': config['base_url'],
            'enabled': config['enabled'],
            'connected': connection_tests.get(system_name, False),
            'cert_required': config['cert_required']
        }
        status['systems'].append(system_status)
    
    return {
        'status': 'ok',
        'data': status
    }


@router.post("/test/{system_name}")
async def test_system_connection(system_name: str):
    """Test connection to specific Army system"""
    if system_name not in SYSTEMS:
        raise HTTPException(status_code=404, detail=f"System '{system_name}' not found")
    
    manager = get_integration_manager()
    
    if system_name not in manager.connectors:
        raise HTTPException(status_code=503, detail=f"System '{system_name}' not initialized")
    
    try:
        connector = manager.connectors[system_name]
        connected = connector.test_connection()
        
        return {
            'status': 'ok',
            'system': system_name,
            'connected': connected,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'system': system_name,
            'connected': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@router.get("/ikrome/enlistments")
async def get_ikrome_enlistments(fiscal_year: int = 2025, rsid: Optional[str] = None):
    """Get enlistment data from iKrome"""
    manager = get_integration_manager()
    result = manager.get_enlistment_data(fiscal_year, rsid)
    
    if not result.get('success'):
        raise HTTPException(status_code=503, detail=result.get('error', 'iKrome unavailable'))
    
    return {
        'status': 'ok',
        'source': 'ikrome',
        'data': result
    }


@router.get("/ikrome/mission")
async def get_ikrome_mission(fiscal_year: int = 2025, rsid: Optional[str] = None):
    """Get mission data from iKrome"""
    manager = get_integration_manager()
    result = manager.get_mission_data(fiscal_year, rsid)
    
    if not result.get('success'):
        raise HTTPException(status_code=503, detail=result.get('error', 'iKrome unavailable'))
    
    return {
        'status': 'ok',
        'source': 'ikrome',
        'data': result
    }


@router.get("/vantage/market")
async def get_vantage_market(zipcode: Optional[str] = None, cbsa: Optional[str] = None):
    """Get market potential from Vantage"""
    manager = get_integration_manager()
    result = manager.get_market_data(zipcode, cbsa)
    
    if not result.get('success'):
        raise HTTPException(status_code=503, detail=result.get('error', 'Vantage unavailable'))
    
    return {
        'status': 'ok',
        'source': 'vantage',
        'data': result
    }


@router.get("/sharepoint/reports")
async def get_sharepoint_reports():
    """Get latest reports from SharePoint G2 Zone"""
    manager = get_integration_manager()
    result = manager.get_latest_reports()
    
    if not result.get('success'):
        raise HTTPException(status_code=503, detail=result.get('error', 'SharePoint unavailable'))
    
    return {
        'status': 'ok',
        'source': 'sharepoint_g2',
        'data': result
    }


@router.get("/dashboard/{dashboard_type}")
async def get_integrated_dashboard(dashboard_type: str, rsid: Optional[str] = None):
    """
    Get dashboard data from multiple integrated sources
    
    dashboard_type: recruiting_funnel, analytics, events, etc.
    """
    manager = get_integration_manager()
    
    filters = {}
    if rsid:
        filters['rsid'] = rsid
    
    # This would be async in production
    result = await manager.get_dashboard_data(dashboard_type, filters)
    
    return {
        'status': 'ok',
        'dashboard_type': dashboard_type,
        'data': result
    }


# ===== SharePoint File Management Endpoints =====

@router.get("/sharepoint/browse")
async def browse_sharepoint(path: str = "/") -> Dict[str, Any]:
    """Browse SharePoint folders and files"""
    try:
        manager = get_integration_manager()
        sharepoint = manager.connectors.get('sharepoint')
        
        if not sharepoint:
            raise HTTPException(status_code=503, detail="SharePoint integration not available")
        
        # Mock data for demonstration - replace with actual SharePoint API calls
        files = [
            {
                "id": "file_001",
                "name": "Monthly_Report_Nov_2024.pdf",
                "type": "file",
                "size": 2457600,
                "modified": "2024-11-18T10:30:00Z",
                "modifiedBy": "John Smith",
                "path": path + "/Monthly_Report_Nov_2024.pdf",
                "url": "https://army.sharepoint-mil.us/...",
                "fileType": "application/pdf"
            },
            {
                "id": "file_002",
                "name": "Recruiting_Stats_Q4.xlsx",
                "type": "file",
                "size": 1048576,
                "modified": "2024-11-17T14:20:00Z",
                "modifiedBy": "Jane Doe",
                "path": path + "/Recruiting_Stats_Q4.xlsx",
                "url": "https://army.sharepoint-mil.us/...",
                "fileType": "application/vnd.ms-excel"
            },
            {
                "id": "file_003",
                "name": "Training_Video.mp4",
                "type": "file",
                "size": 15728640,
                "modified": "2024-11-16T09:15:00Z",
                "modifiedBy": "Mike Johnson",
                "path": path + "/Training_Video.mp4",
                "url": "https://army.sharepoint-mil.us/...",
                "fileType": "video/mp4"
            },
            {
                "id": "file_004",
                "name": "G2_Intelligence_Brief.pptx",
                "type": "file",
                "size": 5242880,
                "modified": "2024-11-15T16:45:00Z",
                "modifiedBy": "Sarah Wilson",
                "path": path + "/G2_Intelligence_Brief.pptx",
                "url": "https://army.sharepoint-mil.us/...",
                "fileType": "application/vnd.ms-powerpoint"
            }
        ]
        
        folders = [
            {
                "id": "folder_001",
                "name": "Reports",
                "path": path + "/Reports" if path != "/" else "/Reports",
                "files": [],
                "subfolders": []
            },
            {
                "id": "folder_002",
                "name": "Training Materials",
                "path": path + "/Training Materials" if path != "/" else "/Training Materials",
                "files": [],
                "subfolders": []
            },
            {
                "id": "folder_003",
                "name": "G2 Intelligence",
                "path": path + "/G2 Intelligence" if path != "/" else "/G2 Intelligence",
                "files": [],
                "subfolders": []
            }
        ] if path == "/" else []
        
        return {
            "status": "ok",
            "path": path,
            "files": files,
            "folders": folders,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sharepoint/download/{file_id}")
async def download_sharepoint_file(file_id: str):
    """Download a file from SharePoint"""
    try:
        # Mock file download - replace with actual SharePoint API call
        # In production: sharepoint.download_file(file_id)
        content = b"Mock file content for demonstration purposes. This would be the actual file content from SharePoint."
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=downloaded_file_{file_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sharepoint/upload")
async def upload_to_sharepoint(
    files: List[UploadFile] = File(...),
    path: str = "/"
) -> Dict[str, Any]:
    """Upload files to SharePoint"""
    try:
        uploaded_files = []
        
        for file in files:
            content = await file.read()
            # Mock upload - replace with actual SharePoint API call
            # In production: sharepoint.upload_file(file.filename, content, path)
            uploaded_files.append({
                "name": file.filename,
                "size": len(content),
                "path": f"{path}/{file.filename}",
                "content_type": file.content_type
            })
        
        return {
            "status": "ok",
            "message": f"Uploaded {len(uploaded_files)} file(s) to SharePoint",
            "files": uploaded_files,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sharepoint/share")
async def share_sharepoint_file(
    file_id: str,
    emails: List[str]
) -> Dict[str, Any]:
    """Share a SharePoint file with specific users"""
    try:
        # Mock sharing - replace with actual SharePoint API call
        # In production: sharepoint.share_file(file_id, emails)
        return {
            "status": "ok",
            "message": f"File shared with {len(emails)} user(s)",
            "file_id": file_id,
            "shared_with": emails,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sharepoint/delete/{file_id}")
async def delete_sharepoint_file(file_id: str) -> Dict[str, Any]:
    """Delete a file from SharePoint"""
    try:
        # Mock deletion - replace with actual SharePoint API call
        # In production: sharepoint.delete_file(file_id)
        return {
            "status": "ok",
            "message": "File deleted successfully from SharePoint",
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sharepoint/create-folder")
async def create_sharepoint_folder(
    folder_name: str,
    path: str = "/"
) -> Dict[str, Any]:
    """Create a new folder in SharePoint"""
    try:
        # Mock folder creation - replace with actual SharePoint API call
        new_folder_path = f"{path}/{folder_name}"
        
        return {
            "status": "ok",
            "message": "Folder created successfully",
            "folder_name": folder_name,
            "path": new_folder_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

