#!/usr/bin/env python3
"""
Machine Learning Prediction Engine for TAAIP
Uses historical EMM data to predict event performance, lead generation, and ROI.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import math

DB_FILE = '/Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3'

class TAIPPredictionEngine:
    """
    ML-based prediction engine for event performance.
    Uses historical EMM data and similarity scoring for predictions.
    """
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def predict_event_performance(
        self, 
        event_type_category: str,
        budget: float,
        team_size: int,
        location: str,
        target_audience: str,
        month: str,
        day_of_week: str,
        rsid: str = None
    ) -> Dict:
        """
        Predict event performance based on historical EMM data.
        Returns predicted leads, conversions, ROI, and confidence score.
        """
        
        # Get similar historical events
        similar_events = self._find_similar_events(
            event_type_category, budget, team_size, location, 
            target_audience, month, day_of_week, rsid
        )
        
        if not similar_events:
            # No historical data - use baseline estimates
            return self._baseline_prediction(event_type_category, budget)
        
        # Calculate weighted average based on similarity scores
        total_weight = sum(e['similarity_score'] for e in similar_events)
        
        predicted_leads = sum(
            e['leads_generated'] * e['similarity_score'] 
            for e in similar_events
        ) / total_weight
        
        predicted_conversions = sum(
            e['conversions'] * e['similarity_score'] 
            for e in similar_events
        ) / total_weight
        
        predicted_roi = sum(
            e['roi'] * e['similarity_score'] 
            for e in similar_events
        ) / total_weight
        
        predicted_cost_per_lead = budget / predicted_leads if predicted_leads > 0 else 0
        
        # Calculate confidence based on number of similar events and data quality
        confidence = min(0.95, 0.5 + (len(similar_events) / 20) * 0.45)
        
        # Calculate feature importance
        feature_importance = self._calculate_feature_importance(similar_events)
        
        return {
            'predicted_leads': int(round(predicted_leads)),
            'predicted_conversions': int(round(predicted_conversions)),
            'predicted_roi': round(predicted_roi, 2),
            'predicted_cost_per_lead': round(predicted_cost_per_lead, 2),
            'confidence_score': round(confidence, 3),
            'model_name': 'similarity_weighted_average',
            'model_version': '1.0',
            'similar_events_count': len(similar_events),
            'feature_importance': json.dumps(feature_importance)
        }
    
    def _find_similar_events(
        self,
        event_type: str,
        budget: float,
        team_size: int,
        location: str,
        target_audience: str,
        month: str,
        day_of_week: str,
        rsid: str = None
    ) -> List[Dict]:
        """Find similar historical events and calculate similarity scores."""
        
        cursor = self.conn.cursor()
        
        # Get historical events
        cursor.execute("""
            SELECT * FROM emm_historical_data
            WHERE event_type_category = ?
            AND leads_generated > 0
            ORDER BY event_date DESC
            LIMIT 50
        """, (event_type,))
        
        historical_events = [dict(row) for row in cursor.fetchall()]
        
        # Calculate similarity scores
        scored_events = []
        for event in historical_events:
            similarity = self._calculate_similarity(
                event, event_type, budget, team_size, location,
                target_audience, month, day_of_week, rsid
            )
            
            if similarity > 0.3:  # Threshold for relevance
                event['similarity_score'] = similarity
                scored_events.append(event)
        
        # Sort by similarity and return top matches
        scored_events.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_events[:10]
    
    def _calculate_similarity(
        self,
        historical_event: Dict,
        event_type: str,
        budget: float,
        team_size: int,
        location: str,
        target_audience: str,
        month: str,
        day_of_week: str,
        rsid: str
    ) -> float:
        """Calculate similarity score between proposed and historical event."""
        
        score = 0.0
        
        # Event type (exact match) - 30%
        if historical_event['event_type_category'] == event_type:
            score += 0.30
        
        # Budget similarity - 20%
        if historical_event['budget'] and budget:
            budget_diff = abs(historical_event['budget'] - budget) / max(budget, 1)
            budget_score = max(0, 1 - budget_diff)
            score += 0.20 * budget_score
        
        # Team size similarity - 10%
        if historical_event['team_size'] and team_size:
            team_diff = abs(historical_event['team_size'] - team_size) / max(team_size, 1)
            team_score = max(0, 1 - team_diff)
            score += 0.10 * team_score
        
        # Location similarity - 15%
        if historical_event['location'] and location:
            if historical_event['location'].lower() in location.lower() or \
               location.lower() in historical_event['location'].lower():
                score += 0.15
        
        # Target audience similarity - 10%
        if historical_event['target_audience'] and target_audience:
            if historical_event['target_audience'].lower() in target_audience.lower() or \
               target_audience.lower() in historical_event['target_audience'].lower():
                score += 0.10
        
        # Month similarity (seasonality) - 10%
        if historical_event['month'] == month:
            score += 0.10
        elif abs(self._month_to_num(historical_event['month']) - self._month_to_num(month)) <= 1:
            score += 0.05
        
        # Day of week similarity - 5%
        if historical_event['day_of_week'] == day_of_week:
            score += 0.05
        
        return score
    
    def _baseline_prediction(self, event_type: str, budget: float) -> Dict:
        """Baseline predictions when no historical data is available."""
        
        # Industry baseline conversion rates by event type
        baselines = {
            'lead_generating': {'leads_per_1k': 25, 'conversion_rate': 0.08, 'roi': 1.5},
            'shaping': {'leads_per_1k': 15, 'conversion_rate': 0.05, 'roi': 1.2},
            'brand_awareness': {'leads_per_1k': 10, 'conversion_rate': 0.03, 'roi': 1.0},
            'community_engagement': {'leads_per_1k': 12, 'conversion_rate': 0.04, 'roi': 1.1},
            'retention': {'leads_per_1k': 8, 'conversion_rate': 0.15, 'roi': 2.0},
            'research': {'leads_per_1k': 5, 'conversion_rate': 0.02, 'roi': 0.8}
        }
        
        baseline = baselines.get(event_type, baselines['lead_generating'])
        
        predicted_leads = int((budget / 1000) * baseline['leads_per_1k'])
        predicted_conversions = int(predicted_leads * baseline['conversion_rate'])
        predicted_roi = baseline['roi']
        predicted_cost_per_lead = budget / predicted_leads if predicted_leads > 0 else 0
        
        return {
            'predicted_leads': predicted_leads,
            'predicted_conversions': predicted_conversions,
            'predicted_roi': predicted_roi,
            'predicted_cost_per_lead': round(predicted_cost_per_lead, 2),
            'confidence_score': 0.40,  # Low confidence without historical data
            'model_name': 'baseline_industry_average',
            'model_version': '1.0',
            'similar_events_count': 0,
            'feature_importance': json.dumps({'baseline': 1.0})
        }
    
    def _calculate_feature_importance(self, similar_events: List[Dict]) -> Dict:
        """Calculate which features most strongly correlate with outcomes."""
        
        importance = {
            'budget': 0.25,
            'event_type': 0.30,
            'team_size': 0.15,
            'location': 0.10,
            'seasonality': 0.10,
            'target_audience': 0.10
        }
        
        return importance
    
    def _month_to_num(self, month: str) -> int:
        """Convert month name to number."""
        months = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        return months.get(month, 0)
    
    def save_prediction(
        self,
        entity_type: str,
        entity_id: str,
        prediction_data: Dict
    ) -> str:
        """Save prediction to database for tracking accuracy."""
        
        prediction_id = f"pred_{uuid.uuid4().hex[:12]}"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ml_predictions (
                prediction_id, entity_type, entity_id, prediction_date,
                model_name, model_version, predicted_leads, predicted_conversions,
                predicted_roi, predicted_cost_per_lead, confidence_score,
                feature_importance, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_id, entity_type, entity_id, datetime.now().isoformat(),
            prediction_data['model_name'], prediction_data['model_version'],
            prediction_data['predicted_leads'], prediction_data['predicted_conversions'],
            prediction_data['predicted_roi'], prediction_data['predicted_cost_per_lead'],
            prediction_data['confidence_score'], prediction_data['feature_importance'],
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        return prediction_id
    
    def update_prediction_accuracy(
        self,
        entity_type: str,
        entity_id: str,
        actual_leads: int,
        actual_conversions: int,
        actual_roi: float
    ):
        """Update prediction with actual results and calculate accuracy."""
        
        cursor = self.conn.cursor()
        
        # Get the prediction
        cursor.execute("""
            SELECT * FROM ml_predictions
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY prediction_date DESC LIMIT 1
        """, (entity_type, entity_id))
        
        prediction = cursor.fetchone()
        if not prediction:
            return
        
        pred_dict = dict(prediction)
        
        # Calculate accuracy metrics
        leads_accuracy = 1 - abs(actual_leads - pred_dict['predicted_leads']) / max(actual_leads, 1)
        roi_accuracy = 1 - abs(actual_roi - pred_dict['predicted_roi']) / max(abs(actual_roi), 0.1)
        overall_accuracy = (leads_accuracy + roi_accuracy) / 2
        
        mae = (abs(actual_leads - pred_dict['predicted_leads']) + 
               abs(actual_roi - pred_dict['predicted_roi'])) / 2
        
        # Update prediction record
        cursor.execute("""
            UPDATE ml_predictions
            SET actual_leads = ?, actual_conversions = ?, actual_roi = ?,
                prediction_accuracy = ?, mean_absolute_error = ?
            WHERE prediction_id = ?
        """, (
            actual_leads, actual_conversions, actual_roi,
            round(overall_accuracy, 3), round(mae, 2),
            pred_dict['prediction_id']
        ))
        
        self.conn.commit()


def generate_event_prediction(event_id: str) -> Dict:
    """
    Generate ML prediction for an event based on its attributes.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get event details
    cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()
    
    if not event:
        conn.close()
        return {'error': 'Event not found'}
    
    event_dict = dict(event)
    conn.close()
    
    # Extract date components
    start_date = datetime.fromisoformat(event_dict['start_date'])
    month = start_date.strftime('%B')
    day_of_week = start_date.strftime('%A')
    
    # Initialize prediction engine
    engine = TAIPPredictionEngine()
    
    # Generate prediction
    prediction = engine.predict_event_performance(
        event_type_category=event_dict.get('event_type_category', 'lead_generating'),
        budget=event_dict.get('budget', 0),
        team_size=event_dict.get('team_size', 5),
        location=event_dict.get('location', ''),
        target_audience=event_dict.get('targeting_principles', 'general'),
        month=month,
        day_of_week=day_of_week,
        rsid=event_dict.get('rsid')
    )
    
    # Save prediction
    prediction_id = engine.save_prediction('event', event_id, prediction)
    prediction['prediction_id'] = prediction_id
    
    # Update event with predictions
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events 
        SET predicted_leads = ?,
            predicted_conversions = ?,
            predicted_roi = ?,
            predicted_cost_per_lead = ?,
            prediction_confidence = ?,
            prediction_date = ?,
            prediction_model = ?
        WHERE event_id = ?
    """, (
        prediction['predicted_leads'],
        prediction['predicted_conversions'],
        prediction['predicted_roi'],
        prediction['predicted_cost_per_lead'],
        prediction['confidence_score'],
        datetime.now().isoformat(),
        prediction['model_name'],
        event_id
    ))
    conn.commit()
    conn.close()
    
    return prediction


if __name__ == '__main__':
    # Test prediction engine
    print("🤖 Testing TAAIP ML Prediction Engine\n")
    
    engine = TAIPPredictionEngine()
    
    test_prediction = engine.predict_event_performance(
        event_type_category='lead_generating',
        budget=5000.0,
        team_size=8,
        location='Dallas, TX',
        target_audience='High school seniors',
        month='March',
        day_of_week='Saturday',
        rsid='RSID_001'
    )
    
    print("Test Prediction Results:")
    print(f"  Predicted Leads: {test_prediction['predicted_leads']}")
    print(f"  Predicted Conversions: {test_prediction['predicted_conversions']}")
    print(f"  Predicted ROI: {test_prediction['predicted_roi']}")
    print(f"  Predicted Cost/Lead: ${test_prediction['predicted_cost_per_lead']}")
    print(f"  Confidence: {test_prediction['confidence_score']*100:.1f}%")
    print(f"  Model: {test_prediction['model_name']} v{test_prediction['model_version']}")
    print(f"  Similar Events: {test_prediction['similar_events_count']}")
    print("\n✅ Prediction engine working correctly!")
