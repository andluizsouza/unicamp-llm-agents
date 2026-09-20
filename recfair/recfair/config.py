"""Application configuration and path helpers."""

from __future__ import annotations

import getpass
import os
import re
from pathlib import Path

CURRENT_ARCH = "multiagent"
ARCHITECTURE_DATES = {
    "baseline": "2026-09-07",
    "workflow": "2026-09-13",
    "multiagent": "2026-09-19",
}

# Legacy global (E2). Each graph module exposes its own ``prompt_version()``.
PROMPT_VERSION = "v2"
TEMPERATURE = 0
N_RECOMMEND = 5
HANDOFF_PHONE = "0800-000-0000"
OUT_OF_CONTEXT_TEXT = (
    "Eu sou um assistente virtual de O Boticário e estou aqui para te ajudar "
    "na sua próxima compra. Qual produto ou marca você procura? "
    "Posso te dar algumas dicas."
)
DEFAULT_MODEL = "gemini-3.5-flash-lite"
THINKING_LEVEL = "minimal"

USD_PER_1M_INPUT_TOKENS = 0.30
USD_PER_1M_OUTPUT_TOKENS = 2.50


def app_root() -> Path:
    """Return the app root (directory with ``requirements.txt`` or ``pyproject.toml``)."""
    here = Path(__file__).resolve().parent
    markers = ("requirements.txt", "pyproject.toml")
    for parent in [here, *here.parents]:
        if any((parent / marker).is_file() for marker in markers):
            return parent
    return here.parents[1]


def data_dir() -> Path:
    """Path to ``data/`` at app root."""
    return app_root() / "data"


def golden_cases_path() -> Path:
    """Frozen golden-set JSON."""
    return data_dir() / "golden" / "cases.json"


def eval_runs_dir() -> Path:
    """Directory for eval run JSON artifacts."""
    return app_root() / "eval" / "runs"


def resolve_arch(arch: str | None) -> str:
    """Map ``current`` to the vigente architecture id."""
    if arch is None or arch == "current":
        return CURRENT_ARCH
    return arch


def model_version() -> str:
    """LLM model id from env or default."""
    return os.environ.get("RECFAIR_MODEL_VERSION", DEFAULT_MODEL)


_FIXED_SAMPLING_MODELS = frozenset({"gemini-3.5-flash-lite", "gemini-3.6-flash"})


def normalize_model_name(model: str) -> str:
    """Match langchain_google_genai naming for fixed-sampling models."""
    name = model.lower().rsplit("/", 1)[-1]
    return re.sub(r"-\d{3}$", "", name)


def sampling_fixed_by_model(model: str) -> bool:
    """Whether provider fixes sampling params for this model."""
    return normalize_model_name(model) in _FIXED_SAMPLING_MODELS


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse ``KEY=VALUE`` lines; strip quotes; skip comments and blanks."""
    parsed: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key:
            parsed[key] = val
    return parsed


def apply_dotenv() -> None:
    """Load KEY=VALUE from nearby ``.env`` files without overriding existing env."""
    seen: set[Path] = set()
    for root in [Path.cwd(), *list(Path.cwd().parents)[:5], app_root()]:
        path = root / ".env"
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for key, val in parse_dotenv(path.read_text(encoding="utf-8")).items():
            if key not in os.environ:
                os.environ[key] = val


def export_hf_token() -> str | None:
    """Export ``HF_TOKEN`` for Hugging Face Hub (and alias ``HUGGING_FACE_HUB_TOKEN``).

    Loads ``.env`` via :func:`apply_dotenv` if the process does not already have
    the variable. Never logs or returns the secret.

    Returns:
        Source label (``HF_TOKEN`` or ``HUGGING_FACE_HUB_TOKEN``), or ``None``
        if neither is set.
    """
    apply_dotenv()
    token = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or "").strip()
    if not token:
        return None
    source = "HF_TOKEN" if (os.environ.get("HF_TOKEN") or "").strip() else "HUGGING_FACE_HUB_TOKEN"
    os.environ["HF_TOKEN"] = token
    os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", token)
    return source


def hf_token() -> str | None:
    """Return the Hugging Face token after exporting aliases, or ``None``."""
    export_hf_token()
    token = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or "").strip()
    return token or None


def huggingface_token_kwargs() -> dict[str, str]:
    """Kwargs for ``SentenceTransformer`` / ``HuggingFaceEmbeddings.model_kwargs``."""
    token = hf_token()
    return {"token": token} if token else {}


def ensure_google_api_key() -> str:
    """Resolve GOOGLE_API_KEY via env or prompt. Returns source label (never the key)."""
    if os.environ.get("GOOGLE_API_KEY"):
        return "GOOGLE_API_KEY"
    if os.environ.get("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
        return "GEMINI_API_KEY"
    try:
        from google.colab import userdata  # type: ignore

        for secret_name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            try:
                value = userdata.get(secret_name)
            except Exception:
                continue
            if value:
                os.environ["GOOGLE_API_KEY"] = value
                return f"colab:{secret_name}"
    except ImportError:
        pass
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("GOOGLE_API_KEY: ")
    return "manual"
