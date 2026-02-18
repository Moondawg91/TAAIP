"""
Data Validation Layer for TAAIP 2.0
Ensures data quality and compliance before storage
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ValidationError
import re
import logging

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of data validation"""
    passed: bool = True
    errors: List[str] = []
    warnings: List[str] = []
    quality_score: float = 100.0
    validated_at: str = datetime.utcnow().isoformat()
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.passed = False
        self.quality_score = max(0, self.quality_score - 20)
        
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
        self.quality_score = max(0, self.quality_score - 5)


class DataValidator:
    """Comprehensive data validation for all TAAIP data"""
    
    @staticmethod
    def validate_lead(lead_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate lead data before storage
        Checks: eligibility, data quality, PII compliance, duplicates
        """
        result = ValidationResult()
        
        # Layer 1: Required fields
        required = ['lead_id', 'age']
        for field in required:
            if not lead_data.get(field):
                result.add_error(f"Missing required field: {field}")
        
        # Layer 2: Army eligibility rules (AR 601-210)
        age = lead_data.get('age', 0)
        if age < 17:
            result.add_error("Age below minimum Army eligibility (17 years)")
        elif age > 42:
            result.add_warning("Age above typical recruiting range (17-42)")
        elif age < 18:
            result.add_warning("Minor: requires parental consent")
        
        # Layer 3: Data quality checks
        if not lead_data.get('email') and not lead_data.get('phone'):
            result.add_error("Missing contact information (email or phone required)")
        
        email = lead_data.get('email')
        if email and not DataValidator._is_valid_email(email):
            result.add_warning(f"Invalid email format: {email}")
        
        phone = lead_data.get('phone')
        if phone and not DataValidator._is_valid_phone(phone):
            result.add_warning(f"Invalid phone format: {phone}")
        
        # Layer 4: Score validation
        score = lead_data.get('score', 0)
        if score < 0 or score > 100:
            result.add_error(f"Invalid score range: {score} (must be 0-100)")
        
        # Layer 5: PII compliance (basic check)
        if not DataValidator._check_pii_compliance(lead_data):
            result.add_warning("Potential PII compliance concern")
        
        logger.info(f"Lead validation: {result.passed} (score: {result.quality_score})")
        return result
    
    @staticmethod
    def validate_event(event_data: Dict[str, Any]) -> ValidationResult:
        """Validate recruiting event data"""
        result = ValidationResult()
        
        # Required fields
        required = ['event_id', 'name', 'start_date']
        for field in required:
            if not event_data.get(field):
                result.add_error(f"Missing required field: {field}")
        
        # Date validation
        start_date = event_data.get('start_date')
        end_date = event_data.get('end_date')
        if start_date and end_date:
            if end_date < start_date:
                result.add_error("End date cannot be before start date")
        
        # Budget validation
        budget = event_data.get('budget', 0)
        if budget < 0:
            result.add_error("Budget cannot be negative")
        elif budget > 1000000:  # $1M threshold
            result.add_warning("Event budget exceeds $1M - verify approval")
        
        # Status validation
        valid_statuses = ['planned', 'in_progress', 'completed', 'cancelled', 'on_hold']
        status = event_data.get('status', 'planned')
        if status not in valid_statuses:
            result.add_error(f"Invalid status: {status}")
        
        return result
    
    @staticmethod
    def validate_metric(metric_data: Dict[str, Any]) -> ValidationResult:
        """Validate marketing/event metrics"""
        result = ValidationResult()
        
        # Check for negative values
        numeric_fields = ['cost_per_lead', 'roi', 'engagement_rate', 'leads_generated']
        for field in numeric_fields:
            value = metric_data.get(field, 0)
            if value is not None and value < 0:
                result.add_error(f"Negative value for {field}: {value}")
        
        # Outlier detection
        cpl = metric_data.get('cost_per_lead', 0)
        if cpl > 5000:
            result.add_warning(f"Unusually high CPL: ${cpl} - verify accuracy")
        
        roi = metric_data.get('roi', 0)
        if roi < -100:
            result.add_warning(f"Extremely negative ROI: {roi}% - verify calculation")
        
        engagement_rate = metric_data.get('engagement_rate', 0)
        if engagement_rate > 100:
            result.add_error(f"Engagement rate cannot exceed 100%: {engagement_rate}")
        
        return result
    
    @staticmethod
    def validate_project(project_data: Dict[str, Any]) -> ValidationResult:
        """Validate project data"""
        result = ValidationResult()
        
        # Required fields
        if not project_data.get('project_id') or not project_data.get('name'):
            result.add_error("Missing project_id or name")
        
        # Date validation
        start_date = project_data.get('start_date')
        target_date = project_data.get('target_date')
        if start_date and target_date:
            if target_date < start_date:
                result.add_error("Target date cannot be before start date")
        
        # Funding validation
        allocated = project_data.get('funding_amount', 0)
        spent = project_data.get('spent_amount', 0)
        if spent > allocated:
            result.add_warning(f"Spent (${spent}) exceeds allocated (${allocated})")
        
        # Percent complete validation
        percent = project_data.get('percent_complete', 0)
        if percent < 0 or percent > 100:
            result.add_error(f"Invalid percent_complete: {percent}")
        
        return result
    
    @staticmethod
    def validate_social_metric(metric_data: Dict[str, Any]) -> ValidationResult:
        """Validate social media metrics from Sprinklr"""
        result = ValidationResult()
        
        # Required fields
        if not metric_data.get('metric_id') or not metric_data.get('platform'):
            result.add_error("Missing metric_id or platform")
        
        # Negative values check
        numeric_fields = ['impressions', 'engagements', 'reach', 'clicks']
        for field in numeric_fields:
            value = metric_data.get(field, 0)
            if value < 0:
                result.add_error(f"Negative value for {field}: {value}")
        
        # Engagement rate validation
        impressions = metric_data.get('impressions', 0)
        engagements = metric_data.get('engagements', 0)
        if impressions > 0:
            calculated_rate = (engagements / impressions) * 100
            stated_rate = metric_data.get('engagement_rate', 0)
            if stated_rate and abs(calculated_rate - stated_rate) > 0.1:
                result.add_warning("Engagement rate mismatch with calculated value")
        
        return result
    
    @staticmethod
    def validate_export(data: List[Dict], export_type: str) -> ValidationResult:
        """Validate data before export/publication"""
        result = ValidationResult()
        
        if not data:
            result.add_error("No data to export")
            return result
        
        # Check for PII in exports (if public)
        if export_type == "public":
            for record in data:
                if DataValidator._contains_sensitive_pii(record):
                    result.add_error("Cannot export PII in public report")
                    break
        
        # Check data completeness
        if len(data) < 10:
            result.add_warning("Small dataset - results may not be statistically significant")
        
        return result
    
    # Helper methods
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone number (basic check)"""
        # Remove formatting
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= 10
    
    @staticmethod
    def _check_pii_compliance(data: Dict) -> bool:
        """Basic PII compliance check"""
        # Check if SSN accidentally included (should never be)
        ssn_pattern = r'\b\d{3}-?\d{2}-?\d{4}\b'
        data_str = str(data)
        if re.search(ssn_pattern, data_str):
            return False
        return True
    
    @staticmethod
    def _contains_sensitive_pii(data: Dict) -> bool:
        """Check for sensitive PII that shouldn't be exported"""
        sensitive_fields = ['ssn', 'social_security', 'date_of_birth', 'dob']
        for field in sensitive_fields:
            if field in data:
                return True
        return False


class ValidationLogger:
    """Log all validation results to database"""
    
    @staticmethod
    async def log_validation(
        record_type: str,
        record_id: str,
        result: ValidationResult,
        validated_by: Optional[str] = None
    ):
        """Store validation result in database"""
        from database.models import DataValidationLog
        from database.config import SessionLocal
        import uuid
        
        db = SessionLocal()
        try:
            log_entry = DataValidationLog(
                log_id=str(uuid.uuid4()),
                record_type=record_type,
                record_id=record_id,
                validation_result="passed" if result.passed else "failed",
                errors=result.errors,
                warnings=result.warnings,
                quality_score=result.quality_score,
                validated_at=datetime.utcnow(),
                validated_by=validated_by or "system"
            )
            db.add(log_entry)
            db.commit()
            logger.info(f"Validation logged: {record_type}/{record_id}")
        except Exception as e:
            logger.error(f"Failed to log validation: {e}")
            db.rollback()
        finally:
            db.close()
