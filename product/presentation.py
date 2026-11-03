from dataclasses import fields, replace
from html import escape
import re
from urllib.parse import urlencode

from product.errors import ErrorCategory, ProductError
from product.models import (
    ProductAppositionPayload, ProductCandidate, ProductClausePayload, ProductEvaluation,
    ProductPage, ProductSelection, ProductSourceNode, ProductToken, ProjectionState,
)
from product import wording


def _text(value: str | int | None) -> str:
    if value is None:
        return "(absent)"
    if value == "":
        return "(present, empty)"
    return escape(str(value), quote=True)


def _human(value: str | None) -> str:
    if value is None:
        return "no label recorded"
    visible = "".join(
        f"U+{ord(c):04X}" if (
            0x202A <= ord(c) <= 0x202E or 0x2066 <= ord(c) <= 0x2069
            or (ord(c) < 0x20 and c not in "\n\t") or 0x7F <= ord(c) <= 0x9F
        ) else c for c in value
    )
    return f"<bdi>{_text(visible)}</bdi>"


def _error(error: ProductError | None) -> str:
    if error is None:
        return ""
    if error.category == ErrorCategory.PROJECTION_STORE_NOT_CONFIGURED:
        return f'<p class="store-state">{_text(error.message)}</p>'
    return (f'<p class="notice" data-error="{_text(error.category.value)}">'
            f'<strong>{_text(error.category.value)}</strong>: {_text(error.message)}</p>')


def _rows(values: tuple[tuple[str, str | int | None], ...]) -> str:
    return "<dl>" + "".join(
        f"<dt>{_text(label)}</dt><dd>{_text(value)}</dd>" for label, value in values
    ) + "</dl>"


def _refs(refs: tuple[str, ...]) -> str:
    return '<ul class="refs">' + "".join(f"<li>{_text(ref)}</li>" for ref in refs) + "</ul>"


def _url(selection: ProductSelection) -> str:
    values: dict[str, str | int] = {"chapter": selection.chapter, "verse": selection.verse}
    if selection.token_ordinal is not None:
        values["token"] = selection.token_ordinal
    for name, value, pattern in (
        ("candidate", selection.candidate_id, r"sha256:[0-9a-f]{64}"),
        ("evaluation", selection.evaluation_id, r"eval-sha256:[0-9a-f]{64}"),
    ):
        if value is not None:
            if re.fullmatch(pattern, value) is None:
                raise ValueError("invalid logical selection")
            values[name] = value
    return escape("/verse?" + urlencode(values), quote=True)


def _node(node: ProductSourceNode) -> str:
    result = _rows((
        ("source_node_id", node.source_node_id),
        ("parent_source_node_id", node.parent_source_node_id),
        ("sibling_ordinal", node.sibling_ordinal), ("Cat", node.cat),
        ("Rule", node.rule), ("ClType", node.cl_type),
    ))
    if node.cl_type == "Verbless":
        result += f"<p>ClType: Verbless</p><p>{wording.VERBLESS_NOTE}</p>"
    return result + "<details><summary>Advanced node facts</summary>" + _rows((
        ("Id", node.id_raw), ("Head", node.head_raw),
    )) + "</details>"


_TOKEN_BASELINE = (
    ("ref", "ref"), ("chapter", "chapter"), ("verse", "verse"), ("ordinal", "ordinal"),
    ("surface", "surface"), ("unicode", "unicode"), ("normalized", "normalized"),
    ("lemma", "lemma"), ("Cat", "cat"), ("language", "language"), ("case", "case"),
    ("gender", "gender"), ("number", "number"), ("person", "person"),
    ("tense", "tense"), ("voice", "voice"), ("mood", "mood"), ("degree", "degree"),
    ("type", "type"), ("FunctionalTag", "functional_tag"), ("FormalTag", "formal_tag"),
    ("strong_number", "strong_number"),
)
_TOKEN_ADVANCED = (
    ("english", "english"), ("mandarin", "mandarin"), ("gloss", "gloss"),
    ("referent (source Ref)", "referent"), ("upstream_node_id", "upstream_node_id"),
    ("xml_id", "xml_id"), ("morph_id", "morph_id"),
)


def _token_details(token: ProductToken) -> str:
    return ("<h3>Token facts</h3>" + _rows(tuple(
        (label, getattr(token, attr)) for label, attr in _TOKEN_BASELINE
    )) + "<details><summary>Advanced token facts</summary>" + _rows(tuple(
        (label, getattr(token, attr)) for label, attr in _TOKEN_ADVANCED
    )) + "</details>")


def _source(page: ProductPage) -> str:
    if page.verse is None or page.selection is None:
        return _error(page.error) if page.error is not None else "<p>Enter a chapter and verse.</p>"
    selected = page.selected_candidate
    members = set(selected.member_token_refs) if selected is not None else set()
    component_labels: dict[str, str] = {}
    if selected is not None and isinstance(selected.payload, ProductClausePayload):
        for component in selected.payload.components:
            for ref in component.member_token_refs:
                component_labels[ref] = component.component_role
    tokens: list[str] = []
    for token in page.verse.tokens:
        member = token.ref in members
        membership = "member" if member else "non-member"
        is_selected = page.selected_token is not None and page.selected_token.key == token.key
        css = "token selected-token" if is_selected else "token"
        accessible = ("member of selected candidate" if member
                      else "not in selected candidate scope")
        marker = '<span class="member-marker" aria-hidden="true">&#x25AE;</span>' if member else ""
        label = (f'<span class="component-label">{_text(component_labels[token.ref])}</span>'
                 if token.ref in component_labels else "")
        link = _url(replace(page.selection, token_ordinal=token.ordinal, evaluation_id=None))
        current = ' aria-current="true"' if is_selected else ""
        tokens.append(
            f'<a class="{css}" data-ref="{_text(token.ref)}" data-membership="{membership}" '
            f'href="{link}"{current}>'
            f'{marker}<span lang="grc" class="surface">{_text(token.surface)}</span>'
            f'<span class="visually-hidden">{accessible}</span>{label}</a>'
        )
    result = f"<h3>{_text(page.verse.key)}</h3><div class=\"scripture\">" + "".join(tokens) + "</div>"
    if page.selected_token is not None:
        result += _token_details(page.selected_token)
    else:
        result += "<p>Select a token to inspect its facts.</p>"
    result += "<h3>Source clauses</h3>"
    result += "".join(_node(n) for n in page.verse.source_nodes if n.cat == "CL")
    result += "<details><summary>Other ancestor nodes</summary>"
    result += "".join(_node(n) for n in page.verse.source_nodes if n.cat != "CL") + "</details>"
    return result


def _candidate_details(candidate: ProductCandidate, page: ProductPage) -> str:
    result = _rows((("Scope source node", candidate.scope_source_node_id),))
    result += "<h4>Evidence</h4><ul>"
    by_id = {n.key: n for n in page.projection.evidence_nodes}
    for role, kind, source_id in candidate.evidence:
        result += f"<li>{_text(role)} / {_text(kind)} / {_text(source_id)}"
        if source_id in by_id:
            result += _node(by_id[source_id])
        result += "</li>"
    result += "</ul>"
    payload = candidate.payload
    if isinstance(payload, ProductAppositionPayload):
        result += _rows((("Anchor source node", payload.anchor_source_node_id),))
        result += "<h4>Ordered child source nodes</h4>" + _refs(payload.child_source_node_ids)
    else:
        result += (f"<p>Source rule: {_text(payload.source_rule)}</p>"
                   f"<p>Derived structural candidate: {_text(payload.source_rule)}</p>")
        result += _rows((("Anchor source node", payload.anchor_source_node_id),
                         ("Source Head", payload.source_head_raw)))
        for component in payload.components:
            result += '<div class="component">' + _rows((
                ("Structural component", component.component_role),
                ("Source node", component.source_node_id), ("Source Cat", component.source_cat),
                ("Sibling ordinal", component.sibling_ordinal),
            )) + _refs(component.member_token_refs) + "</div>"
    result += _rows((("Source family", candidate.source_snapshot.source_family),
                     ("Edition", candidate.source_snapshot.edition)))
    return result


def _candidates(page: ProductPage) -> str:
    panel = page.projection
    if panel.state == ProjectionState.NOT_CONFIGURED:
        return f"<p>{wording.NOT_CONFIGURED}</p>"
    if panel.error is not None:
        return _error(panel.error)
    if page.verse is None:
        return "<p>Load a source verse to discover persisted candidates.</p>"
    if not panel.candidates:
        return f"<p>{wording.NO_CANDIDATES}</p>"
    result = _error(panel.candidate_error)
    for candidate in panel.candidates:
        selected = page.selected_candidate is not None and candidate.key == page.selected_candidate.key
        result += (f'<article class="candidate-card{" selected-card" if selected else ""}" '
                   f'data-candidate="{_text(candidate.key)}">'
                   f'<p class="badge">{wording.CANDIDATE_BADGE}</p>')
        if page.selection is not None:
            result += (f'<h3><a href="{_url(replace(page.selection, candidate_id=candidate.key, evaluation_id=None))}">'
                       f'{_text(candidate.candidate_kind)} / {_text(candidate.derivation_kind)} / '
                       f'{_text(candidate.derivation_version)}</a></h3>')
        result += f"<p>Candidate status: {_text(candidate.status)}</p>"
        result += "<h4>Exact member refs</h4>" + _refs(candidate.member_token_refs)
        if not candidate.is_evaluated:
            result += f"<p>{wording.NOT_EVALUATED}</p>"
        if selected:
            result += _candidate_details(candidate, page)
        result += "</article>"
    return result


def _evaluation(evaluation: ProductEvaluation, page: ProductPage) -> str:
    selected = page.selection is not None and page.selection.evaluation_id == evaluation.key
    result = (f'<article class="evaluation-card{" selected-card" if selected else ""}" '
              f'data-evaluation="{_text(evaluation.key)}">'
              f'<p class="badge">{wording.EVALUATION_BADGE}</p>')
    if page.selection is not None:
        result += (f'<a href="{_url(replace(page.selection, candidate_id=evaluation.candidate_id, evaluation_id=evaluation.key))}">'
                   'Inspect this evaluation</a>')
    result += (f'<p>Evaluation: {_text(evaluation.disposition)} under '
               f'{_text(evaluation.protocol_id)}/{_text(evaluation.protocol_version)} by '
               f'{_human(evaluation.evaluator_label)}</p>')
    result += _rows((("Evaluator class", evaluation.evaluator_class),
                     ("Protocol", evaluation.protocol_id), ("Protocol version", evaluation.protocol_version),
                     ("Evaluation disposition", evaluation.disposition)))
    result += "<h4>Rationale evidence</h4><ul>" + "".join(
        f"<li>{_text(kind)}: {_text(citation)}</li>" for kind, citation in evaluation.rationale_evidence
    ) + "</ul>"
    language = evaluation.rationale_note_language
    lang = f' lang="{_text(language)}"' if re.fullmatch(r"[A-Za-z0-9-]{1,35}", language) else ""
    result += (f'<p>Rationale language: {_text(language)}</p>'
               f'<div class="rationale-note"{lang}>{_human(evaluation.rationale_note_text)}</div>')
    result += _rows((("Supersedes", evaluation.supersedes),))
    if evaluation.not_superseded:
        result += f"<p>{wording.NOT_SUPERSEDED}</p>"
    for successor in evaluation.superseded_by:
        result += f"<p>Superseded by {_text(successor)}</p>"
    return result + "</article>"


def _history(page: ProductPage) -> str:
    result = f"<p>{wording.ORDER_NOTE}</p>"
    if page.projection.error is not None and page.projection.state != ProjectionState.NOT_CONFIGURED:
        return result + "<p>Evaluation history unavailable.</p>"
    if page.selected_history is None:
        return result + "<p>Select a persisted candidate to inspect human evaluations.</p>"
    if not page.selected_history.evaluations:
        return result + f"<p>{wording.NOT_EVALUATED}</p>"
    result += "".join(_evaluation(e, page) for e in page.selected_history.evaluations)
    result += "<h3>Supersession edges</h3><ul>" + "".join(
        f"<li>{_text(predecessor)} &rarr; {_text(successor)}</li>"
        for predecessor, successor in page.selected_history.edges
    ) + "</ul>"
    return result


def _diagnostics(page: ProductPage) -> str:
    result = '<details class="diagnostics"><summary>Diagnostics</summary>' + _rows((
        ("Source file", page.status.source_file_name),
        ("Structural interpretation file", page.status.projection_file_name),
    ))
    for candidate in page.projection.candidates:
        result += _rows((("candidate_id", candidate.key),))
        result += "<h3>source_snapshot</h3>" + _rows(tuple(
            (f.name, getattr(candidate.source_snapshot, f.name)) for f in fields(candidate.source_snapshot)
        ))
    for history in page.projection.histories:
        for evaluation in history.evaluations:
            result += _rows((("evaluation_id", evaluation.key),
                             ("candidate_id", evaluation.candidate_id)))
    return result + "</details>"


def render_page(page: ProductPage) -> str:
    selection = page.selection
    chapter = "" if selection is None else str(selection.chapter)
    verse = "" if selection is None else str(selection.verse)
    sections = (
        ("source", "Source", "source_fact", wording.SOURCE_BADGE, _source(page)),
        ("candidates", "Derived structural candidates", "derived_structural_candidate",
         wording.CANDIDATE_BADGE, _candidates(page)),
        ("evaluations", "Human evaluation history", "human_evaluation",
         wording.EVALUATION_BADGE, _history(page)),
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{wording.TITLE}</title><link rel="stylesheet" href="/static/explorer.css">'
        f'</head><body><header><h1>{wording.TITLE}</h1>'
        f'<p>Source: {_text(page.status.source_status.value)} | Structural interpretation store: '
        f'{_text(page.status.projection_state.value)}</p>'
        f'{_error(page.status.error)}</header><nav aria-label="Scripture selection">'
        '<form method="get" action="/verse"><span>Matthew</span>'
        f'<label for="chapter">Chapter</label><input id="chapter" name="chapter" inputmode="numeric" value="{_text(chapter) if chapter else ""}" required>'
        f'<label for="verse">Verse</label><input id="verse" name="verse" inputmode="numeric" value="{_text(verse) if verse else ""}" required>'
        '<button type="submit">Go / Load</button></form></nav><main>'
        + "".join(_error(n) for n in page.notices)
        + "".join(
            f'<section aria-labelledby="{name}-heading" data-epistemic="{epistemic}">'
            f'<h2 id="{name}-heading">{title}</h2><p class="badge">{badge}</p>{body}</section>'
            for name, title, epistemic, badge, body in sections
        )
        + _diagnostics(page) + "</main></body></html>"
    )
