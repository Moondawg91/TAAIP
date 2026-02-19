"""
Budget Tracking API Router
Endpoints for fiscal year budget allocation, tracking, and reporting
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import sqlite3

router = APIRouter()

# Database connection
def get_db():
    conn = sqlite3.connect('/Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class BudgetAllocation(BaseModel):
    unit_id: str
    unit_name: str
    unit_type: str  # 'battalion' or 'brigade'
    fiscal_year: int
    total_budget: float
    allocated: float
    spent: float
    remaining: float
    utilization_rate: float
    categories: Dict[str, float]


class BudgetTransaction(BaseModel):
    id: str
    date: str
    type: str  # 'event', 'project', 'operation', 'other'
    description: str
    amount: float
    unit: str
    status: str  # 'approved', 'pending', 'completed'


@router.get("/budget/allocations")
async def get_budget_allocations(
    fiscal_year: int = 2025,
    unit_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get budget allocations for all units or specific unit"""
    
    # Mock data - replace with actual database queries
    budgets = [
        {
            "unit_id": "brigade_1",
            "unit_name": "1st Brigade",
            "unit_type": "brigade",
            "fiscal_year": fiscal_year,
            "total_budget": 2500000,
            "allocated": 2100000,
            "spent": 1850000,
            "remaining": 650000,
            "utilization_rate": 74.0,
            "categories": {
                "events": 650000,
                "projects": 850000,
                "operations": 250000,
                "other": 100000
            },
            "transactions": [
                {
                    "id": "txn_001",
                    "date": "2024-11-15",
                    "type": "event",
                    "description": "College Football Game Event",
                    "amount": 15000,
                    "unit": "1st Brigade",
                    "status": "completed"
                },
                {
                    "id": "txn_002",
                    "date": "2024-11-10",
                    "type": "project",
                    "description": "Social Media Campaign Q4",
                    "amount": 25000,
                    "unit": "1st Brigade",
                    "status": "completed"
                },
                {
                    "id": "txn_003",
                    "date": "2024-11-08",
                    "type": "operation",
                    "description": "Recruiter Training Workshop",
                    "amount": 8000,
                    "unit": "1st Brigade",
                    "status": "completed"
                }
            ]
        },
        {
            "unit_id": "brigade_2",
            "unit_name": "2nd Brigade",
            "unit_type": "brigade",
            "fiscal_year": fiscal_year,
            "total_budget": 2300000,
            "allocated": 1950000,
            "spent": 1650000,
            "remaining": 650000,
            "utilization_rate": 71.7,
            "categories": {
                "events": 580000,
                "projects": 750000,
                "operations": 220000,
                "other": 100000
            },
            "transactions": [
                {
                    "id": "txn_004",
                    "date": "2024-11-12",
                    "type": "event",
                    "description": "Career Fair - State University",
                    "amount": 12000,
                    "unit": "2nd Brigade",
                    "status": "completed"
                }
            ]
        },
        {
            "unit_id": "battalion_101",
            "unit_name": "1-101 Battalion",
            "unit_type": "battalion",
            "fiscal_year": fiscal_year,
            "total_budget": 850000,
            "allocated": 720000,
            "spent": 620000,
            "remaining": 230000,
            "utilization_rate": 72.9,
            "categories": {
                "events": 220000,
                "projects": 280000,
                "operations": 85000,
                "other": 35000
            },
            "transactions": [
                {
                    "id": "txn_005",
                    "date": "2024-11-14",
                    "type": "event",
                    "description": "High School Visit - Lincoln HS",
                    "amount": 3500,
                    "unit": "1-101 Battalion",
                    "status": "completed"
                },
                {
                    "id": "txn_006",
                    "date": "2024-11-09",
                    "type": "project",
                    "description": "Local Marketing Materials",
                    "amount": 8500,
                    "unit": "1-101 Battalion",
                    "status": "completed"
                }
            ]
        },
        {
            "unit_id": "battalion_102",
            "unit_name": "1-102 Battalion",
            "unit_type": "battalion",
            "fiscal_year": fiscal_year,
            "total_budget": 800000,
            "allocated": 680000,
            "spent": 720000,
            "remaining": 80000,
            "utilization_rate": 90.0,
            "categories": {
                "events": 250000,
                "projects": 320000,
                "operations": 100000,
                "other": 50000
            },
            "transactions": [
                {
                    "id": "txn_007",
                    "date": "2024-11-11",
                    "type": "event",
                    "description": "Community Outreach Program",
                    "amount": 6000,
                    "unit": "1-102 Battalion",
                    "status": "completed"
                }
            ]
        },
        {
            "unit_id": "brigade_3",
            "unit_name": "3rd Brigade",
            "unit_type": "brigade",
            "fiscal_year": fiscal_year,
            "total_budget": 2200000,
            "allocated": 1850000,
            "spent": 1350000,
            "remaining": 850000,
            "utilization_rate": 61.4,
            "categories": {
                "events": 450000,
                "projects": 650000,
                "operations": 180000,
                "other": 70000
            },
            "transactions": [
                {
                    "id": "txn_008",
                    "date": "2024-11-13",
                    "type": "project",
                    "description": "Digital Advertising Campaign",
                    "amount": 35000,
                    "unit": "3rd Brigade",
                    "status": "approved"
                }
            ]
        },
        {
            "unit_id": "battalion_201",
            "unit_name": "2-201 Battalion",
            "unit_type": "battalion",
            "fiscal_year": fiscal_year,
            "total_budget": 780000,
            "allocated": 650000,
            "spent": 580000,
            "remaining": 200000,
            "utilization_rate": 74.4,
            "categories": {
                "events": 200000,
                "projects": 250000,
                "operations": 90000,
                "other": 40000
            },
            "transactions": []
        }
    ]
    
    # Filter by unit if specified
    if unit_id:
        budgets = [b for b in budgets if b['unit_id'] == unit_id]
    
    # Get recent transactions across all units
    all_transactions = []
    for budget in budgets:
        all_transactions.extend(budget.get('transactions', []))
    
    # Sort by date descending
    all_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    return {
        'status': 'ok',
        'fiscal_year': fiscal_year,
        'budgets': budgets,
        'recent_transactions': all_transactions[:20],
        'summary': {
            'total_budget': sum(b['total_budget'] for b in budgets),
            'total_spent': sum(b['spent'] for b in budgets),
            'total_remaining': sum(b['remaining'] for b in budgets),
            'overall_utilization': (sum(b['spent'] for b in budgets) / sum(b['total_budget'] for b in budgets) * 100) if sum(b['total_budget'] for b in budgets) > 0 else 0
        },
        'timestamp': datetime.now().isoformat()
    }


@router.get("/budget/transactions")
async def get_budget_transactions(
    unit_id: Optional[str] = None,
    fiscal_year: int = 2025,
    transaction_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Get budget transactions with optional filters"""
    
    # This would query the actual database
    # For now, returning mock data
    
    return {
        'status': 'ok',
        'transactions': [],
        'total': 0,
        'timestamp': datetime.now().isoformat()
    }


@router.post("/budget/transaction")
async def create_budget_transaction(
    unit_id: str,
    transaction_type: str,
    description: str,
    amount: float,
    category: str = 'other'
) -> Dict[str, Any]:
    """Create a new budget transaction"""
    
    # This would insert into the database
    # For now, returning success
    
    return {
        'status': 'ok',
        'message': 'Budget transaction created successfully',
        'transaction_id': f'txn_{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'timestamp': datetime.now().isoformat()
    }


@router.get("/budget/summary")
async def get_budget_summary(fiscal_year: int = 2025) -> Dict[str, Any]:
    """Get overall budget summary across all units"""
    
    allocations_response = await get_budget_allocations(fiscal_year=fiscal_year)
    
    return {
        'status': 'ok',
        'fiscal_year': fiscal_year,
        'summary': allocations_response.get('summary', {}),
        'by_unit_type': {
            'brigades': {
                'count': len([b for b in allocations_response['budgets'] if b['unit_type'] == 'brigade']),
                'total_budget': sum(b['total_budget'] for b in allocations_response['budgets'] if b['unit_type'] == 'brigade'),
                'total_spent': sum(b['spent'] for b in allocations_response['budgets'] if b['unit_type'] == 'brigade'),
            },
            'battalions': {
                'count': len([b for b in allocations_response['budgets'] if b['unit_type'] == 'battalion']),
                'total_budget': sum(b['total_budget'] for b in allocations_response['budgets'] if b['unit_type'] == 'battalion'),
                'total_spent': sum(b['spent'] for b in allocations_response['budgets'] if b['unit_type'] == 'battalion'),
            }
        },
        'timestamp': datetime.now().isoformat()
    }
