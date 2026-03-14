from __future__ import annotations

import re
import shutil
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


DOCX_PATH = Path("/Users/leg4/.nuke/LGA_ToolPack/DocToMD/LGA_ToolPack.docx")
OUTPUT_MD = Path("/Users/leg4/.nuke/LGA_ToolPack/DocToMD/README.md")
MEDIA_ORIGINAL = Path("/Users/leg4/.nuke/LGA_ToolPack/DocToMD/media_original")
MEDIA_CONVERTED = Path("/Users/leg4/.nuke/LGA_ToolPack/DocToMD/media_converted")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

TITLE_RE = re.compile(r"v\d", re.IGNORECASE)
URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_section_heading(text: str) -> bool:
    if not text:
        return False
    if TITLE_RE.search(text):
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return upper_ratio > 0.65 and len(text.split()) <= 5


def is_tool_heading(text: str) -> bool:
    return bool(text and TITLE_RE.search(text))


def normalize_shortcut_lines(text: str) -> str:
    replacements = {
        "Ctrl + Alt + CCopy with inputs": "Ctrl + Alt + C: Copy with inputs",
        "Ctrl + Alt + VPaste with inputs": "Ctrl + Alt + V: Paste with inputs",
        "Ctrl + Alt + KDuplicate with inputs": "Ctrl + Alt + K: Duplicate with inputs",
        "Shift + HAbre la GUI": "Shift + H: Abre la GUI",
    }
    return replacements.get(text, text)


def image_markdown(target: str) -> str:
    return f"![]({target})"


def read_docx():
    with ZipFile(DOCX_PATH) as docx:
        document = ET.fromstring(docx.read("word/document.xml"))
        rels = ET.fromstring(docx.read("word/_rels/document.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"].replace("\\", "/")
            for rel in rels
            if rel.attrib.get("Target", "").startswith("media/")
        }
        body = document.find("w:body", NS)
        return docx, body, rel_map


def prepare_media():
    if MEDIA_ORIGINAL.exists():
        shutil.rmtree(MEDIA_ORIGINAL)
    if MEDIA_CONVERTED.exists():
        shutil.rmtree(MEDIA_CONVERTED)
    MEDIA_ORIGINAL.mkdir(parents=True, exist_ok=True)
    MEDIA_CONVERTED.mkdir(parents=True, exist_ok=True)

    with ZipFile(DOCX_PATH) as docx:
        for name in docx.namelist():
            if not name.startswith("word/media/"):
                continue
            filename = Path(name).name
            data = docx.read(name)
            (MEDIA_ORIGINAL / filename).write_bytes(data)
            (MEDIA_CONVERTED / filename).write_bytes(data)


def paragraph_text(paragraph: ET.Element) -> str:
    parts = []
    for child in paragraph.iter():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "t" and child.text:
            parts.append(child.text)
        elif tag in {"tab", "br"}:
            parts.append("\n")
    return clean_text("".join(parts))


def paragraph_images(paragraph: ET.Element, rel_map: dict[str, str]) -> list[str]:
    images = []
    for blip in paragraph.findall(".//a:blip", NS):
        embed = blip.attrib.get(f"{{{NS['r']}}}embed")
        target = rel_map.get(embed)
        if target:
            images.append(target)
    return images


def table_text(table: ET.Element) -> str:
    parts = []
    for cell in table.findall(".//w:t", NS):
        if cell.text:
            parts.append(cell.text)
    return clean_text("".join(parts))


def main():
    prepare_media()

    with ZipFile(DOCX_PATH) as docx:
        document = ET.fromstring(docx.read("word/document.xml"))
        rels = ET.fromstring(docx.read("word/_rels/document.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"].replace("\\", "/")
            for rel in rels
            if rel.attrib.get("Target", "").startswith("media/")
        }
        body = document.find("w:body", NS)

        lines: list[str] = []
        pending_images: list[str] = []
        title_seen = False

        for child in body:
            tag = child.tag.rsplit("}", 1)[-1]

            if tag == "tbl":
                code = table_text(child)
                if code:
                    lines.extend(["```python", code, "```", ""])
                continue

            if tag != "p":
                continue

            text = normalize_shortcut_lines(paragraph_text(child))
            images = paragraph_images(child, rel_map)
            converted_images = [f"media_converted/{Path(img).name}" for img in images]

            if converted_images and not text:
                if title_seen and converted_images == ["media_converted/image1.png"]:
                    continue
                pending_images.extend(converted_images)
                continue

            if not title_seen and text == "LGA TOOL PACK":
                title_seen = True
                if pending_images:
                    lines.append(image_markdown(pending_images[0]))
                    lines.append("")
                    pending_images.clear()
                elif converted_images:
                    lines.append(image_markdown(converted_images[0]))
                    lines.append("")
                lines.append(f"# {text}")
                lines.append("")
                continue

            if text == "Lega | v2.44":
                lines.append(text)
                lines.append("")
                continue

            if is_section_heading(text):
                if pending_images:
                    for image in pending_images:
                        lines.append(image_markdown(image))
                        lines.append("")
                    pending_images.clear()
                lines.append(f"## {text}")
                lines.append("")
                continue

            if is_tool_heading(text):
                if pending_images:
                    for image in pending_images:
                        lines.append(image_markdown(image))
                        lines.append("")
                    pending_images.clear()
                lines.append(f"### {text}")
                lines.append("")
                continue

            if URL_RE.match(text):
                lines.append(f"[{text}]({text})")
                lines.append("")
                continue

            if text in {"Instalación:", "Funciones:", "Opciones disponibles en los Settings:", "Modo de uso:", "Shortcuts:", "Shortcut:"}:
                if pending_images:
                    for image in pending_images:
                        lines.append(image_markdown(image))
                        lines.append("")
                    pending_images.clear()
                lines.append(f"**{text.rstrip(':')}**")
                lines.append("")
                continue

            if text.startswith(("Copiar la carpeta ", "Con un editor de texto", "El ToolPack permite ", "Go to read:", "Explorer:", "Relink:", "Delete:", "Copy to:", "Shot folder depth:", "Reproduce un sonido", "Calcula la duración", "Envía un email", "Ctrl + *", "Ctrl + shift + *", "Ctrl + /", "Ctrl + shift + /", "Ctrl + Alt + C:", "Ctrl + Alt + V:", "Ctrl + Alt + K:", "Shift + H:", "Click ", "Shift+Click ", "Ctrl+Click ", "Alt ")):
                lines.append(f"- {text}")
                continue

            if pending_images:
                for image in pending_images:
                    lines.append(image_markdown(image))
                    lines.append("")
                pending_images.clear()

            if converted_images:
                extra_images = converted_images[:]
            else:
                extra_images = []

            lines.append(text)
            lines.append("")

            for image in extra_images:
                lines.append(image_markdown(image))
                lines.append("")

        if pending_images:
            for image in pending_images:
                lines.append(image_markdown(image))
                lines.append("")

    OUTPUT_MD.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
