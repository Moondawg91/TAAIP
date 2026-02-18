# SharePoint Integration Guide

## Overview

The TAAIP (Talent Acquisition Analytics and Intelligence Platform) now includes full SharePoint integration for file management, enabling users to browse, upload, download, share, and organize files from the Army G2 Report Zone SharePoint site directly within the application.

## Features

### 1. **File Browsing**
- Navigate through SharePoint folders
- View file metadata (name, size, modified date, modified by)
- Search files by name
- Breadcrumb navigation for easy folder traversal
- File type icons (PDF, Excel, PowerPoint, Video, etc.)

### 2. **File Operations**
- **Upload**: Upload multiple files to any SharePoint folder
- **Download**: Download individual files or selected files in bulk
- **Share**: Share files with other users via email
- **Delete**: Remove files from SharePoint
- **Create Folders**: Organize content by creating new folders

### 3. **User Interface**
- Clean, Army Vantage-themed interface (Black/Gray/Yellow)
- Responsive table layout with checkboxes for bulk actions
- Real-time search filtering
- Modal dialogs for upload and share operations
- Integrated into main navigation under "Operations > SharePoint Files"

## Accessing SharePoint Integration

### From the Main Menu
1. Click the menu dropdown in the top right
2. Navigate to **Operations** section
3. Click **SharePoint Files**

### Direct Navigation
The SharePoint Integration component is accessible at the `/sharepoint` route within the application.

## API Endpoints

All SharePoint API endpoints are available under `/api/v2/integrations/sharepoint/`

### Browse Files and Folders
```http
GET /api/v2/integrations/sharepoint/browse?path=/
```

**Response:**
```json
{
  "status": "ok",
  "path": "/",
  "files": [
    {
      "id": "file_001",
      "name": "Monthly_Report_Nov_2024.pdf",
      "type": "file",
      "size": 2457600,
      "modified": "2024-11-18T10:30:00Z",
      "modifiedBy": "John Smith",
      "path": "/Monthly_Report_Nov_2024.pdf",
      "url": "https://army.sharepoint-mil.us/...",
      "fileType": "application/pdf"
    }
  ],
  "folders": [
    {
      "id": "folder_001",
      "name": "Reports",
      "path": "/Reports",
      "files": [],
      "subfolders": []
    }
  ],
  "timestamp": "2024-11-19T13:50:12Z"
}
```

### Download File
```http
GET /api/v2/integrations/sharepoint/download/{file_id}
```

Returns the file as a binary stream with appropriate `Content-Disposition` header.

### Upload Files
```http
POST /api/v2/integrations/sharepoint/upload
Content-Type: multipart/form-data

files: [file1, file2, ...]
path: /target/folder
```

**Response:**
```json
{
  "status": "ok",
  "message": "Uploaded 2 file(s) to SharePoint",
  "files": [
    {
      "name": "document.pdf",
      "size": 1048576,
      "path": "/target/folder/document.pdf",
      "content_type": "application/pdf"
    }
  ],
  "timestamp": "2024-11-19T13:50:12Z"
}
```

### Share File
```http
POST /api/v2/integrations/sharepoint/share
Content-Type: application/json

{
  "file_id": "file_001",
  "emails": ["user1@army.mil", "user2@army.mil"]
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "File shared with 2 user(s)",
  "file_id": "file_001",
  "shared_with": ["user1@army.mil", "user2@army.mil"],
  "timestamp": "2024-11-19T13:50:12Z"
}
```

### Delete File
```http
DELETE /api/v2/integrations/sharepoint/delete/{file_id}
```

**Response:**
```json
{
  "status": "ok",
  "message": "File deleted successfully from SharePoint",
  "file_id": "file_001",
  "timestamp": "2024-11-19T13:50:12Z"
}
```

### Create Folder
```http
POST /api/v2/integrations/sharepoint/create-folder
Content-Type: application/json

{
  "folder_name": "New Folder",
  "path": "/parent/folder"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Folder created successfully",
  "folder_name": "New Folder",
  "path": "/parent/folder/New Folder",
  "timestamp": "2024-11-19T13:50:12Z"
}
```

## Component Architecture

### Frontend Component
**Location**: `/taaip-dashboard/src/components/SharePointIntegration.tsx`

**Key Features:**
- React functional component with TypeScript
- State management for files, folders, selections, and modals
- Lucide icons for visual elements
- Integrated search and filtering
- Responsive design with Army Vantage theme

### Backend Router
**Location**: `/backend/routers/integrations.py`

**Endpoints:**
- Browse files/folders
- Download files
- Upload files
- Share files
- Delete files
- Create folders

### SharePoint Connector
**Location**: `/backend/integrations/sharepoint.py`

**Key Methods:**
- `test_connection()`: Verify SharePoint connectivity
- `get_g2_reports()`: Retrieve G2 reports by category
- `get_report_content()`: Fetch specific report content
- `get_latest_sitrep()`: Get latest SITREP reports

## Configuration

### SharePoint System Configuration
**Location**: `/backend/integrations/config.py`

```python
'sharepoint': {
    'enabled': True,
    'base_url': 'https://army.sharepoint-mil.us/teams/TR-USREC-G2-ReportZone',
    'cert_required': True,
    'description': 'G2 Report Zone SharePoint'
}
```

### Authentication
SharePoint integration requires CAC (Common Access Card) authentication for Army network access. Set the certificate path:

```bash
export CAC_CERT_PATH=/path/to/your/cac/certificate.p12
```

## Current Implementation Status

### ✅ Completed Features
- Full UI component with file browsing
- Search and filter functionality
- Multi-select with bulk operations
- Upload modal with file selection
- Share modal with email input
- Download functionality
- API endpoints for all operations
- Integration with main navigation
- Mock data for demonstration

### 🔄 Ready for Real Data Integration
The current implementation uses mock data for demonstration. To connect to the real Army SharePoint:

1. **Configure CAC Certificate**:
   ```bash
   export CAC_CERT_PATH=/path/to/cert.p12
   ```

2. **Update SharePoint Connector**:
   - Replace mock responses in `/backend/integrations/sharepoint.py`
   - Implement Microsoft Graph API calls
   - Add OAuth2 authentication flow

3. **Test Connection**:
   ```bash
   curl http://localhost:8000/api/v2/integrations/test/sharepoint
   ```

## Usage Examples

### Browsing Files
1. Navigate to **SharePoint Files** from the main menu
2. Click on folders to navigate deeper
3. Use breadcrumb navigation to go back
4. Click refresh button to reload current directory

### Uploading Files
1. Click the **Upload** button in the toolbar
2. Select one or more files from your computer
3. Files will be uploaded to the current directory
4. Success notification will appear

### Downloading Files
1. Check the checkbox next to file(s) you want to download
2. Click the **Download** button in the toolbar
3. Or click the download icon next to individual files
4. Files will download to your default download location

### Sharing Files
1. Click the share icon next to the file you want to share
2. Enter email addresses (comma-separated) in the modal
3. Press Enter or click **Share File** button
4. Recipients will receive SharePoint access notification

### Searching Files
1. Use the search box in the toolbar
2. Type any part of the filename
3. Results filter in real-time
4. Search works across all files in current directory

## Security Considerations

- **CAC Authentication**: All SharePoint requests require valid CAC certificate
- **Access Control**: Integrated with TAAIP's 4-tier access system
- **Audit Logging**: All file operations are logged for security audit
- **Encryption**: All data transfer uses TLS 1.2+
- **Session Management**: Tokens expire after inactivity period

## Troubleshooting

### "SharePoint integration not available"
**Cause**: SharePoint connector not initialized
**Solution**: 
1. Check `SYSTEMS['sharepoint']['enabled']` in config.py
2. Verify CAC certificate path is set
3. Restart backend service

### "503: SharePoint unavailable"
**Cause**: Cannot connect to SharePoint
**Solution**:
1. Test connectivity: `curl https://army.sharepoint-mil.us`
2. Verify VPN connection to Army network
3. Check CAC certificate is valid and not expired

### "File upload failed"
**Cause**: Permission or network issue
**Solution**:
1. Verify you have write permissions to target folder
2. Check file size limits (default: 100MB per file)
3. Ensure stable network connection

## Integration with Other TAAIP Features

### 1. **G2 Zone Performance Dashboard**
- Links to related SharePoint reports
- Displays latest G2 intelligence documents
- One-click access to detailed reports

### 2. **Mission Analysis (M-IPOE)**
- Access to mission planning documents from SharePoint
- Upload After-Action Reports (AAR)
- Share SITREP documents with team

### 3. **Project Management**
- Attach SharePoint documents to projects
- Track document versions
- Collaborate on deliverables

### 4. **Resource Management**
- Centralized document repository
- Training materials and SOPs
- Forms and templates library

## Future Enhancements

### Planned Features
- [ ] Document preview in-app (PDF, Office docs)
- [ ] Version history tracking
- [ ] Advanced search with filters (date, size, type)
- [ ] Document check-in/check-out
- [ ] Folder permissions management
- [ ] Batch operations (move, copy)
- [ ] Document tagging and metadata
- [ ] Integration with MS Teams
- [ ] Offline sync capability
- [ ] Document workflows and approvals

### Under Consideration
- [ ] Document commenting and annotations
- [ ] Real-time collaborative editing
- [ ] Document templates library
- [ ] Automated report generation
- [ ] Document expiration and retention policies
- [ ] Integration with iKrome and Vantage
- [ ] Mobile app support
- [ ] Document watermarking

## Technical Details

### Frontend Dependencies
- React 18
- TypeScript 4.9+
- Lucide React (icons)
- Tailwind CSS (styling)

### Backend Dependencies
- FastAPI
- Python 3.9+
- requests (HTTP client)
- Office365-REST-Python-Client (SharePoint API)

### Browser Compatibility
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Support

For technical issues or feature requests related to SharePoint Integration:

1. Check this documentation
2. Review integration logs: `/backend/logs/integrations.log`
3. Test API endpoints using curl or Postman
4. Contact TAAIP support team

## Changelog

### Version 2.0 (November 19, 2024)
- ✅ Initial SharePoint Integration release
- ✅ Full UI component with file browser
- ✅ All CRUD operations (Create, Read, Update, Delete)
- ✅ Mock data implementation for demonstration
- ✅ Integration with main TAAIP navigation
- ✅ Army Vantage themed interface
- ✅ Comprehensive API documentation

---

**Document Version**: 1.0  
**Last Updated**: November 19, 2024  
**Author**: TAAIP Development Team  
**Classification**: UNCLASSIFIED
