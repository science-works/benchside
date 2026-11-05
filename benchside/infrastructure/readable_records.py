"""Private, rebuildable ODT/Markdown views of the complete saved project journal."""

import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.model.ids import user_project_id
from benchside.infrastructure.files import atomic_json

ODT_TYPE = "application/vnd.oasis.opendocument.text"
NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "manifest": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def tag(prefix, name):
    return f"{{{NS[prefix]}}}{name}"


def xml(node):
    return ET.tostring(node, encoding="utf-8", xml_declaration=True)


def _text(element, value):
    # ODF requires explicit elements for repeated spaces, tabs and line breaks.
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", "�", str(value))
    tail = None
    for part in re.split(r"( {2,}|\t|\n)", value):
        if part == "\n":
            tail = ET.SubElement(element, tag("text", "line-break"))
        elif part == "\t":
            tail = ET.SubElement(element, tag("text", "tab"))
        elif len(part) > 1 and not part.strip():
            tail = ET.SubElement(element, tag("text", "s"), {tag("text", "c"): str(len(part))})
        elif tail is None:
            element.text = (element.text or "") + part
        else:
            tail.tail = (tail.tail or "") + part


def odt_bytes(blocks):
    root = ET.Element(tag("office", "document-content"), {tag("office", "version"): "1.2"})
    body = ET.SubElement(ET.SubElement(root, tag("office", "body")), tag("office", "text"))
    for level, text in blocks:
        attributes = {tag("text", "outline-level"): str(level)} if level else {}
        _text(ET.SubElement(body, tag("text", "h" if level else "p"), attributes), text)
    styles = ET.Element(tag("office", "document-styles"), {tag("office", "version"): "1.2"})
    defaults = ET.SubElement(ET.SubElement(styles, tag("office", "styles")), tag("style", "default-style"), {tag("style", "family"): "paragraph"})
    ET.SubElement(defaults, tag("style", "paragraph-properties"), {tag("fo", "margin-bottom"): "0.12in"})
    ET.SubElement(defaults, tag("style", "text-properties"), {tag("fo", "font-size"): "11pt", tag("fo", "font-family"): "Liberation Sans"})
    manifest = ET.Element(tag("manifest", "manifest"), {tag("manifest", "version"): "1.2"})
    for path, media in [("/", ODT_TYPE), ("content.xml", "text/xml"), ("styles.xml", "text/xml")]:
        ET.SubElement(manifest, tag("manifest", "file-entry"), {tag("manifest", "full-path"): path, tag("manifest", "media-type"): media})
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", ODT_TYPE, compress_type=zipfile.ZIP_STORED)
        archive.writestr("content.xml", xml(root))
        archive.writestr("styles.xml", xml(styles))
        archive.writestr("META-INF/manifest.xml", xml(manifest))
    return output.getvalue()


def _atomic_bytes(path, data):
    if path.is_symlink():
        raise ValidationError("Readable record destination must not be a symlink")
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".benchside-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _fields(value, prefix=""):
    for key, item in value.items():
        if item is None:
            continue
        label = (prefix + " / " if prefix else "") + key.replace("_", " ").capitalize()
        if isinstance(item, dict):
            yield from _fields(item, label)
        elif isinstance(item, list):
            for index, child in enumerate(item, 1):
                if isinstance(child, dict):
                    yield from _fields(child, f"{label} {index}")
                else:
                    yield f"{label}: {child}"
        else:
            yield f"{label}: {item}"


def export_project(paths, journal, project_id):
    project_id = user_project_id(project_id)
    if paths.store_root is None:
        raise ValidationError("Readable file export needs durable local storage; use the cloud host's document export instead")
    from benchside.domain.consultation.query.recall_project import describe_target
    from benchside.infrastructure.journal.projection import JournalProjectRepository

    config = paths.home / "app-projects" / f"{project_id.root}.json"
    project = JournalProjectRepository(journal).get(project_id)
    if project is None and not config.exists():
        raise ValidationError("Project not found")
    title = json.loads(config.read_text()).get("title") if config.exists() else None
    title = title or project_id.root
    index_path = paths.home / "readable-index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    if not isinstance(index, dict):
        raise ValidationError("Invalid readable project index; preserve the journal and rebuild this index")
    label = re.sub(r'[^\w .()-]+', ' ', title, flags=re.UNICODE).strip(' .')[:80] or "Research project"
    label = label.encode("utf-8")[:180].decode("utf-8", errors="ignore").rstrip(" .")
    suffix = hashlib.sha256(project_id.root.encode()).hexdigest()[:10]
    folder_name = f"{label} — {suffix}"
    previous_name = index.get(project_id.root, folder_name)
    if not isinstance(previous_name, str) or Path(previous_name).name != previous_name or previous_name in {".", ".."}:
        raise ValidationError("Invalid readable project folder; rebuild the private readable index")
    root = paths.store_root.resolve()
    folder = root / "researcher" / "projects" / folder_name
    previous = folder.parent / previous_name
    if any((directory / ".git").exists() for destination in (folder, previous)
           for directory in (destination, *destination.parents)):
        raise ValidationError("Readable research records must also stay outside Git")
    # Do not follow a human-created symlink into a public/other directory.
    if any(p.is_symlink() for p in (root / "researcher", root / "researcher/projects", folder, previous)):
        raise ValidationError("Readable record folders must not be symlinks")
    if previous != folder and previous.exists():
        if folder.exists():
            raise ValidationError("Both old and new readable project folders exist; resolve the conflict before renaming")
        previous.rename(folder)
    index[project_id.root] = folder_name
    atomic_json(index_path, index)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    for directory in (root / "researcher", root / "researcher/projects", folder):
        os.chmod(directory, 0o700)
    events = list(journal.read_envelopes(project_id))
    blocks = [
        (1, title),
        (0, "Private Benchside research record"),
        (0, f"Updated {datetime.now(UTC).isoformat(timespec='seconds')} · {len(events)} saved events"),
        (0, "This is a generated reading copy of the complete saved project record. Edits here are not imported into Benchside. Ask your agent to record corrections; these files are refreshed from the private journal. Nothing is sent to Science Works by creating this copy."),
        (1, "Where things stand"),
    ]
    if project:
        current = project.current_hypothesis
        if current:
            blocks.append((0, "Current hypothesis: " + current.statement))
        blocks.append((2, "Unresolved research questions"))
        questions = [q.question for q in project.questions if q.answer is None]
        blocks.extend((0, q) for q in questions)
        if not questions:
            blocks.append((0, "None recorded."))
        blocks.append((2, "Open critiques"))
        critiques = [describe_target(c.target) for c in project.critiques if c.is_open]
        blocks.extend((0, c) for c in critiques)
        if not critiques:
            blocks.append((0, "None recorded."))
        blocks.append((2, "Current decisions"))
        superseded = {d.supersedes for d in project.decisions if d.supersedes}
        for decision in project.decisions:
            if decision.id not in superseded:
                blocks.extend([(0, decision.decision), (0, "Reason: " + decision.rationale)])
    else:
        blocks.append((0, "No scientific records yet."))
    blocks.append((1, "Complete saved history"))
    for number, event in enumerate(events, 1):
        data = dict(event.get("data", {}))
        recorded = data.pop("recorded_at", "Date not recorded")
        kind = re.sub(r"(?<!^)(?=[A-Z])", " ", event.get("type", "Record"))
        blocks.append((2, f"{number}. {kind} — {recorded}"))
        blocks.extend((0, text) for text in _fields(data))
    if not events:
        blocks.append((0, "Nothing recorded yet."))
    markdown = "\n\n".join(("#" * level + " " + text) if level else "\n".join("> " + line for line in str(text).splitlines()) for level, text in blocks) + "\n"
    odt = folder / "Research record.odt"
    md = folder / "Research record.md"
    _atomic_bytes(odt, odt_bytes(blocks))
    _atomic_bytes(md, markdown.encode())
    return {"odt": str(odt), "markdown": str(md), "events": len(events), "generated_view": True}
