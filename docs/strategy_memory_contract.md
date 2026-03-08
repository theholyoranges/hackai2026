# Strategy Memory Contract

## Overview
The Restaurant Growth Copilot uses a deterministic, evidence-based recommendation system.
Strategies are NEVER invented by the LLM -- they are selected from a fixed playbook based on analytics evidence.

## Strategy Lifecycle

```
suggested -> accepted -> active -> evaluating -> successful | failed -> archived
```

### Status Definitions
- **suggested**: System has identified this strategy as applicable based on current analytics
- **accepted**: Restaurant owner has accepted the recommendation
- **active**: Strategy is currently being executed
- **evaluating**: Strategy execution is complete, measuring results
- **successful**: Strategy achieved its KPI targets
- **failed**: Strategy did not achieve targets or was abandoned
- **archived**: Strategy has been retired from active consideration

## Blocking Rules
1. **Active strategies** cannot be re-suggested (no duplicates)
2. **Recently failed strategies** are blocked for the cooldown period (default 14 days)
3. **Strategies in cooldown** cannot be re-suggested until cooldown_until date passes
4. **Successful strategies** produce scale-up recommendations instead of repetition

## Cooldown Logic
- Default cooldown: 14 days (configurable per strategy)
- Cooldown starts when a strategy is marked successful or failed
- During cooldown, the strategy code is blocked for that restaurant

## Evidence Requirements
- Every recommendation must include structured evidence (JSON)
- Evidence fields must match the strategy definition's expected_evidence_fields
- No recommendation can be generated without matching analytics data

## Confidence Scoring
- Each recommendation has a confidence score (0.0 to 1.0)
- Confidence must meet the strategy's confidence_threshold to be eligible
- Confidence is calculated from analytics data quality and match strength

## Ranking Formula
```
score = impact * confidence * (1.0 - recency_penalty)
```
- impact: derived from expected KPI targets
- confidence: from strategy matching
- recency_penalty: 0.5 if suggested <7 days ago, 0.3 if <14 days, 0.1 if <30 days
