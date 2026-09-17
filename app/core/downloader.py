"""Download dos componentes na primeira execução (com barra de progresso).

Busca a versão mais recente dos pacotes de cursor direto das releases do GitHub
e instala em %APPDATA%/CustomMF/cursors. Roda em thread e conversa com a UI por
uma fila de eventos.
"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import requests

from . import cursors, paths

API = "https://api.github.com/repos/{repo}/releases/latest"
HEADERS = {"User-Agent": "CustomMF/1.0 (+personalizador de windows)"}


class SkipDownload(Exception):
    pass


def resolve_asset(repo: str, prefer: str) -> tuple[str, int]:
    """URL + tamanho do asset 'windows .zip' mais recente da release."""
    r = requests.get(API.format(repo=repo), headers=HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    assets = data.get("assets", [])
    prefer_l = (prefer or "").lower()
    chosen = None
    for a in assets:
        if a.get("name", "").lower() == prefer_l:
            chosen = a
            break
    if chosen is None:
        for a in assets:
            n = a.get("name", "").lower()
            if prefer_l and prefer_l.replace("-windows", "") in n and n.endswith(".zip"):
                chosen = a
                break
    if chosen is None:
        for a in assets:
            n = a.get("name", "").lower()
            if "windows" in n and n.endswith(".zip"):
                chosen = a
                break
    if chosen is None:
        raise RuntimeError(f"Nenhum pacote Windows encontrado em {repo}")
    return chosen["browser_download_url"], int(chosen.get("size", 0)), chosen["name"]


def download_file(url: str, dest: Path, progress=None, skip_flag: threading.Event | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers=HEADERS, stream=True, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0)) or 1
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(64 * 1024):
                if skip_flag is not None and skip_flag.is_set():
                    raise SkipDownload()
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(min(1.0, done / total), done, total)
    return dest


class Downloader(threading.Thread):
    """Baixa a lista de tarefas e emite eventos numa queue:

    ("item", idx, título) | ("item_state", idx, "done"/"err"/"skip", msg)
    ("progress", fração_total, detalhe) | ("done", n_erros)
    """

    def __init__(self, tasks: list[dict], q: queue.Queue, skip_flag: threading.Event | None = None):
        super().__init__(daemon=True)
        self.tasks = tasks
        self.q = q
        self.skip_flag = skip_flag or threading.Event()
        total_weight = sum(t.get("weight", 1) for t in tasks) or 1
        self._weights = [t.get("weight", 1) / total_weight for t in tasks]

    def _report(self, frac_in_task: float, detail: str) -> None:
        frac = min(1.0, sum(self._weights[:self._idx]) + self._weights[self._idx] * frac_in_task)
        self.q.put(("progress", frac, detail))

    def run(self) -> None:
        errors = 0
        tmp = paths.temp_dir()
        tmp.mkdir(parents=True, exist_ok=True)
        self._idx = 0
        for i, task in enumerate(self.tasks):
            self._idx = i
            title = task["title"]
            self.q.put(("item", i, title))
            if self.skip_flag.is_set():
                self.q.put(("item_state", i, "skip", "pulado"))
                continue
            zpath = tmp / (task["key"] + ".zip")
            try:
                url, size, name = resolve_asset(task["repo"], task["asset"])

                def cb(frac, done, total, _t=title):
                    mb_d, mb_t = done / 1e6, total / 1e6
                    self._report(frac, f"{_t} — {mb_d:.1f} / {mb_t:.1f} MB")

                download_file(url, zpath, cb, self.skip_flag)
                self._report(0.98, f"Instalando {title}…")
                names = cursors.install_from_zip(zpath, paths.packs_root())
                try:
                    zpath.unlink(missing_ok=True)
                except Exception:
                    pass
                self.q.put(("item_state", i, "done", ", ".join(names) or title))
            except SkipDownload:
                self.q.put(("item_state", i, "skip", "pulado"))
            except Exception as e:
                errors += 1
                self.q.put(("item_state", i, "err", str(e)[:120]))
        self.q.put(("progress", 1.0, "Tudo pronto!"))
        self.q.put(("done", errors))


DEFAULT_TASKS = [
    {**t, "weight": 40 if t["key"] == "macos" else 30}
    for t in cursors.KNOWN_DOWNLOADS
    if t["key"] in ("macos", "bibata-ice", "bibata-amber")
]
