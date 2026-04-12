from typing import Any, Dict, List, Callable, Optional


class Rule:
    def __init__(self, id: str, source: str, category: str, condition: Callable[[Dict[str, Any]], bool], action: str, weight: float, explanation: str, tags: Optional[List[str]] = None):
        self.id = id
        self.source = source
        self.category = category
        self.condition = condition
        self.action = action
        self.weight = weight
        self.explanation = explanation
        self.tags = tags or []


class DoctrineEngine:
    """Lightweight rule engine for mapping recommendations to doctrine.

    Rules are intentionally simple, deterministic, and easy to extend. Each
    rule evaluates a callable `condition` against an input context (merged
    recommendation + evidence) and yields metadata for triggered rules.
    """

    def __init__(self):
        self.rules: List[Rule] = []
        self._register_default_rules()

    def _register_default_rules(self):
        # Targeting: demographic age band for late teen/young adult
        self.rules.append(Rule(
            id="UR_601_210_TARGETING_01",
            source="UR 601-210",
            category="Targeting",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('median_age') is not None and 17 <= (ctx.get('market', {}) or {}).get('median_age') <= 24,
            action="prioritize_high_school_engagement",
            weight=0.9,
            explanation="Primary recruiting demographic per UR 601-210"
        ))

        # Recruiting ops: mission capacity and available slots
        self.rules.append(Rule(
            id="UR_601_106_MISSION_CAPACITY_01",
            source="UR 601-106",
            category="RecruitingOps",
            condition=lambda ctx: (ctx.get('mission', {}) or {}).get('mission_total', 0) > 0,
            action="allocate_resources_to_unfilled_slots",
            weight=0.8,
            explanation="Mission allocation available; align recruiting resources"
        ))

        # Outreach: school enrollment high and historical production exists
        self.rules.append(Rule(
            id="UR_27_4_OUTREACH_01",
            source="UR 27-4",
            category="Outreach",
            condition=lambda ctx: (ctx.get('school', {}) or {}).get('enrollment', 0) >= 200 and (ctx.get('school', {}) or {}).get('components', {}).get('historical_production', 0) > 0,
            action="deploy_outreach_campaign",
            weight=0.85,
            explanation="Engage large schools with demonstrated historical production"
        ))

        # Heuristic: if recommendation type mentions targeting/school, map to outreach + targeting
        self.rules.append(Rule(
            id="UR_27_4_HEURISTIC_01",
            source="UR 27-4",
            category="Heuristic",
            condition=lambda ctx: ('recommendation' in ctx and isinstance(ctx.get('recommendation'), dict) and ('target' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower() or 'school' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower())),
            action="heuristic_map_outreach",
            weight=0.6,
            explanation="Heuristic mapping: recommendation_type implies outreach/targeting"
        ))

        # Companion heuristic to map to UR 601-210 (targeting/demographics)
        self.rules.append(Rule(
            id="UR_601_210_HEURISTIC_01",
            source="UR 601-210",
            category="Heuristic",
            condition=lambda ctx: ('recommendation' in ctx and isinstance(ctx.get('recommendation'), dict) and ('target' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower() or 'school' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower())),
            action="heuristic_map_targeting",
            weight=0.6,
            explanation="Heuristic mapping: recommendation_type implies targeting demographics"
        ))

        # Heuristic: mission/allocation recommendation types map to UR 350-1 and UR 601-106
        self.rules.append(Rule(
            id="UR_350_1_HEURISTIC_01",
            source="UR 350-1",
            category="Heuristic",
            condition=lambda ctx: ('recommendation' in ctx and isinstance(ctx.get('recommendation'), dict) and ('mission' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower() or 'allocation' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower())),
            action="heuristic_map_mission_ops",
            weight=0.6,
            explanation="Heuristic mapping: recommendation_type implies mission/ops relevance"
        ))

        self.rules.append(Rule(
            id="UR_601_106_HEURISTIC_01",
            source="UR 601-106",
            category="Heuristic",
            condition=lambda ctx: ('recommendation' in ctx and isinstance(ctx.get('recommendation'), dict) and ('mission' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower() or 'allocation' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower())),
            action="heuristic_map_mission_admin",
            weight=0.6,
            explanation="Heuristic mapping: recommendation_type implies mission resource/admin relevance"
        ))

        # Heuristic: market-analysis recommendation types map to UM 3-0 and UTP 3-10.2
        self.rules.append(Rule(
            id="UM_3_0_HEURISTIC_01",
            source="UM 3-0",
            category="Heuristic",
            condition=lambda ctx: ('recommendation' in ctx and isinstance(ctx.get('recommendation'), dict) and 'market' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower()),
            action="heuristic_map_market",
            weight=0.6,
            explanation="Heuristic mapping: recommendation_type implies market analysis"
        ))

        self.rules.append(Rule(
            id="UTP_3_10_2_HEURISTIC_01",
            source="UTP 3-10.2",
            category="Heuristic",
            condition=lambda ctx: ('recommendation' in ctx and isinstance(ctx.get('recommendation'), dict) and 'market' in (ctx.get('recommendation') or {}).get('recommendation_type', '').lower()),
            action="heuristic_map_tactical",
            weight=0.5,
            explanation="Heuristic mapping: tactical employment reference for market analysis"
        ))


        # Market-analysis anchor: local market share high
        self.rules.append(Rule(
            id="UM_3_0_MARKET_01",
            source="UM 3-0",
            category="MarketAnalysis",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('avg_share', 0) >= 0.25,
            action="increase_market_focus",
            weight=0.7,
            explanation="Market share indicates operationally significant opportunity"
        ))

        # Eligibility: age-eligible population density
        self.rules.append(Rule(
            id="UR_601_210_AGE_DENSITY_01",
            source="UR 601-210",
            category="Targeting",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('age_eligible_pct', 0) >= 0.20,
            action="prioritize_age_eligible_reach",
            weight=0.9,
            explanation="High share of age-eligible population per UR 601-210",
            tags=['ASCOPE', 'market', 'demographics']
        ))

        # Infrastructure/logistics anchor (planning support)
        self.rules.append(Rule(
            id="UM_3_30_INFRA_01",
            source="UM 3-30",
            category="Planning",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('infrastructure_score', 0) >= 0.7,
            action="consider_fixed_site_operations",
            weight=0.7,
            explanation="Sufficient local infrastructure to support fixed-site recruiting (UM 3-30)",
            tags=['PMESII-PT', 'infrastructure']
        ))

        # Access constraint: flag restricted access or hostile environment
        self.rules.append(Rule(
            id="UM_3_31_ACCESS_01",
            source="UM 3-31",
            category="Constraints",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('access_restrictions') is True or (ctx.get('school', {}) or {}).get('access') == 'restricted',
            action="flag_access_constraint",
            weight=0.2,
            explanation="Access restrictions detected; operations constrained",
            tags=['ASCOPE', 'access']
        ))

        # Conflict detection: high enrollment but zero historical production
        self.rules.append(Rule(
            id="CONFLICT_HIGH_ENROLL_LOW_PROD_01",
            source="UM 3-0",
            category="DataQuality",
            condition=lambda ctx: (ctx.get('school', {}) or {}).get('enrollment', 0) >= 200 and (ctx.get('school', {}) or {}).get('components', {}).get('historical_production', 0) == 0,
            action="flag_conflicting_signals",
            weight=0.25,
            explanation="High enrollment with no historical production — verify local conversion factors",
            tags=['risk', 'data_quality']
        ))

        # Rural/mobile ops: prefer mobile recruiting when rural indicator set
        self.rules.append(Rule(
            id="UR_601_210_RURAL_01",
            source="UR 601-210",
            category="Targeting",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('rural', False) is True,
            action="prioritize_mobile_recruit_teams",
            weight=0.6,
            explanation="Rural area detected; deploy mobile recruiting per UR 601-210",
            tags=['ASCOPE', 'rural']
        ))

        # PMESII-PT / ASCOPE rules
        # Political: low political risk favors outreach
        self.rules.append(Rule(
            id="PMESII_POLITICAL_LOW_RISK_01",
            source="PMESII-Political",
            category="PMESII-Political",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('political_risk') is not None and (ctx.get('market', {}) or {}).get('political_risk') <= 0.3,
            action="favor_outreach_due_to_stability",
            weight=0.6,
            explanation="Low political risk suggests stable environment for engagement",
            tags=['PMESII', 'political']
        ))

        # Economic: favorable economic index improves conversion prospects
        self.rules.append(Rule(
            id="PMESII_ECONOMIC_INDEX_01",
            source="PMESII-Economic",
            category="PMESII-Economic",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('economic_index', 0) >= 0.6,
            action="prioritize_market_with_strong_economy",
            weight=0.5,
            explanation="Stronger local economy indicates higher outreach ROI",
            tags=['PMESII', 'economic']
        ))

        # Social: social cohesion low (unrest) reduces confidence
        self.rules.append(Rule(
            id="PMESII_SOCIAL_UNREST_01",
            source="PMESII-Social",
            category="PMESII-Social",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('social_unrest', False) is True,
            action="deprioritize_outreach_due_to_unrest",
            weight=0.2,
            explanation="Social unrest detected; operations risk increased",
            tags=['PMESII', 'social', 'risk']
        ))

        # Information environment: high media influence needs tailored messaging
        self.rules.append(Rule(
            id="ASCOPE_INFORMATION_ENV_01",
            source="ASCOPE-Information",
            category="ASCOPE-Information",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('media_influence', 0) >= 0.7,
            action="tailor_messaging_for_information_environment",
            weight=0.45,
            explanation="High media influence; messaging must be adapted",
            tags=['ASCOPE', 'information']
        ))

        # Structures: presence of community centers or schools with facilities
        self.rules.append(Rule(
            id="ASCOPE_STRUCTURES_COMMUNITY_01",
            source="ASCOPE-Structures",
            category="ASCOPE-Structures",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('community_centers', 0) >= 1 or (ctx.get('school', {}) or {}).get('facilities', False) is True,
            action="use_local_structures_as_event_sites",
            weight=0.6,
            explanation="Local community structures available for events/outreach",
            tags=['ASCOPE', 'structures']
        ))

        # Population movement: high transient population increases targeting difficulty
        self.rules.append(Rule(
            id="PMESII_POP_MOVEMENT_01",
            source="PMESII-Physical",
            category="PMESII-Physical",
            condition=lambda ctx: (ctx.get('market', {}) or {}).get('population_transient_pct', 0) >= 0.3,
            action="flag_transient_population",
            weight=0.3,
            explanation="High transient population; adapt engagement strategy",
            tags=['PMESII', 'population', 'mobility']
        ))

        # Fallback: low data quality
        self.rules.append(Rule(
            id="FALLBACK_LOW_DATA_01",
            source="UM 3-0",
            category="DataQuality",
            condition=lambda ctx: ctx.get('data_quality') == 'low' or ((ctx.get('school', {}) or {}).get('confidence_score', 1) < 0.4),
            action="flag_low_confidence",
            weight=0.3,
            explanation="Insufficient data quality; treat recommendation cautiously"
        ))

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all rules against the merged input context.

        Returns a dict with triggered rules, aggregated doctrine refs and a
        brief rationale list.
        """
        triggered: List[Dict[str, Any]] = []
        refs: List[str] = []
        rationale: List[str] = []
        score = 0.0
        for r in self.rules:
            try:
                if r.condition(context):
                    triggered.append({
                        'id': r.id,
                        'source': r.source,
                        'category': r.category,
                        'action': r.action,
                        'weight': r.weight,
                        'explanation': r.explanation
                    })
                    refs.append(r.source)
                    rationale.append(r.explanation)
                    score += r.weight
            except Exception:
                # keep engine robust: ignore rule errors
                continue

        # normalize score into [0,1] by dividing by number of rules (simple)
        norm = 0.0
        if len(self.rules) > 0:
            norm = min(1.0, score / float(len(self.rules)))

        return {
            'triggered_rules': triggered,
            'doctrine_refs': list(sorted(set(refs))),
            'rationale': rationale,
            'rule_alignment_score': round(norm, 2)
        }


# Singleton engine for module-level use
ENGINE = DoctrineEngine()
