"""
Data Export Utility - Export dashboard data to CSV/Excel/JSON
Enables verification and external analysis of TAAIP data
"""
import json
import csv
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import io


class DataExporter:
    """Export TAAIP data in various formats"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dicts"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to CSV format"""
        if not data:
            return "No data to export"
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        if filename:
            with open(filename, 'w', newline='') as f:
                f.write(csv_content)
            return f"Exported to {filename}"
        
        return csv_content
    
    def export_to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to JSON format"""
        json_content = json.dumps(data, indent=2, default=str)
        
        if filename:
            with open(filename, 'w') as f:
                f.write(json_content)
            return f"Exported to {filename}"
        
        return json_content
    
    def export_projects(self, rsid: Optional[str] = None, status: Optional[str] = None, 
                       format: str = 'csv', filename: str = None) -> str:
        """
        Export projects data with optional filtering
        
        Args:
            rsid: Filter by RSID (e.g., "1BDE", "1BDE-1BN", "1BDE-1BN-1-1")
            status: Filter by status (planning, in_progress, etc.)
            format: 'csv' or 'json'
            filename: Optional output filename
        """
        query = """
            SELECT 
                project_id, name, status, owner_id, rsid, brigade, battalion, station,
                start_date, target_date, percent_complete,
                funding_amount, spent_amount, 
                (funding_amount - spent_amount) as remaining_budget,
                CASE 
                    WHEN funding_amount > 0 THEN 
                        ROUND((spent_amount / funding_amount) * 100, 2)
                    ELSE 0 
                END as budget_utilization_percent,
                risk_level, objectives, blockers,
                created_at, updated_at
            FROM projects
            WHERE is_archived = 0
        """
        
        params = []
        if rsid:
            query += " AND (rsid LIKE ? OR brigade = ? OR battalion = ?)"
            params.extend([f"{rsid}%", rsid, rsid])
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        data = self._execute_query(query, tuple(params))
        
        if format == 'json':
            return self.export_to_json(data, filename)
        else:
            return self.export_to_csv(data, filename)
    
    def export_tasks(self, project_id: Optional[str] = None, status: Optional[str] = None,
                    assigned_to: Optional[str] = None, format: str = 'csv', 
                    filename: str = None) -> str:
        """Export tasks data with filtering"""
        query = """
            SELECT 
                t.task_id, t.project_id, p.name as project_name, p.rsid,
                t.title, t.description, t.assigned_to, t.status, t.priority,
                t.due_date, 
                CASE 
                    WHEN t.due_date < date('now') AND t.status != 'completed' 
                    THEN 'overdue'
                    ELSE 'on_track'
                END as timeline_status,
                t.created_at, t.updated_at
            FROM tasks t
            JOIN projects p ON t.project_id = p.project_id
            WHERE 1=1
        """
        
        params = []
        if project_id:
            query += " AND t.project_id = ?"
            params.append(project_id)
        if status:
            query += " AND t.status = ?"
            params.append(status)
        if assigned_to:
            query += " AND t.assigned_to = ?"
            params.append(assigned_to)
        
        query += " ORDER BY t.due_date ASC"
        
        data = self._execute_query(query, tuple(params))
        
        if format == 'json':
            return self.export_to_json(data, filename)
        else:
            return self.export_to_csv(data, filename)
    
    def export_events(self, rsid: Optional[str] = None, format: str = 'csv', 
                     filename: str = None) -> str:
        """Export events data"""
        query = """
            SELECT 
                event_id, name, type, location, rsid, brigade, battalion, station,
                start_date, end_date, budget, team_size, status,
                targeting_principles, created_at
            FROM events
            WHERE is_archived = 0
        """
        
        params = []
        if rsid:
            query += " AND (rsid LIKE ? OR brigade = ?)"
            params.extend([f"{rsid}%", rsid])
        
        query += " ORDER BY start_date DESC"
        
        data = self._execute_query(query, tuple(params))
        
        if format == 'json':
            return self.export_to_json(data, filename)
        else:
            return self.export_to_csv(data, filename)
    
    def export_leads(self, cbsa_code: Optional[str] = None, format: str = 'csv',
                    filename: str = None) -> str:
        """Export leads data"""
        query = """
            SELECT 
                lead_id, age, education_level, cbsa_code, campaign_source,
                predicted_probability, score, recommendation, converted,
                received_at, created_at
            FROM leads
            WHERE is_archived = 0
        """
        
        params = []
        if cbsa_code:
            query += " AND cbsa_code = ?"
            params.append(cbsa_code)
        
        query += " ORDER BY received_at DESC LIMIT 10000"
        
        data = self._execute_query(query, tuple(params))
        
        if format == 'json':
            return self.export_to_json(data, filename)
        else:
            return self.export_to_csv(data, filename)
    
    def export_dashboard_summary(self, rsid: Optional[str] = None, format: str = 'csv',
                                filename: str = None) -> str:
        """Export comprehensive dashboard summary"""
        # Projects summary
        projects_query = """
            SELECT 
                'Projects' as category,
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN status = 'at_risk' THEN 1 ELSE 0 END) as at_risk_count,
                SUM(funding_amount) as total_budget,
                SUM(spent_amount) as total_spent,
                AVG(percent_complete) as avg_completion
            FROM projects
            WHERE is_archived = 0
        """
        
        params = []
        if rsid:
            projects_query += " AND (rsid LIKE ? OR brigade = ?)"
            params.extend([f"{rsid}%", rsid])
        
        data = self._execute_query(projects_query, tuple(params))
        
        # Tasks summary
        tasks_query = """
            SELECT 
                'Tasks' as category,
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
                SUM(CASE WHEN due_date < date('now') AND status != 'completed' THEN 1 ELSE 0 END) as overdue_count
            FROM tasks t
            JOIN projects p ON t.project_id = p.project_id
            WHERE 1=1
        """
        
        if rsid:
            tasks_query += " AND (p.rsid LIKE ? OR p.brigade = ?)"
        
        tasks_data = self._execute_query(tasks_query, tuple(params))
        data.extend(tasks_data)
        
        if format == 'json':
            return self.export_to_json(data, filename)
        else:
            return self.export_to_csv(data, filename)
    
    def export_budget_analysis(self, rsid: Optional[str] = None, format: str = 'csv',
                              filename: str = None) -> str:
        """Export detailed budget analysis"""
        query = """
            SELECT 
                project_id, name, rsid, brigade, battalion,
                funding_amount, spent_amount,
                (funding_amount - spent_amount) as remaining,
                CASE 
                    WHEN funding_amount > 0 THEN 
                        ROUND((spent_amount / funding_amount) * 100, 2)
                    ELSE 0 
                END as utilization_percent,
                CASE
                    WHEN spent_amount > funding_amount THEN 'over_budget'
                    WHEN spent_amount >= funding_amount * 0.9 THEN 'at_risk'
                    WHEN spent_amount >= funding_amount * 0.75 THEN 'on_track'
                    ELSE 'under_budget'
                END as budget_status,
                status, percent_complete,
                start_date, target_date
            FROM projects
            WHERE is_archived = 0 AND funding_amount > 0
        """
        
        params = []
        if rsid:
            query += " AND (rsid LIKE ? OR brigade = ?)"
            params.extend([f"{rsid}%", rsid])
        
        query += " ORDER BY utilization_percent DESC"
        
        data = self._execute_query(query, tuple(params))
        
        if format == 'json':
            return self.export_to_json(data, filename)
        else:
            return self.export_to_csv(data, filename)


# Convenience functions for API endpoints
def export_projects_csv(db_path: str, rsid: str = None, status: str = None) -> str:
    """Quick export projects to CSV"""
    exporter = DataExporter(db_path)
    return exporter.export_projects(rsid=rsid, status=status, format='csv')

def export_tasks_csv(db_path: str, project_id: str = None, status: str = None) -> str:
    """Quick export tasks to CSV"""
    exporter = DataExporter(db_path)
    return exporter.export_tasks(project_id=project_id, status=status, format='csv')

def export_budget_analysis_csv(db_path: str, rsid: str = None) -> str:
    """Quick export budget analysis to CSV"""
    exporter = DataExporter(db_path)
    return exporter.export_budget_analysis(rsid=rsid, format='csv')
