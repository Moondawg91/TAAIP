"""
AI Predictive Pipeline for TAAIP
- Model training on historical lead/conversion data
- Batch prediction on new leads
- Scheduled retraining
- Lead propensity scoring
"""

import pickle
import json
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import logging
from typing import Dict, List, Tuple, Any

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "lead_propensity_model.pkl"
SCALER_PATH = MODEL_DIR / "feature_scaler.pkl"


class LeadPropensityModel:
    """Random Forest model for predicting lead conversion propensity."""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = ['age', 'propensity_score', 'web_activity', 'engagement_count', 'education_level_encoded']
        self.label_encoders = {}
        self.accuracy = 0.0
        self.training_samples = 0
        
    def train(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train model on historical lead data."""
        if not HAS_SKLEARN:
            logger.warning("scikit-learn not installed; using mock model")
            self.accuracy = 0.87
            self.training_samples = len(data)
            return {
                "status": "trained (mock)",
                "accuracy": self.accuracy,
                "samples": self.training_samples,
                "note": "Install scikit-learn for real model: pip install scikit-learn"
            }
        
        try:
            X = []
            y = []
            
            for lead in data:
                features = [
                    lead.get('age', 20),
                    lead.get('propensity_score', 5),
                    lead.get('web_activity', 3),
                    lead.get('engagement_count', 1),
                    1 if lead.get('education_level') == 'Degree' else 0,
                ]
                X.append(features)
                y.append(lead.get('converted', 0))
            
            if len(X) < 10:
                logger.warning("Insufficient training data")
                return {"status": "error", "message": "Need at least 10 samples"}
            
            X = np.array(X)
            y = np.array(y)
            
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            self.model.fit(X_scaled, y)
            
            # Calculate accuracy
            self.accuracy = self.model.score(X_scaled, y)
            self.training_samples = len(data)
            
            # Save model
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(self.model, f)
            with open(SCALER_PATH, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            logger.info(f"Model trained with accuracy {self.accuracy:.2%}")
            return {
                "status": "trained",
                "accuracy": round(self.accuracy, 4),
                "samples": self.training_samples,
            }
        except Exception as e:
            logger.error(f"Training error: {e}")
            return {"status": "error", "message": str(e)}
    
    def predict(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict propensity for new leads."""
        if not HAS_SKLEARN:
            # Mock prediction
            import random
            predictions = []
            for lead in leads:
                propensity = round(lead.get('propensity_score', 5) * 15 + random.randint(-10, 10), 1)
                tier = "Tier 1" if propensity >= 70 else "Tier 2" if propensity >= 50 else "Tier 3"
                predictions.append({
                    "lead_id": lead.get("lead_id"),
                    "propensity_score": max(0, min(100, propensity)),
                    "tier": tier,
                    "recommendation": f"{tier} lead"
                })
            return predictions
        
        try:
            if self.model is None or self.scaler is None:
                return [{"error": "Model not trained"}]
            
            predictions = []
            for lead in leads:
                features = np.array([[
                    lead.get('age', 20),
                    lead.get('propensity_score', 5),
                    lead.get('web_activity', 3),
                    lead.get('engagement_count', 1),
                    1 if lead.get('education_level') == 'Degree' else 0,
                ]])
                
                X_scaled = self.scaler.transform(features)
                propensity = self.model.predict_proba(X_scaled)[0][1] * 100
                
                tier = "Tier 1" if propensity >= 70 else "Tier 2" if propensity >= 50 else "Tier 3"
                predictions.append({
                    "lead_id": lead.get("lead_id"),
                    "propensity_score": round(propensity, 1),
                    "tier": tier,
                    "recommendation": f"{tier} lead - {['Nurture', 'Engage', 'Prioritize'][['Tier 3', 'Tier 2', 'Tier 1'].index(tier)]}"
                })
            
            return predictions
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return [{"error": str(e)}]


# Global model instance
lead_propensity_model = LeadPropensityModel()


def train_lead_propensity_model(db_path: str) -> Dict[str, Any]:
    """Train model on historical data from SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Fetch historical leads with outcomes
        cur.execute("""
            SELECT lead_id, age, education_level, campaign_source, 
                   predicted_probability, score, converted, received_at
            FROM leads
            ORDER BY received_at DESC
            LIMIT 1000
        """)
        
        rows = cur.fetchall()
        conn.close()
        
        data = [dict(row) for row in rows]
        
        if not data:
            return {"status": "warning", "message": "No training data available"}
        
        result = lead_propensity_model.train(data)
        logger.info(f"Trained model on {len(data)} leads")
        return result
    except Exception as e:
        logger.error(f"Model training error: {e}")
        return {"status": "error", "message": str(e)}


def predict_lead_propensity(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get propensity predictions for new leads."""
    return lead_propensity_model.predict(leads)


def get_model_status() -> Dict[str, Any]:
    """Return current model status."""
    return {
        "status": "ready" if lead_propensity_model.model is not None else "untrained",
        "accuracy": lead_propensity_model.accuracy,
        "training_samples": lead_propensity_model.training_samples,
        "model_path": str(MODEL_PATH),
        "last_updated": MODEL_PATH.stat().st_mtime if MODEL_PATH.exists() else None,
    }
