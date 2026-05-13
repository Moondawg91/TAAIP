from typing import Dict, List


def recommendations_for_classification(classification: str, role: str = "commander") -> List[Dict]:
    c = (classification or "insufficient_data").lower()

    mapping = {
        "execution_failure": [
            "processing_pipeline_fundamentals",
            "stage_management_and_follow_through",
            "future_soldier_management_basics",
        ],
        "access_constrained": [
            "school_access_planning",
            "community_engagement_and_access_negotiation",
            "zip_to_school_zone_alignment",
        ],
        "effort_misaligned": [
            "targeting_board_d3ae_f3a",
            "effort_allocation_by_market_signal",
            "message_channel_frequency_optimization",
        ],
        "market_constrained": [
            "market_intelligence_and_segmentation",
            "opportunity_development_in_weak_markets",
        ],
        "leadership_or_training_issue": [
            "leader_coaching_for_recruiting_teams",
            "metric_discipline_and_accountability",
        ],
        "balanced": [
            "advanced_optimization_and_scaling",
        ],
        "insufficient_data": [
            "data_quality_and_reporting_standards",
        ],
    }

    modules = mapping.get(c, mapping["insufficient_data"])
    return [
        {
            "module_key": m,
            "role": role,
            "delivery": "lms",
            "priority": idx + 1,
        }
        for idx, m in enumerate(modules)
    ]
