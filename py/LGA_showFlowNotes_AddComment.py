import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = r"C:/Portable/LGA/PipeSync/cache/pipesync.db"


def _toolpack_py_dir():
    return Path(__file__).resolve().parent


def _ensure_shotgun_api_path():
    shotgun_api_path = _toolpack_py_dir() / "shotgun_api3"
    path_text = str(shotgun_api_path)
    if shotgun_api_path.exists() and path_text not in sys.path:
        sys.path.insert(0, path_text)


def _ensure_secure_reader_path():
    nuke_dir = Path(__file__).resolve().parents[2]
    shared_dir = nuke_dir / "Python" / "Startup" / "LGA_NKS_Shared"
    for path in (shared_dir.parent, shared_dir):
        path_text = str(path)
        if path.exists() and path_text not in sys.path:
            sys.path.insert(0, path_text)


def read_secure_config():
    _ensure_secure_reader_path()
    from SecureConfig_Reader import read_secure_config as _read_secure_config

    return _read_secure_config()


def get_flow_credentials():
    _ensure_secure_reader_path()
    from SecureConfig_Reader import get_flow_credentials as _get_flow_credentials

    return _get_flow_credentials()


def get_special_roles_from_secure_config():
    config = read_secure_config() or {}
    flow_config = config.get("Flow", {}) if isinstance(config, dict) else {}
    raw_roles = flow_config.get("SpecialRoles", "")
    if isinstance(raw_roles, str):
        return [role.strip() for role in raw_roles.split(",") if role.strip()]
    if isinstance(raw_roles, (list, tuple)):
        return [str(role).strip() for role in raw_roles if str(role).strip()]
    return []


def is_current_user_reviewer():
    return "Reviewer" in get_special_roles_from_secure_config()


def get_current_user(db_path=DB_PATH):
    values = {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT setting_key, setting_value
            FROM app_settings
            WHERE setting_key IN ('user_id', 'user_login', 'user_name')
            """
        )
        for row in cur.fetchall():
            values[row["setting_key"]] = row["setting_value"]

    user_id_raw = values.get("user_id", "")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        user_id = None

    return {
        "user_id": user_id,
        "user_login": values.get("user_login", ""),
        "user_name": values.get("user_name", ""),
    }


def _connect_to_flow():
    _ensure_shotgun_api_path()
    import shotgun_api3

    flow_url, flow_login, flow_password = get_flow_credentials()
    if not flow_url or not flow_login or not flow_password:
        raise RuntimeError("No se pudieron leer las credenciales de Flow desde config.secure.")
    return shotgun_api3.Shotgun(flow_url, login=flow_login, password=flow_password)


def add_comment_to_flow(
    project_id,
    version_sg_id,
    user_id,
    content,
    attachment_paths=None,
    progress_callback=None,
):
    attachment_paths = attachment_paths or []
    content = (content or "").strip()
    if not content:
        raise ValueError("El comentario esta vacio.")
    if not project_id or not version_sg_id or not user_id:
        raise ValueError("Faltan ids requeridos para crear la nota en Flow.")

    def progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    progress(5, "Conectando con Flow...")
    sg = _connect_to_flow()

    progress(20, "Creando nota...")
    note_data = {
        "project": {"type": "Project", "id": int(project_id)},
        "content": content,
        "user": {"type": "HumanUser", "id": int(user_id)},
        "note_links": [{"type": "Version", "id": int(version_sg_id)}],
    }
    result = sg.create("Note", note_data)
    note_id = result.get("id") if result else None
    if not note_id:
        raise RuntimeError("Flow no devolvio un id valido para la nota.")

    valid_paths = [path for path in attachment_paths if path and os.path.exists(path)]
    total = len(valid_paths)
    for index, path in enumerate(valid_paths, start=1):
        progress(
            25 + int((index - 1) * 70 / max(total, 1)),
            f"Subiendo adjunto {index}/{total}...",
        )
        sg.upload("Note", note_id, path)

    progress(100, "Nota enviada.")
    return int(note_id)


def insert_local_comment(
    db_path,
    version_db_id,
    version_sg_id,
    note_sg_id,
    content,
    author_name,
    attachment_paths=None,
    created_on=None,
):
    attachment_paths = attachment_paths or []
    created_on = created_on or datetime.now(timezone.utc).astimezone().isoformat(
        sep=" ", timespec="seconds"
    )
    clean_paths = [path for path in attachment_paths if path]
    attachment_info = [
        {
            "id": 0,
            "name": os.path.basename(path),
            "frame": None,
            "url": "",
        }
        for path in clean_paths
    ]
    note_links = [{"type": "Version", "id": int(version_sg_id)}]

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO version_notes
              (version_id, note_sg_id, content, created_by, created_on, from_playlist,
               playlist_name, note_links, attachment_info, local_attachment_paths)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(version_db_id),
                int(note_sg_id),
                content,
                author_name or "",
                created_on,
                0,
                "",
                json.dumps(note_links, separators=(",", ":")),
                json.dumps(attachment_info, separators=(",", ":")),
                ";".join(clean_paths),
            ),
        )
        conn.commit()


def submit_comment(
    db_path,
    project_id,
    version_db_id,
    version_sg_id,
    content,
    attachment_paths=None,
    progress_callback=None,
):
    user = get_current_user(db_path)
    user_id = user.get("user_id")
    if not user_id:
        raise RuntimeError("No se encontro user_id en app_settings de PipeSync.")

    note_id = add_comment_to_flow(
        project_id,
        version_sg_id,
        user_id,
        content,
        attachment_paths=attachment_paths or [],
        progress_callback=progress_callback,
    )
    author = user.get("user_name") or user.get("user_login") or ""
    insert_local_comment(
        db_path,
        version_db_id,
        version_sg_id,
        note_id,
        content,
        author,
        attachment_paths=attachment_paths or [],
    )
    return note_id
