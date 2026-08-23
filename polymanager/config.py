"""Central configuration: bankroll, risk tiers, and drawdown rules.

These are the defaults described in the portfolio-manager mandate. They are
guidelines, not hardcoded law -- callers may override them, but nothing in
this module silently changes behavior based on bankroll growth (that
decision belongs to the strategy layer, deliberately, per the "do not
increase risk just because bankroll grew" rule).
"""

from dataclasses import dataclass

STARTING_BANKROLL_USD = 200.0

GAMMA_API_BASE = "https://gamma-api.polymarket.com"
CLOB_API_BASE = "https://clob.polymarket.com"
DATA_API_BASE = "https://data-api.polymarket.com"

# Minimum market-quality bar. Markets failing any of these are rejected
# before any probability/EV analysis is performed (MARKET SELECTION FILTER).
MIN_LIQUIDITY_USD = 2_000.0
MIN_24H_VOLUME_USD = 500.0
MAX_SPREAD = 0.06
MIN_HOURS_TO_RESOLUTION = 2.0


@dataclass(frozen=True)
class RiskTier:
    name: str
    min_pct: float
    max_pct: float
    min_edge_pp: float  # minimum edge, in percentage points, required to qualify
    min_confidence: int  # 1-10


TIERS = {
    "T1_HIGH_CONFIDENCE": RiskTier("Tier 1 - High Confidence", 0.05, 0.12, 10.0, 8),
    "T2_MEDIUM_CONFIDENCE": RiskTier("Tier 2 - Medium Confidence", 0.02, 0.06, 6.0, 6),
    "T3_EXPERIMENTAL": RiskTier("Tier 3 - Experimental", 0.005, 0.03, 3.0, 4),
}

# Drawdown safeguards, measured against the bankroll's high-water mark.
DRAWDOWN_RULES = [
    # (drawdown_threshold, size_multiplier, description)
    (0.30, 0.0, "Stop all aggressive strategies. Diagnose before resuming."),
    (0.20, 0.25, "Cut risk substantially. Review strategy performance."),
    (0.10, 0.5, "Reduce position sizing."),
    (0.0, 1.0, "Normal sizing."),
]

# Fractional-Kelly multipliers by confidence bucket (1-10 scale).
#
# Confidence 4 exists here to match T3_EXPERIMENTAL.min_confidence (4) --
# without it, kelly.recommended_position_size gave confidence-4
# opportunities a 0.0 multiplier (the next bucket down was 5), which
# always zeroed out sizing even for a real, tier-qualifying edge. Found
# live 2026-08-20: polymanager.btc_touch caps its own confidence at
# CONFIDENCE_CAP=4 (deliberately, per that module's backtest finding),
# which meant that entire strategy could never produce a trade regardless
# of edge size -- a live BTC market showing a real, tier-qualifying 5.2pp
# edge sized to exactly $0. 1/8-Kelly is deliberately the most
# conservative nonzero fraction in this table, one step down from 1/4.
KELLY_FRACTION_BY_CONFIDENCE = [
    (9, 0.5),   # very high confidence -> up to half-Kelly
    (7, 1 / 3),
    (5, 0.25),
    (4, 1 / 8),
    (0, 0.0),   # below 4/10 confidence: below every tier's floor, no bet
]

MAX_SINGLE_POSITION_PCT = 0.12  # hard ceiling regardless of Kelly output
MAX_CORRELATED_GROUP_PCT = 0.20  # cap on aggregate exposure to correlated events
