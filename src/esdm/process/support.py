"""Set-valued ecological process support and monotone refinement."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Iterable, Mapping, Sequence


SEPARATOR_STATES = {"exclude", "compatible", "indeterminate", "unavailable"}


def _clean_name(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


@dataclass(frozen=True, slots=True)
class ProcessSupportSet:
    members: tuple[str, ...]

    def __post_init__(self) -> None:
        members = tuple(_clean_name(value, "process") for value in self.members)
        if len(set(members)) != len(members):
            raise ValueError("process support set contains duplicate members")
        object.__setattr__(self, "members", members)


@dataclass(frozen=True, slots=True)
class SeparatorEvidence:
    process: str
    separator_id: str
    evidence_state: str
    qualified: bool
    source_disjoint: bool
    preoutcome_frozen: bool

    def __post_init__(self) -> None:
        process = _clean_name(self.process, "process")
        separator_id = _clean_name(self.separator_id, "separator_id")
        evidence_state = _clean_name(self.evidence_state, "evidence_state")
        if evidence_state not in SEPARATOR_STATES:
            raise ValueError(f"unknown separator evidence state: {evidence_state}")
        for name in ("qualified", "source_disjoint", "preoutcome_frozen"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be boolean")
        object.__setattr__(self, "process", process)
        object.__setattr__(self, "separator_id", separator_id)
        object.__setattr__(self, "evidence_state", evidence_state)


@dataclass(frozen=True, slots=True)
class ProcessRefinement:
    base: ProcessSupportSet
    refined: ProcessSupportSet
    removed: tuple[str, ...]
    member_decisions: Mapping[str, str]
    contracted: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "member_decisions",
            MappingProxyType(dict(self.member_decisions)),
        )


def refine_process_support_set(
    base: ProcessSupportSet,
    evidence: Iterable[SeparatorEvidence],
    *,
    required_separator_ids: Sequence[str],
) -> ProcessRefinement:
    """Shrink a support set only under unanimous qualified new exclusion evidence.

    The routine never adds a process and never forces a unique winner. Missing,
    unavailable, indeterminate, compatible, or unqualified separator evidence retains
    the member. Evidence that reuses the support source or whose rule was not frozen
    before outcomes fails closed.
    """

    required_ids = tuple(_clean_name(value, "required_separator_id") for value in required_separator_ids)
    if not required_ids or len(set(required_ids)) != len(required_ids):
        raise ValueError("required_separator_ids must be a non-empty unique sequence")

    base_set = set(base.members)
    rows = tuple(evidence)
    seen: set[tuple[str, str]] = set()
    lookup: dict[tuple[str, str], SeparatorEvidence] = {}
    for row in rows:
        if row.process not in base_set:
            raise ValueError("separator evidence cannot introduce a process outside the base support set")
        key = (row.process, row.separator_id)
        if key in seen:
            raise ValueError("duplicate process/separator evidence")
        seen.add(key)
        if not row.source_disjoint:
            raise ValueError("separator evidence is not source-disjoint from support evidence")
        if not row.preoutcome_frozen:
            raise ValueError("separator decision rule was not frozen before outcomes")
        lookup[key] = row

    retained: list[str] = []
    removed: list[str] = []
    decisions: dict[str, str] = {}

    for process in base.members:
        process_rows: list[SeparatorEvidence] = []
        missing = False
        for separator_id in required_ids:
            row = lookup.get((process, separator_id))
            if row is None:
                missing = True
                break
            process_rows.append(row)

        if missing:
            retained.append(process)
            decisions[process] = "retain_missing_separator"
            continue

        if not all(row.qualified for row in process_rows):
            retained.append(process)
            decisions[process] = "retain_unqualified_separator"
            continue

        if all(row.evidence_state == "exclude" for row in process_rows):
            removed.append(process)
            decisions[process] = "remove_unanimous_exclusion"
            continue

        retained.append(process)
        decisions[process] = "retain_nonexclusion"

    refined = ProcessSupportSet(tuple(retained))
    return ProcessRefinement(
        base=base,
        refined=refined,
        removed=tuple(removed),
        member_decisions=decisions,
        contracted=bool(removed),
    )
