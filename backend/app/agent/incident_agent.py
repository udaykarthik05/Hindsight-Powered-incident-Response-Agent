import re
from typing import List, Optional

from app.agent.analysis import DeterministicAnalyzer
from app.agent.llm import LLMClient
from app.agent.models import (
    HistoricalContext,
    HistoricalIncidentMatch,
    InvestigationResult,
)
from app.agent.prompts import SYSTEM_PROMPT, build_investigation_user_prompt
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.hindsight.memory import (
    HindsightError,
    HindsightMemoryService,
    MemoryRecallInput,
    MemoryReflectInput,
    get_memory_service,
)
from app.schemas.incident import Incident

logger = get_logger("agent.core")


class IncidentResponseAgent:
    """
    Core AI Incident Response Agent orchestrating:
    1. Deterministic evidence and signal extraction
    2. Hindsight RECALL (historical memory retrieval)
    3. Hindsight REFLECT (comparative historical reasoning)
    4. LLM synthesis into structured hypotheses, investigation steps, and remediations.
    """

    def __init__(
        self,
        memory_service: Optional[HindsightMemoryService] = None,
        llm_client: Optional[LLMClient] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.memory_service = memory_service or get_memory_service()
        self.llm_client = llm_client or LLMClient(self.settings)

    async def investigate(self, incident: Incident) -> InvestigationResult:
        """
        Execute full investigation pipeline for a given incident.
        """
        logger.info(
            "Starting agent investigation for incident %s: '%s' on %s",
            incident.incident_id,
            incident.title,
            incident.affected_service,
        )

        # ----------------------------------------------------------------------
        # 1. Deterministic Signal Analysis
        # ----------------------------------------------------------------------
        signals, recall_query = DeterministicAnalyzer.analyze(incident)
        logger.info(
            "Deterministic signals extracted: %d error types, %d components, categories: %s",
            len(signals.error_types),
            len(signals.infrastructure_components),
            signals.suspected_categories,
        )

        # ----------------------------------------------------------------------
        # 2. Hindsight RECALL
        # ----------------------------------------------------------------------
        recalled_matches: List[HistoricalIncidentMatch] = []
        historical_available = False
        reflection_summary: Optional[str] = None
        status_msg: str

        try:
            logger.info("Executing Hindsight RECALL with query: '%s'", recall_query)
            recall_response = await self.memory_service.recall(
                MemoryRecallInput(
                    query=recall_query,
                    budget="mid",
                    max_tokens=4096,
                    bank_id=self.settings.hindsight_bank_id,
                )
            )
            historical_available = True
            raw_results = recall_response.results or []
            logger.info("Hindsight RECALL returned %d historical memory units", len(raw_results))

            seen_ids = set()
            for res in raw_results:
                text_content = getattr(res, "text", str(res))
                scores = getattr(res, "scores", None)
                tags = getattr(res, "tags", []) or []
                metadata = getattr(res, "metadata", {}) or {}

                # Extract incident ID from metadata or text
                matched_id = metadata.get("incident_id")
                title_match = metadata.get("title")

                if not matched_id:
                    postmortem_match = re.search(r"POSTMORTEM RECORD:\s*(\S+)\s*[—–-]\s*([^\n\r]+)", text_content)
                    if postmortem_match:
                        matched_id = postmortem_match.group(1).strip()
                        if not title_match:
                            title_match = postmortem_match.group(2).strip()
                    else:
                        id_match = re.search(r"\b(INC-[\w-]+|PHASE6-[\w-]+)\b", text_content)
                        if id_match:
                            matched_id = id_match.group(1).strip()
                        else:
                            matched_id = "HISTORICAL-MEMORY"

                if not title_match:
                    first_line = text_content.splitlines()[0] if text_content else ""
                    title_match = first_line[:80].strip() if first_line else f"Historical Incident ({matched_id})"

                # Parse score accurately from RecallScores model or dict
                sim_score = None
                if scores is not None:
                    if hasattr(scores, "final") and scores.final is not None:
                        sim_score = round(float(scores.final), 3)
                    elif hasattr(scores, "reranker") and scores.reranker is not None:
                        sim_score = round(float(scores.reranker), 3)
                    elif hasattr(scores, "semantic") and scores.semantic is not None:
                        sim_score = round(float(scores.semantic), 3)
                    elif isinstance(scores, dict):
                        score_val = scores.get("final") or scores.get("reranker") or scores.get("combined") or scores.get("similarity")
                        if score_val is not None:
                            sim_score = round(float(score_val), 3)

                # Deduplicate by matched_id if already added
                if matched_id != "HISTORICAL-MEMORY" and matched_id in seen_ids:
                    continue
                if matched_id != "HISTORICAL-MEMORY":
                    seen_ids.add(matched_id)

                recalled_matches.append(
                    HistoricalIncidentMatch(
                        incident_id=matched_id,
                        title=title_match,
                        service=metadata.get("service", incident.affected_service),
                        similarity_score=sim_score,
                        summary=text_content[:300],
                        tags=tags,
                    )
                )

            status_msg = f"Retrieved {len(recalled_matches)} historical incidents from Hindsight."

            # ------------------------------------------------------------------
            # 3. Hindsight REFLECT (only if recall produced matches)
            # ------------------------------------------------------------------
            if recalled_matches:
                reflect_query = (
                    f"Given current symptoms '{', '.join(signals.suspected_categories)}' in {incident.affected_service}, "
                    "compare against historical incident memories. What previous root causes and successful mitigation "
                    "strategies are most relevant to investigate first?"
                )
                try:
                    logger.info("Executing Hindsight REFLECT...")
                    reflect_response = await self.memory_service.reflect(
                        MemoryReflectInput(
                            query=reflect_query,
                            budget="low",
                            bank_id=self.settings.hindsight_bank_id,
                        )
                    )
                    reflection_summary = getattr(reflect_response, "text", str(reflect_response))
                    logger.info("Hindsight REFLECT synthesized successfully.")
                except Exception as reflect_err:
                    logger.warning("Hindsight REFLECT failed (%s), proceeding with RECALL context only.", reflect_err)
                    reflection_summary = None

        except (HindsightError, Exception) as recall_err:
            logger.warning(
                "Hindsight memory is unreachable (%s: %s). Proceeding with current evidence analysis only.",
                type(recall_err).__name__,
                recall_err,
            )
            historical_available = False
            status_msg = "Hindsight memory service is currently offline. Historical cross-referencing skipped."

        historical_context = HistoricalContext(
            available=historical_available,
            query_used=recall_query,
            recalled_incidents=recalled_matches,
            reflection_summary=reflection_summary,
            status_message=status_msg,
        )

        # ----------------------------------------------------------------------
        # 4. LLM Synthesis & Hypothesis Generation
        # ----------------------------------------------------------------------
        user_prompt = build_investigation_user_prompt(incident, signals, historical_context)
        investigation_result = await self.llm_client.generate_investigation(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            incident=incident,
            signals=signals,
            historical=historical_context,
        )

        logger.info(
            "Investigation concluded for %s: generated %d hypotheses, %d steps, confidence: %.2f",
            incident.incident_id,
            len(investigation_result.hypotheses),
            len(investigation_result.investigation_steps),
            investigation_result.confidence,
        )
        return investigation_result


# Global singleton agent instance
_agent_instance: Optional[IncidentResponseAgent] = None


def get_incident_agent() -> IncidentResponseAgent:
    """Dependency provider returning singleton IncidentResponseAgent."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = IncidentResponseAgent()
    return _agent_instance
