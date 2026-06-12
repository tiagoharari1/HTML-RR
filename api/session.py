"""
Gestión de sesiones en disco para la API FastAPI.

Cada sesión es un UUID con una carpeta en el directorio temporal del sistema.
Los DataFrames se serializan como Parquet; la config como JSON.
"""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path

import pandas as pd

_SESSION_BASE = Path(tempfile.gettempdir()) / "rrai_sessions"


def _session_dir(session_id: str) -> Path:
    return _SESSION_BASE / session_id


def create_session() -> str:
    sid = str(uuid.uuid4())
    _session_dir(sid).mkdir(parents=True, exist_ok=True)
    return sid


def ensure_session(session_id: str) -> None:
    """Crea la carpeta de la sesión si no existe."""
    _session_dir(session_id).mkdir(parents=True, exist_ok=True)


def session_exists(session_id: str) -> bool:
    return _session_dir(session_id).exists()


def save_df(session_id: str, name: str, df: pd.DataFrame) -> None:
    path = _session_dir(session_id) / f"{name}.parquet"
    df.to_parquet(path, index=False)


def load_df(session_id: str, name: str) -> pd.DataFrame:
    path = _session_dir(session_id) / f"{name}.parquet"
    return pd.read_parquet(path)


def df_exists(session_id: str, name: str) -> bool:
    return (_session_dir(session_id) / f"{name}.parquet").exists()


def save_config(session_id: str, config: dict) -> None:
    path = _session_dir(session_id) / "config.json"
    path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")


def load_config(session_id: str) -> dict:
    path = _session_dir(session_id) / "config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def config_exists(session_id: str) -> bool:
    return (_session_dir(session_id) / "config.json").exists()


def save_json(session_id: str, name: str, data: object) -> None:
    """Guarda datos arbitrarios como JSON en la carpeta de sesión."""
    path = _session_dir(session_id) / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_json(session_id: str, name: str) -> object:
    path = _session_dir(session_id) / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
