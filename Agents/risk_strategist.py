"""
Risk Strategist Agent Module.

GAMP 5 and CSA Compliant Risk Assessment Logic.
"""
from enum import Enum
from typing import Tuple


class RiskLevel(Enum):
    """
    Risk level classification per GAMP 5 guidelines.

    :requirement: URS-3.1 - System shall classify risk as Low, Medium, or High.
    """

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Severity(Enum):
    """
    Severity classification for patient safety impact.

    :requirement: URS-3.2 - System shall assess severity based on patient impact.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Occurrence(Enum):
    """
    Occurrence classification for likelihood of failure.

    :requirement: URS-3.3 - System shall assess occurrence likelihood.
    """

    RARE = 1
    OCCASIONAL = 2
    FREQUENT = 3


class Detectability(Enum):
    """
    Detectability classification for ability to detect failures.

    :requirement: URS-3.4 - System shall assess detectability of failures.
    """

    HIGH = 1      # Easy to detect
    MEDIUM = 2    # Moderately detectable
    LOW = 3       # Hard to detect


class TestingStrategy(Enum):
    """
    CSA-aligned testing strategy recommendations.

    :requirement: URS-4.1 - System shall recommend testing strategy per CSA.
    """

    UNSCRIPTED = "Unscripted Testing"
    HYBRID = "Hybrid Testing (Scripted + Unscripted)"
    RIGOROUS_SCRIPTED = "Rigorous Scripted Testing"


def calculate_risk_score(
    severity: Severity,
    occurrence: Occurrence,
    detectability: Detectability
) -> Tuple[int, RiskLevel]:
    """
    Calculate Risk Priority Number (RPN) and determine risk level.

    Implements GAMP 5 risk-based approach where patient safety (severity)
    takes precedence. If severity is HIGH, risk is automatically HIGH
    regardless of other factors.

    :param severity: The severity of potential patient/product impact.
    :param occurrence: The likelihood of the failure occurring.
    :param detectability: The ability to detect the failure before impact.
    :return: Tuple of (RPN score, RiskLevel classification).
    :requirement: URS-4.2 - System shall calculate risk using GAMP 5 methodology.
    """
    # GAMP 5 Rule: Patient Safety First
    # If severity is HIGH, risk is HIGH regardless of other factors
    if severity == Severity.HIGH:
        rpn = severity.value * occurrence.value * detectability.value
        return (rpn, RiskLevel.HIGH)

    # Calculate Risk Priority Number (RPN)
    rpn = severity.value * occurrence.value * detectability.value

    # Determine risk level based on RPN thresholds
    risk_level = _determine_risk_level(rpn)

    return (rpn, risk_level)


def _determine_risk_level(rpn: int) -> RiskLevel:
    """
    Determine risk level based on Risk Priority Number.

    :param rpn: The calculated Risk Priority Number (1-27 scale).
    :return: RiskLevel classification.
    :requirement: URS-4.3 - System shall classify RPN into risk categories.
    """
    if rpn <= 4:
        return RiskLevel.LOW
    elif rpn <= 12:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def get_csa_testing_strategy(risk_level: RiskLevel) -> TestingStrategy:
    """
    Recommend CSA-aligned testing strategy based on risk level.

    Per CSA guidance, low-risk systems benefit from unscripted testing
    which leverages tester expertise, while high-risk systems require
    rigorous scripted testing for full traceability.

    :param risk_level: The assessed risk level of the change.
    :return: Recommended TestingStrategy.
    :requirement: URS-4.4 - System shall recommend CSA testing strategy.
    """
    if risk_level == RiskLevel.LOW:
        return TestingStrategy.UNSCRIPTED
    elif risk_level == RiskLevel.MEDIUM:
        return TestingStrategy.HYBRID
    else:
        return TestingStrategy.RIGOROUS_SCRIPTED


def map_criticality_to_severity(system_criticality: str) -> Severity:
    """
    Map ServiceNow system criticality to GAMP 5 severity.

    :param system_criticality: The criticality string from ServiceNow.
    :return: Corresponding Severity enum value.
    :requirement: URS-4.5 - System shall map external criticality to severity.
    """
    criticality_map = {
        "high": Severity.HIGH,
        "critical": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "moderate": Severity.MEDIUM,
        "low": Severity.LOW,
        "minor": Severity.LOW
    }
    return criticality_map.get(system_criticality.lower(), Severity.MEDIUM)


def map_change_type_to_occurrence(change_type: str) -> Occurrence:
    """
    Map ServiceNow change type to occurrence likelihood.

    :param change_type: The change type string from ServiceNow.
    :return: Corresponding Occurrence enum value.
    :requirement: URS-4.6 - System shall map change type to occurrence.
    """
    change_type_map = {
        "emergency": Occurrence.FREQUENT,
        "expedited": Occurrence.FREQUENT,
        "normal": Occurrence.OCCASIONAL,
        "standard": Occurrence.RARE,
        "routine": Occurrence.RARE
    }
    return change_type_map.get(change_type.lower(), Occurrence.OCCASIONAL)


def assess_change_request(
    system_criticality: str,
    change_type: str,
    detectability: Detectability = Detectability.MEDIUM
) -> dict:
    """
    Perform full risk assessment for a ServiceNow change request.

    :param system_criticality: The system criticality from ServiceNow CR.
    :param change_type: The change type from ServiceNow CR.
    :param detectability: Detection capability (defaults to MEDIUM).
    :return: Dictionary containing full risk assessment results.
    :requirement: URS-4.7 - System shall assess risk for all change requests.
    """
    severity = map_criticality_to_severity(system_criticality)
    occurrence = map_change_type_to_occurrence(change_type)

    rpn, risk_level = calculate_risk_score(severity, occurrence, detectability)
    testing_strategy = get_csa_testing_strategy(risk_level)

    return {
        "severity": severity.name,
        "occurrence": occurrence.name,
        "detectability": detectability.name,
        "rpn": rpn,
        "risk_level": risk_level.value,
        "testing_strategy": testing_strategy.value,
        "patient_safety_override": severity == Severity.HIGH
    }
