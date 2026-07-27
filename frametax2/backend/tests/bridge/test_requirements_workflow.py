from __future__ import annotations

import pytest

from app.bridge.requirements_workflow import (
    ProfileAcceptanceRefused,
    accept_profile,
    build_research_brief,
    compare_candidate_facts,
    draft_profile,
    parse_candidate_response,
    select_missing_programs,
)
from app.bridge.schema import ErrorCategory, ModelResponse, OperationType, ProviderID


def _fake_response(provider, model_id, program_slug, jurisdiction_code, facts, sources):
    return ModelResponse(
        provider=provider, model_id=model_id, operation=OperationType.REQUIREMENTS_RESEARCH,
        parsed_response={
            "research_id": f"r-{provider.value}", "package_id": "pkg_x",
            "program_slug": program_slug, "jurisdiction_code": jurisdiction_code,
            "candidate_facts": facts, "source_records": sources,
        },
    )


_PRIMARY_SOURCE = {
    "source_title": "Official gov page", "source_url": "https://gov.example/incentive",
    "publisher_authority": "Ministry of Culture", "source_type": "primary",
    "proposition_supported": "preapproval required", "primary_or_secondary": "primary",
}
_SECONDARY_SOURCE = {
    "source_title": "Industry blog", "source_url": "https://blog.example/incentive",
    "publisher_authority": "Some Blog", "source_type": "secondary",
    "proposition_supported": "preapproval required", "primary_or_secondary": "secondary",
}


class TestSelectMissingPrograms:
    def test_returns_real_gap_from_canonical_registry(self):
        targets = select_missing_programs(limit=5)
        assert len(targets) == 5
        assert all(t.program_slug and t.jurisdiction_code for t in targets)

    def test_limit_respected(self):
        assert len(select_missing_programs(limit=3)) == 3

    def test_no_limit_returns_full_gap(self):
        # The gap shrinks as Database Completion phase batches land (was
        # ~93-98, now 40 at 70/110 executable jurisdictions profiled,
        # 2026-07-26) -- assert a floor tied to the executable registry
        # itself rather than a point-in-time snapshot, so this doesn't
        # need re-pinning every batch.
        from app.data.canonical_executable_registry import canonical_executable_jurisdictions
        from app.data.program_requirements import get_program_requirements

        total_executable = len(canonical_executable_jurisdictions())
        unprofiled = sum(
            1 for e in canonical_executable_jurisdictions().values()
            if get_program_requirements(e.primary_program_slug) is None
        )
        targets = select_missing_programs()
        assert len(targets) > 0
        assert len(targets) <= total_executable
        assert len(targets) == unprofiled


class TestBuildResearchBrief:
    def test_brief_includes_already_known_rate_structure(self):
        target = select_missing_programs(limit=1)[0]
        brief = build_research_brief(target, ProviderID.ANTHROPIC, "claude-test")
        assert brief.structured_input["program_slug"] == target.program_slug
        assert "already_known_rate_structure" in brief.structured_input

    def test_brief_allows_web_search(self):
        target = select_missing_programs(limit=1)[0]
        brief = build_research_brief(target, ProviderID.OPENAI, "gpt-test")
        assert brief.allow_web_search is True


class TestParseCandidateResponse:
    def test_valid_response_parses(self):
        response = _fake_response(
            ProviderID.ANTHROPIC, "claude-test", "test_slug", "TC",
            [{"field_name": "preapproval_mandatory", "proposed_value": True,
              "source_index": 0, "confidence": 0.9}],
            [_PRIMARY_SOURCE],
        )
        candidate = parse_candidate_response(response, "pkg_x")
        assert candidate is not None
        assert len(candidate.candidate_facts) == 1

    def test_error_response_returns_none(self):
        response = ModelResponse(
            provider=ProviderID.ANTHROPIC, model_id="x", operation=OperationType.REQUIREMENTS_RESEARCH,
            error_category=ErrorCategory.AUTH,
        )
        assert parse_candidate_response(response, "pkg_x") is None

    def test_malformed_parsed_response_returns_none_never_raises(self):
        response = ModelResponse(
            provider=ProviderID.ANTHROPIC, model_id="x", operation=OperationType.REQUIREMENTS_RESEARCH,
            parsed_response={"totally": "wrong shape"},
        )
        assert parse_candidate_response(response, "pkg_x") is None

    def test_out_of_range_source_index_is_dropped_not_crashed(self):
        response = _fake_response(
            ProviderID.ANTHROPIC, "claude-test", "test_slug", "TC",
            [{"field_name": "preapproval_mandatory", "proposed_value": True,
              "source_index": 5, "confidence": 0.9}],  # only 1 source exists
            [_PRIMARY_SOURCE],
        )
        candidate = parse_candidate_response(response, "pkg_x")
        assert candidate.candidate_facts == []


class TestCompareAndDraft:
    def test_primary_source_agreement_across_two_providers(self):
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", "slug", "TC",
            [{"field_name": "preapproval_mandatory", "proposed_value": True, "source_index": 0, "confidence": 0.9}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        c2 = parse_candidate_response(_fake_response(
            ProviderID.OPENAI, "gpt", "slug", "TC",
            [{"field_name": "preapproval_mandatory", "proposed_value": True, "source_index": 0, "confidence": 0.8}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        comparisons = compare_candidate_facts([c1, c2])
        assert comparisons["preapproval_mandatory"].is_primary_source_agreement is True

    def test_consensus_without_primary_source_is_flagged_separately(self):
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", "slug", "TC",
            [{"field_name": "refundable", "proposed_value": True, "source_index": 0, "confidence": 0.6}],
            [_SECONDARY_SOURCE],
        ), "pkg_x")
        c2 = parse_candidate_response(_fake_response(
            ProviderID.OPENAI, "gpt", "slug", "TC",
            [{"field_name": "refundable", "proposed_value": True, "source_index": 0, "confidence": 0.6}],
            [_SECONDARY_SOURCE],
        ), "pkg_x")
        comparisons = compare_candidate_facts([c1, c2])
        cmp = comparisons["refundable"]
        assert cmp.is_model_consensus_only is True
        assert cmp.is_primary_source_agreement is False

    def test_conflicting_values_are_flagged_as_conflict(self):
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", "slug", "TC",
            [{"field_name": "refundable", "proposed_value": True, "source_index": 0, "confidence": 0.6}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        c2 = parse_candidate_response(_fake_response(
            ProviderID.OPENAI, "gpt", "slug", "TC",
            [{"field_name": "refundable", "proposed_value": False, "source_index": 0, "confidence": 0.6}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        comparisons = compare_candidate_facts([c1, c2])
        assert comparisons["refundable"].is_conflict is True

    def test_draft_excludes_consensus_only_and_conflicted_fields(self):
        target = select_missing_programs(limit=1)[0]
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", target.program_slug, target.jurisdiction_code,
            [
                {"field_name": "preapproval_mandatory", "proposed_value": True, "source_index": 0, "confidence": 0.9},
                {"field_name": "refundable", "proposed_value": True, "source_index": 1, "confidence": 0.5},
            ],
            [_PRIMARY_SOURCE, _SECONDARY_SOURCE],
        ), "pkg_x")
        draft = draft_profile(target, compare_candidate_facts([c1]))
        assert "preapproval_mandatory" in draft.fields
        assert "refundable" not in draft.fields
        assert "refundable" in draft.model_consensus_only_fields


class TestAcceptProfile:
    def test_refuses_blank_actor(self, clean_requirements_registry):
        target = select_missing_programs(limit=1)[0]
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", target.program_slug, target.jurisdiction_code,
            [{"field_name": "preapproval_mandatory", "proposed_value": True, "source_index": 0, "confidence": 0.9}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        draft = draft_profile(target, compare_candidate_facts([c1]))
        with pytest.raises(ProfileAcceptanceRefused, match="real accepted_by identity"):
            accept_profile(draft, accepted_by="")

    def test_refuses_when_conflicts_unresolved(self, clean_requirements_registry):
        target = select_missing_programs(limit=1)[0]
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", target.program_slug, target.jurisdiction_code,
            [{"field_name": "refundable", "proposed_value": True, "source_index": 0, "confidence": 0.6}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        c2 = parse_candidate_response(_fake_response(
            ProviderID.OPENAI, "gpt", target.program_slug, target.jurisdiction_code,
            [{"field_name": "refundable", "proposed_value": False, "source_index": 0, "confidence": 0.6}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        draft = draft_profile(target, compare_candidate_facts([c1, c2]))
        with pytest.raises(ProfileAcceptanceRefused, match="unresolved conflicts"):
            accept_profile(draft, accepted_by="tester")

    def test_refuses_when_nothing_primary_source_backed(self, clean_requirements_registry):
        target = select_missing_programs(limit=1)[0]
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", target.program_slug, target.jurisdiction_code,
            [{"field_name": "refundable", "proposed_value": True, "source_index": 0, "confidence": 0.6}],
            [_SECONDARY_SOURCE],
        ), "pkg_x")
        draft = draft_profile(target, compare_candidate_facts([c1]))
        with pytest.raises(ProfileAcceptanceRefused, match="No primary-source-backed fields"):
            accept_profile(draft, accepted_by="tester")

    def test_successful_acceptance_writes_to_real_registry(self, clean_requirements_registry):
        from app.data.program_requirements import get_program_requirements

        target = select_missing_programs(limit=1)[0]
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", target.program_slug, target.jurisdiction_code,
            [{"field_name": "preapproval_mandatory", "proposed_value": True, "source_index": 0,
              "confidence": 0.9, "is_hard_eligibility_gate": True}],
            [_PRIMARY_SOURCE],
        ), "pkg_x")
        draft = draft_profile(target, compare_candidate_facts([c1]))
        profile = accept_profile(draft, accepted_by="claude-session-test")
        assert profile.preapproval_mandatory is True
        assert get_program_requirements(target.program_slug) is profile

    def test_consensus_only_fields_never_written_even_when_present(self, clean_requirements_registry):
        target = select_missing_programs(limit=1)[0]
        c1 = parse_candidate_response(_fake_response(
            ProviderID.ANTHROPIC, "claude", target.program_slug, target.jurisdiction_code,
            [
                {"field_name": "preapproval_mandatory", "proposed_value": True, "source_index": 0, "confidence": 0.9},
                {"field_name": "refundable", "proposed_value": True, "source_index": 1, "confidence": 0.5},
            ],
            [_PRIMARY_SOURCE, _SECONDARY_SOURCE],
        ), "pkg_x")
        draft = draft_profile(target, compare_candidate_facts([c1]))
        profile = accept_profile(draft, accepted_by="tester")
        assert profile.refundable is None  # consensus-only field never promoted
