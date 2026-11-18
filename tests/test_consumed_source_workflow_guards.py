"""Regression tests for historically consumed empirical one-shot workflows.

A previous NEON C2 workflow accidentally matched every *new* PR opened.
This tests that new PRs or additional run attempts cannot activate it.
The original Actions run snapshots remain outside the repository's control.
"""
from pathlib import Path

import pytest


SOURCE_WORKFLOWS = {
    'neon-c2-region-pool-null.yml': {
        'pr_number': 235,
        'head_sha': 'b3921e1d9cb3a10ff5ae525836a93c04761a8d54',
        'event': 'opened',
        'event_types': 'types: [opened]',
    },
    'camtrapasia-spatial-ibe.yml': {
        'pr_number': 234,
        'head_sha': '8cb348c1996343c25b55c7c86d9679beb04d9449',
        'event': 'reopened',
        'event_types': 'types: [opened, reopened]',
    },
}


def expected_job_guard(spec: dict) -> str:
    return (
        f"github.event.action == '{spec['event']}'"
        f" && github.event.pull_request.number == {spec['pr_number']}"
        f" && github.event.pull_request.head.sha == '{spec['head_sha']}'"
        ' && github.run_attempt == 1'
    )


def source_job_guard(workflow: str, spec: dict) -> str:
    """Reject trigger broadening without a third-party YAML parser."""
    lines = workflow.splitlines()
    if 'on:' not in lines or 'jobs:' not in lines:
        raise ValueError('workflow structure has no on/jobs blocks')
    on = lines.index('on:')
    jobs = lines.index('jobs:')
    trigger_end = next((i for i in range(on+1, len(lines))
                        if lines[i] and not lines[i].startswith((' ', '#'))), None)
    if trigger_end is None:
        raise ValueError('unterminated event trigger block')
    trigger = lines[on+1:trigger_end]
    if trigger[0].strip() != 'pull_request:' or len([x for x in trigger if x.startswith('  ') and not x.startswith('    ') and x.strip()]) != 1:
        raise ValueError('must have only pull_request trigger')
    if not any(x.strip() == spec['event_types'] for x in trigger):
        raise ValueError('changed allowed trigger event')
    guards = [x.strip()[4:].strip() for x in lines[jobs+1:] if x.startswith('    if: ')]
    if len(guards) != 1 or guards[0] != expected_job_guard(spec):
        raise ValueError('one-shot job must have exact historical PR/head and attempt=1 guard')
    return guards[0]


def permitted_event(spec: dict, *, event: str, pr_number: int, sha: str, run_attempt: int) -> bool:
    return (
        event == spec['event'] and pr_number == spec['pr_number']
        and sha == spec['head_sha'] and run_attempt == 1
    )


@pytest.mark.parametrize('workflow', sorted(SOURCE_WORKFLOWS))
def test_consumed_workflow_exact_guard_in_checkout(workflow):
    spec = SOURCE_WORKFLOWS[workflow]
    path = Path(__file__).resolve().parents[1] / '.github' / 'workflows' / workflow
    text = path.read_text(encoding='utf-8')
    assert source_job_guard(text, spec) == expected_job_guard(spec)


@pytest.mark.parametrize('workflow', sorted(SOURCE_WORKFLOWS))
def test_unrelated_pr_and_attempt_two_are_disallowed(workflow):
    spec = SOURCE_WORKFLOWS[workflow]
    assert permitted_event(spec, event=spec['event'], pr_number=spec['pr_number'],
                           sha=spec['head_sha'], run_attempt=1)
    assert not permitted_event(spec, event='opened', pr_number=236,
                               sha='25f976637f4e823f7c6c93ad288630ba1d9ff87d', run_attempt=1)
    assert not permitted_event(spec, event=spec['event'], pr_number=spec['pr_number'],
                               sha=spec['head_sha'], run_attempt=2)


def test_broad_action_only_gate_is_refused():
    spec=SOURCE_WORKFLOWS['neon-c2-region-pool-null.yml']
    body='on:\n  pull_request:\n    types: [opened]\njobs:\n  one_shot:\n    if: github.event.action == \'opened\'\n'
    with pytest.raises(ValueError, match='historical PR/head'):
        source_job_guard(body, spec)


def test_extra_trigger_is_refused():
    spec=SOURCE_WORKFLOWS['neon-c2-region-pool-null.yml']
    body='on:\n  pull_request:\n    types: [opened]\n  workflow_dispatch:\njobs:\n  one_shot:\n    if: '+expected_job_guard(spec)+'\n'
    with pytest.raises(ValueError, match='only pull_request trigger'):
        source_job_guard(body, spec)
