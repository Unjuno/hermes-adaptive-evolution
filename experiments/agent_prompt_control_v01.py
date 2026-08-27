from __future__ import annotations

"""Agent Prompt control-surface experiment manifest.

This repository entry records the retained AP-1/AP-2/AP-3/AP-4/AP-4b experiment family.
The exact retained parameters and outputs live in:
- results/agent_prompt/ap1_agent_prompt_leverage_v01.json
- results/agent_prompt/agent_prompt_control_v01_summary.json
- docs/AGENT_PROMPT_GLOBAL_CONTROL_SURFACE_2026-08-28.md

Local full-fidelity experiment artifacts were generated in-session. This compact manifest is
kept on the active branch to bind the experiment family, decisions, and result files without
claiming an independent live-LLM run.
"""

EXPERIMENT_FAMILY = "humies.agent-prompt-control.v0.1"
DECISIONS = {
    "ap1_prompt_reuse_leverage": "positive_synthetic_evidence",
    "ap2_prompt_x_organization": "pass_in_synthetic_mechanism",
    "ap3_prompt_only_forever": "fail_as_allocation_rule",
    "ap4_always_audit_benign_edits": "not_supported",
    "ap4b_audited_immutable_overlay_under_reward_hack": "positive_synthetic_evidence",
}

if __name__ == "__main__":
    for key, value in DECISIONS.items():
        print(f"{key}: {value}")
