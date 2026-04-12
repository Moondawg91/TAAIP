"""
Canonical mission-alignment input template for TAAIP.

This module defines the `MISSION_ALIGNMENT_TEMPLATE` object which will be
used as the canonical shape for commander intent and mission-alignment
information before any AI parsing of ROP / School Plans is introduced.
"""

MISSION_ALIGNMENT_TEMPLATE = {
    "commander_intent": "",
    "mission_statement": "",
    "priorities": [],
    "loes": [],
    "decisive_points": [],
    "risks": [],
    "targeting_guidance": [],
    "school_recruiting_guidance": [],
    "constraints": [],
    "assumptions": [],
    "task_organization": [],
    "planning_horizon": "FY",
    "source_document_type": None,
}
