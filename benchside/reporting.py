"""Offline aggregate report from operator-authorised R2 downloads.

Links new contributions by a pseudonymous store ID; emits aggregate counts only. Highest weekly
usage revisions replace earlier snapshots; repeated uploads never add counts.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from benchside.domain.export.model.metascience import (
    MANUAL_SAMPLING,
    TextAnswer,
    parse_activity,
    parse_survey,
)
from benchside.domain.export.model.reporting import UsagePayload, parse_feedback
from benchside.domain.export.model.wire import validate_payload
from benchside.domain.shared.error import BenchsideError


def summarise(files):
    gaps, feedback, usage, surveys, activity = {}, {}, {}, {}, {}
    gap_contributors = {}
    invalid, conflicts = 0, set()
    for path in files:
        try:
            text = Path(path).read_text(encoding="utf-8")
            data = json.loads(text)
            schema = data.get("schema")
            if schema in {"benchside.gaps.v1", "benchside.gaps.v2", "benchside.gaps.v3"}:
                for item in validate_payload(text)["observations"]:
                    previous = gaps.get(item["id"])
                    if previous is not None and previous != item:
                        conflicts.add(("gaps", item["id"]))
                    owner = data.get("contributor_id")
                    if item["id"] in gap_contributors and gap_contributors[item["id"]] != owner:
                        conflicts.add(("gaps", item["id"]))
                    gap_contributors[item["id"]] = owner
                    gaps[item["id"]] = item
            elif schema in {"benchside.feedback.v1", "benchside.feedback.v2"}:
                parsed = parse_feedback(text)
                existing = feedback.get(parsed.feedback.id)
                if existing is not None and existing != parsed:
                    conflicts.add(("feedback", parsed.feedback.id))
                feedback[parsed.feedback.id] = parsed
            elif schema == "benchside.usage.v1":
                parsed = UsagePayload.model_validate_json(text)
                key = (parsed.installation_id, parsed.week)
                previous = usage.get(key)
                if previous and previous.revision == parsed.revision and previous != parsed:
                    conflicts.add(("usage", *key, parsed.revision))
                if previous is None or parsed.revision > previous.revision:
                    usage[key] = parsed
            elif schema in {"benchside.survey.v1", "benchside.survey.v2"}:
                parsed = parse_survey(text)
                previous = surveys.get(parsed.response_id)
                if previous and previous != parsed:
                    conflicts.add(("survey", parsed.response_id))
                surveys[parsed.response_id] = parsed
            elif schema in {"benchside.activity.v1", "benchside.activity.v2"}:
                parsed = parse_activity(text)
                previous = activity.get(parsed.batch_id)
                if previous and previous.sampling != parsed.sampling:
                    conflicts.add(("activity-method", parsed.batch_id))
                if previous and getattr(previous, "contributor_id", None) != getattr(
                    parsed, "contributor_id", None
                ):
                    conflicts.add(("activity-method", parsed.batch_id))
                if previous and previous.revision == parsed.revision and previous != parsed:
                    conflicts.add(("activity", parsed.batch_id, parsed.revision))
                if previous is None or parsed.revision > previous.revision:
                    activity[parsed.batch_id] = parsed
            else:
                invalid += 1
        except (BenchsideError, OSError, ValueError, TypeError, AttributeError):
            invalid += 1
    gaps = {k: v for k, v in gaps.items() if ("gaps", k) not in conflicts}
    feedback = {k: v for k, v in feedback.items() if ("feedback", k) not in conflicts}
    usage = {
        key: value
        for key, value in usage.items()
        if ("usage", *key, value.revision) not in conflicts
    }
    surveys = {k: v for k, v in surveys.items() if ("survey", k) not in conflicts}
    activity = {
        k: v
        for k, v in activity.items()
        if ("activity", k, v.revision) not in conflicts and ("activity-method", k) not in conflicts
    }
    survey_counts = Counter()
    survey_text_counts = Counter()
    activity_counts = Counter()
    activity_contexts = Counter()
    by_sampling = {}
    for survey in surveys.values():
        for question, answer in survey.answers.items():
            if isinstance(answer, TextAnswer):
                survey_text_counts[f"{survey.study_id}@{survey.study_version}/{question}"] += 1
                continue
            survey_counts[
                f"{survey.study_id}@{survey.study_version}/{survey.study_sha256}/{question}/{answer}"
            ] += 1
    for batch in activity.values():
        method = by_sampling.setdefault(
            batch.sampling,
            {
                "batches": 0,
                "coverage": Counter(),
                "findings": Counter(),
            },
        )
        method["batches"] += 1
        method["coverage"].update(
            {
                "eligible_in_submitted_batches": batch.eligible,
                "selected_in_submitted_batches": batch.selected,
                "reviewed_and_shared": len(batch.observations),
            }
        )
        for observation in batch.observations:
            context = {"none": "outside_benchside", "unknown": "unknown"}.get(
                observation.benchside_role, "benchside"
            )
            activity_contexts[context] += 1
            findings = Counter()
            for field in ("activity", "obstacle", "verification", "outcome"):
                finding = getattr(observation, field)
                findings[f"{field}/{finding.value}/{finding.basis}"] += 1
            findings[f"benchside_role/{observation.benchside_role}"] += 1
            findings[f"host/{observation.host}"] += 1
            activity_counts.update(findings)
            method["findings"].update(findings)
    active = defaultdict(set)
    uses = Counter()
    weekly = defaultdict(lambda: Counter())
    roles, hosts, app_versions, versions, errors = (
        Counter(),
        Counter(),
        Counter(),
        Counter(),
        Counter(),
    )
    for (installation, week), report in usage.items():
        for row in report.sessions:
            if (
                row.started
                or row.concluded
                or row.abandoned
                or sum(row.records.model_dump().values())
            ):
                active[week].add(installation)
            uses[installation] += row.started
            roles[row.role] += row.started
            hosts[f"{row.host}/{row.surface}"] += row.started
            app_versions[f"{row.host}@{row.app_version}"] += row.started
            versions[f"{report.benchside_version} / {row.role}@{row.role_version}"] += row.started
            for field in ("started", "concluded", "abandoned"):
                weekly[week][field] += getattr(row, field)
        errors.update(report.errors)
    # One demographic entry per participating installation, from its latest accepted
    # weekly snapshot. The aggregate output does not expose per-store records.
    latest = {}
    for (installation, week), report in usage.items():
        previous = latest.get(installation)
        if previous is None or (week, report.revision) > (previous.week, previous.revision):
            latest[installation] = report
    demographic_counts = {"discipline": Counter(), "career_stage": Counter()}
    for report in latest.values():
        if report.demographics:
            for field, value in report.demographics.model_dump(exclude_none=True).items():
                demographic_counts[field][value] += 1
    weeks_by_installation = Counter(i for installations in active.values() for i in installations)
    contributors = {
        "gaps": {gap_contributors[key] for key in gaps if gap_contributors.get(key)},
        "feedback": {getattr(v, "contributor_id", None) for v in feedback.values()} - {None},
        "usage": {key[0] for key in usage},
        "surveys": {getattr(v, "contributor_id", None) for v in surveys.values()} - {None},
        "activity": {getattr(v, "contributor_id", None) for v in activity.values()} - {None},
    }
    contributor_channels = Counter(
        identifier for identifiers in contributors.values() for identifier in identifiers
    )
    gap_kind_contributors = defaultdict(set)
    for key, item in gaps.items():
        if gap_contributors.get(key):
            gap_kind_contributors[item["gap"]["kind"]].add(gap_contributors[key])
    return {
        "workflow_observations": len(gaps),
        "workflow_origins": dict(
            sorted(Counter(o.get("origin", "legacy_unknown") for o in gaps.values()).items())
        ),
        "workflow_kinds": dict(sorted(Counter(o["gap"]["kind"] for o in gaps.values()).items())),
        "contributing_stores": len(contributor_channels),
        "contributing_stores_by_channel": {key: len(value) for key, value in contributors.items()},
        "stores_contributing_multiple_channels": sum(n > 1 for n in contributor_channels.values()),
        "contributing_stores_by_workflow_kind": {
            key: len(value) for key, value in sorted(gap_kind_contributors.items())
        },
        "feedback_submissions": len(feedback),
        "feedback_ease": dict(
            sorted(Counter(str(f.feedback.ease) for f in feedback.values()).items())
        ),
        "feedback_repeat_intent": dict(
            sorted(Counter(f.feedback.would_use_again for f in feedback.values()).items())
        ),
        "demographic_installations": sum(
            bool(r.demographics and r.demographics.model_dump(exclude_none=True))
            for r in latest.values()
        ),
        "installations_by_discipline": dict(sorted(demographic_counts["discipline"].items())),
        "installations_by_career_stage": dict(sorted(demographic_counts["career_stage"].items())),
        "active_installations": len(weeks_by_installation),
        "returning_installations_across_weeks": sum(n >= 2 for n in weeks_by_installation.values()),
        "installations_with_multiple_consultations": sum(n >= 2 for n in uses.values()),
        "weekly": {
            week: {"active_installations": len(active[week]), **dict(weekly[week])}
            for week in sorted(set(active) | set(weekly))
        },
        "consultations_by_role": dict(sorted(roles.items())),
        "consultations_by_app": dict(sorted(hosts.items())),
        "consultations_by_app_version": dict(sorted(app_versions.items())),
        "consultations_by_version": dict(sorted(versions.items())),
        "failures": dict(sorted(errors.items())),
        "survey_submissions": len(surveys),
        "survey_answers": dict(sorted(survey_counts.items())),
        "survey_free_text_responses": dict(sorted(survey_text_counts.items())),
        "activity_batches": len(activity),
        "activity_coverage": {
            "eligible_in_submitted_batches": sum(b.eligible for b in activity.values()),
            "selected_in_submitted_batches": sum(b.selected for b in activity.values()),
            "reviewed_and_shared": sum(len(b.observations) for b in activity.values()),
        },
        "activity_findings": dict(sorted(activity_counts.items())),
        "activity_contexts": dict(sorted(activity_contexts.items())),
        "activity_by_sampling": {
            key: {
                "batches": value["batches"],
                "coverage": dict(value["coverage"]),
                "findings": dict(sorted(value["findings"].items())),
            }
            for key, value in sorted(by_sampling.items())
        },
        "invalid_files": invalid,
        "conflicting_snapshots": len(conflicts),
        "interpretation": "Opt-in stores/installations, not unique people or total adoption. New contributions can be linked by a random store ID after the updated explanation is accepted; legacy unlinked records remain unlinked. Workflow problems are the primary output; activity categories provide supporting context. Outside-Benchside conversations are not Benchside usage. Completion does not establish scientific benefit. Demographic buckets describe optional self-reports from each installation's latest accepted weekly snapshot, not population estimates. Activity totals pool submitted batches only; use activity_by_sampling to distinguish legacy percentage sampling, capped random selection and manual selection. Manual eligible counts describe only the researcher-chosen set, not a population denominator or frequency estimate. Random selection covers only the supplied accessible research inventory. Historical legacy samples may cover a partial week. Model-inferred findings and researcher-reported outcomes are distinct; review and nonresponse introduce selection bias. Validate the classifier on separately consented examples before making accuracy claims. These exploratory rollout findings are separate from the original paper evaluation.",
    }


def markdown(report):
    lines = [
        "# Benchside rollout report",
        "",
        report["interpretation"],
        "",
        f"- Active installations: {report['active_installations']}",
        f"- Returning across weeks: {report['returning_installations_across_weeks']}",
        f"- Multiple consultations: {report['installations_with_multiple_consultations']}",
        f"- Workflow observations: {report['workflow_observations']}",
        f"- Feedback submissions: {report['feedback_submissions']}",
        f"- Survey submissions: {report['survey_submissions']}",
        f"- Research activity batches: {report['activity_batches']}",
        f"- Invalid files: {report['invalid_files']}; conflicting snapshots: {report['conflicting_snapshots']}",
    ]
    for label, key in [
        ("Weekly activity", "weekly"),
        ("Workflow problems", "workflow_kinds"),
        ("Contributing stores by workflow kind", "contributing_stores_by_workflow_kind"),
        ("Workflow observation sources", "workflow_origins"),
        ("Optional discipline buckets (installations)", "installations_by_discipline"),
        ("Optional career-stage buckets (installations)", "installations_by_career_stage"),
        ("Roles used", "consultations_by_role"),
        ("Apps used", "consultations_by_app"),
        ("App versions", "consultations_by_app_version"),
        ("Versions", "consultations_by_version"),
        ("Ease of use (1–5)", "feedback_ease"),
        ("Would use again", "feedback_repeat_intent"),
        ("Failures", "failures"),
        ("Survey answers (study/version/definition/question/answer)", "survey_answers"),
        ("Pooled activity counts (submitted batches only)", "activity_coverage"),
        ("Pooled activity findings and evidence basis", "activity_findings"),
        ("Activity with and without Benchside roles", "activity_contexts"),
    ]:
        lines += ["", f"## {label}", "", "| Measure | Count |", "|---|---|"]
        for name, value in report[key].items():
            rendered = (
                ", ".join(f"{k}: {v}" for k, v in value.items())
                if isinstance(value, dict)
                else str(value)
            )
            lines.append(f"| {name} | {rendered} |")
        if not report[key]:
            lines.append("| No reports yet | — |")
    for method, values in report.get("activity_by_sampling", {}).items():
        label = (
            "Researcher-chosen conversations" if method == MANUAL_SAMPLING else "Random selection"
        )
        lines += ["", f"## {label}: {method}", ""]
        if method == MANUAL_SAMPLING:
            lines += [
                "Eligible counts cover only the chosen set; no population frequency estimate.",
                "",
            ]
        lines += ["| Measure | Count |", "|---|---|"]
        for key, value in {
            "batches": values["batches"],
            **values["coverage"],
            **values["findings"],
        }.items():
            lines.append(f"| {key} | {value} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    files = sorted(
        {
            p
            for source in args.inputs
            for p in (source.rglob("*.json") if source.is_dir() else [source])
        }
    )
    report = summarise(files)
    print(json.dumps(report, indent=2) if args.json else markdown(report))


if __name__ == "__main__":
    main()
