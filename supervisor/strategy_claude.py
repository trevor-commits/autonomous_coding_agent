from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

from jsonschema import Draft202012Validator

from supervisor.actions import Action, ActionValidationError, validate_action_for_phase
from supervisor.contracts import RepoContract, RunContract
from supervisor.models import Phase
from supervisor.strategy_simple import SimpleStrategy
from supervisor.verifier import VerificationSummary


DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT_SECONDS = 30
PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "strategy-decision.schema.json"
API_URL = "https://api.anthropic.com/v1/messages"

PROMPT_FILES = {
    "planner": "planner.txt",
    "builder_task_shaper": "builder-task-shaper.txt",
    "stall_diagnosis": "stall-diagnosis.txt",
    "candidate_review": "candidate-review.txt",
    "final_audit": "final-audit.txt",
}

Transport = Callable[[str, str, int, int, str], dict[str, Any]]


@dataclass(frozen=True)
class StrategyUsage:
    prompt_name: str
    input_tokens: int
    output_tokens: int
    estimated_cost_dollars: float


class ClaudeStrategy:
    """Anthropic-backed strategy adapter with strict typed-action fallback."""

    def __init__(
        self,
        *,
        fallback: SimpleStrategy | None = None,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        prompt_dir: Path | None = None,
        transport: Transport | None = None,
        input_cost_per_million_tokens: float = 0.0,
        output_cost_per_million_tokens: float = 0.0,
    ) -> None:
        self.fallback = fallback or SimpleStrategy()
        self.api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.prompt_dir = Path(prompt_dir or PROMPT_DIR)
        self.transport = transport or self._default_transport
        self.input_cost_per_million_tokens = input_cost_per_million_tokens
        self.output_cost_per_million_tokens = output_cost_per_million_tokens
        self.invocation_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_dollars = 0.0
        self._pending_cost_dollars = 0.0
        self._planned_run_ids: set[str] = set()
        self._validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text()))

    def build_action(
        self,
        run_contract: RunContract,
        repo_contract: RepoContract,
        *,
        prior_failure_fingerprints: tuple[str, ...],
    ) -> Action:
        fallback_action = self.fallback.build_action(
            run_contract,
            repo_contract,
            prior_failure_fingerprints=prior_failure_fingerprints,
        )
        prompt_name = (
            "planner"
            if run_contract.run_id not in self._planned_run_ids
            else "builder_task_shaper"
        )
        action = self._request_action(
            phase=Phase.BUILD,
            prompt_name=prompt_name,
            context={
                "run_contract": run_contract.to_dict(),
                "repo_contract": repo_contract.to_dict(),
                "prior_failure_fingerprints": prior_failure_fingerprints,
                "fallback_description": fallback_action.payload["description"],
            },
            fallback_action=fallback_action,
        )
        self._planned_run_ids.add(run_contract.run_id)
        return action

    def app_launch_repair_action(
        self,
        run_contract: RunContract,
        *,
        failure_reason: str,
        failure_fingerprint: str | None,
    ) -> Action:
        fallback_action = self.fallback.app_launch_repair_action(
            run_contract,
            failure_reason=failure_reason,
            failure_fingerprint=failure_fingerprint,
        )
        return self._request_action(
            phase=Phase.BUILD,
            prompt_name="stall_diagnosis",
            context={
                "run_contract": run_contract.to_dict(),
                "failure_reason": failure_reason,
                "failure_fingerprint": failure_fingerprint,
                "failure_type": "app_launch",
                "fallback_description": fallback_action.payload["description"],
            },
            fallback_action=fallback_action,
        )

    def ui_repair_action(
        self,
        run_contract: RunContract,
        *,
        defect_packets: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ) -> Action:
        fallback_action = self.fallback.ui_repair_action(
            run_contract,
            defect_packets=defect_packets,
        )
        return self._request_action(
            phase=Phase.BUILD,
            prompt_name="stall_diagnosis",
            context={
                "run_contract": run_contract.to_dict(),
                "failure_type": "ui_verify",
                "defect_packets": tuple(defect_packets),
                "fallback_description": fallback_action.payload["description"],
            },
            fallback_action=fallback_action,
        )

    def blocking_action_for_failure(
        self,
        summary: VerificationSummary,
        *,
        attempt: int,
        max_repair_loops: int,
    ) -> Action | None:
        return self.fallback.blocking_action_for_failure(
            summary,
            attempt=attempt,
            max_repair_loops=max_repair_loops,
        )

    def consume_pending_cost(self) -> float:
        pending = self._pending_cost_dollars
        self._pending_cost_dollars = 0.0
        return pending

    def _request_action(
        self,
        *,
        phase: Phase,
        prompt_name: str,
        context: dict[str, Any],
        fallback_action: Action,
    ) -> Action:
        if not self.api_key:
            return fallback_action

        prompt = self._render_prompt(prompt_name, context)
        try:
            response = self.transport(
                self.api_key,
                self.model,
                self.max_tokens,
                self.timeout_seconds,
                prompt,
            )
        except Exception:
            return fallback_action

        self.invocation_count += 1
        self._record_usage(prompt_name, response)

        try:
            text = _extract_response_text(response)
            payload = _extract_json_payload(text)
            self._validator.validate(payload)
            action = Action.from_mapping(payload)
            validate_action_for_phase(phase, action)
        except (json.JSONDecodeError, ActionValidationError, ValueError):
            return fallback_action

        return action

    def _record_usage(self, prompt_name: str, response: dict[str, Any]) -> StrategyUsage:
        usage = response.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        estimated_cost = (
            (input_tokens * self.input_cost_per_million_tokens)
            + (output_tokens * self.output_cost_per_million_tokens)
        ) / 1_000_000
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_dollars += estimated_cost
        self._pending_cost_dollars += estimated_cost
        return StrategyUsage(
            prompt_name=prompt_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_dollars=estimated_cost,
        )

    def _render_prompt(self, prompt_name: str, context: dict[str, Any]) -> str:
        template_name = PROMPT_FILES[prompt_name]
        template = (self.prompt_dir / template_name).read_text()
        context_json = json.dumps(context, indent=2, sort_keys=True)
        schema_json = json.dumps(json.loads(SCHEMA_PATH.read_text()), indent=2, sort_keys=True)
        return (
            template.replace("{{CONTEXT_JSON}}", context_json)
            .replace("{{SCHEMA_JSON}}", schema_json)
            .replace("{{MODEL_NAME}}", self.model)
        )

    def _default_transport(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        timeout_seconds: int,
        prompt: str,
    ) -> dict[str, Any]:
        payload = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        http_request = request.Request(
            API_URL,
            data=payload,
            headers={
                "content-type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(body) from exc
        return json.loads(body)


def _extract_response_text(response: dict[str, Any]) -> str:
    content = response.get("content", ())
    text_blocks = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    if text_blocks:
        return "\n".join(text_blocks).strip()
    raise ValueError("Claude response did not contain a text block.")


def _extract_json_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    if stripped.startswith("{"):
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError("Strategy payload must be a JSON object.")
        return payload

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Strategy payload did not include a JSON object.")
    payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("Strategy payload must be a JSON object.")
    return payload
