"""Transcrição de vídeo/áudio com faster-whisper (local, offline).

Uso:
    python transcrever.py <arquivo|pasta|url> [...] [--formato json|srt|vtt|txt]
                          [--modelo small] [--idioma pt] [--gpu] [--saida DIR]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
EXTENSOES = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".ts",
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wma",
}

# Windows sem modo desenvolvedor não tem symlink; o cache do HF funciona igual, só avisa
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Windows: garante UTF-8 no console
for fluxo in (sys.stdout, sys.stderr):
    try:
        fluxo.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------- tempo ----------
def _hms(seg: float, sep: str) -> str:
    ms = int(round(seg * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def _curto(seg: float) -> str:
    m, s = divmod(int(seg), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ---------- escritores ----------
def escrever_json(dados, destino: Path):
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def escrever_srt(dados, destino: Path):
    blocos = [
        f"{i}\n{_hms(s['inicio'], ',')} --> {_hms(s['fim'], ',')}\n{s['texto']}\n"
        for i, s in enumerate(dados["segmentos"], 1)
    ]
    destino.write_text("\n".join(blocos), encoding="utf-8")


def escrever_vtt(dados, destino: Path):
    blocos = ["WEBVTT\n"] + [
        f"{_hms(s['inicio'], '.')} --> {_hms(s['fim'], '.')}\n{s['texto']}\n"
        for s in dados["segmentos"]
    ]
    destino.write_text("\n".join(blocos), encoding="utf-8")


def escrever_txt(dados, destino: Path):
    destino.write_text("\n".join(s["texto"] for s in dados["segmentos"]) + "\n", encoding="utf-8")


ESCRITORES = {"json": escrever_json, "srt": escrever_srt, "vtt": escrever_vtt, "txt": escrever_txt}


# ---------- entradas ----------
def baixar_url(url: str) -> Path:
    import yt_dlp

    pasta = RAIZ / "_downloads"
    pasta.mkdir(exist_ok=True)
    opcoes = {
        "format": "bestaudio/best",
        "outtmpl": str(pasta / "%(title).150B [%(id)s].%(ext)s"),
        "restrictfilenames": False,
        "windowsfilenames": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    print(f"⬇  Baixando áudio: {url}")
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)
        caminho = Path(ydl.prepare_filename(info))
    if not caminho.exists():  # extensão pode mudar no download
        candidatos = sorted(pasta.glob(caminho.stem + ".*"))
        if not candidatos:
            raise FileNotFoundError(f"download não encontrado: {caminho}")
        caminho = candidatos[0]
    return caminho


def expandir_entradas(entradas):
    """Retorna lista de (caminho_ou_url, eh_url)."""
    itens = []
    for e in entradas:
        if re.match(r"^https?://", e, re.I):
            itens.append((e, True))
            continue
        p = Path(e)
        if p.is_dir():
            achados = sorted(f for f in p.iterdir() if f.suffix.lower() in EXTENSOES)
            if not achados:
                print(f"⚠  Nenhum vídeo/áudio em {p}")
            itens += [(str(f), False) for f in achados]
        elif p.is_file():
            itens.append((str(p), False))
        else:
            print(f"⚠  Não encontrado: {e}")
    return itens


# ---------- modelo ----------
def carregar_modelo(nome: str, gpu: bool):
    from faster_whisper import WhisperModel

    if gpu:
        try:
            print(f"🧠 Carregando modelo '{nome}' na GPU...")
            # GTX 960M (Maxwell) só suporta float32; "auto" escolhe o melhor tipo da placa
            return WhisperModel(nome, device="cuda", compute_type="auto"), True
        except Exception as erro:
            print(f"⚠  GPU indisponível ({erro}). Usando CPU.")
    print(f"🧠 Carregando modelo '{nome}' na CPU...")
    return WhisperModel(nome, device="cpu", compute_type="int8"), False


def transcrever(modelo, arquivo: Path, idioma):
    segmentos, info = modelo.transcribe(str(arquivo), language=idioma, vad_filter=True, beam_size=5)
    print(f"   idioma: {info.language} ({info.language_probability:.0%}) · duração: {_curto(info.duration)}")
    lista = []
    for s in segmentos:  # a transcrição acontece aqui (gerador)
        texto = s.text.strip()
        pct = (s.end / info.duration * 100) if info.duration else 0
        print(f"   [{_curto(s.start)} → {_curto(s.end)}] {pct:5.1f}%  {texto}")
        lista.append({"inicio": round(s.start, 3), "fim": round(s.end, 3), "texto": texto})
    return {
        "arquivo": arquivo.name,
        "idioma": info.language,
        "duracao": round(info.duration, 3),
        "segmentos": lista,
        "texto": " ".join(s["texto"] for s in lista),
    }


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Transcreve vídeos/áudios (arquivos, pastas ou links) com faster-whisper.")
    ap.add_argument("entradas", nargs="+", help="arquivo(s), pasta(s) ou URL(s)")
    ap.add_argument("-f", "--formato", choices=ESCRITORES, default="json", help="formato de saída (padrão: json)")
    ap.add_argument("-m", "--modelo", default="small",
                    help="tiny, base, small, medium, large-v3, turbo... (padrão: small)")
    ap.add_argument("-i", "--idioma", default=None, help="código do idioma, ex.: pt, en (padrão: detecta)")
    ap.add_argument("--gpu", action="store_true", help="tenta usar a GPU NVIDIA (CUDA)")
    ap.add_argument("-o", "--saida", default=None,
                    help="pasta de saída (padrão: junto do arquivo; links vão para ./saida)")
    args = ap.parse_args()

    itens = expandir_entradas(args.entradas)
    if not itens:
        sys.exit("Nada para transcrever.")

    modelo, na_gpu = carregar_modelo(args.modelo, args.gpu)
    ok, falhas = [], []

    for alvo, eh_url in itens:
        try:
            arquivo = baixar_url(alvo) if eh_url else Path(alvo)
            print(f"\n🎬 {arquivo.name}")
            try:
                dados = transcrever(modelo, arquivo, args.idioma)
            except RuntimeError as erro:
                if not na_gpu:
                    raise
                # erros de CUDA (ex.: DLL do cuBLAS/cuDNN ausente) só aparecem na hora de transcrever
                print(f"⚠  Falha na GPU ({erro}). Repetindo na CPU...")
                modelo, na_gpu = carregar_modelo(args.modelo, False)
                dados = transcrever(modelo, arquivo, args.idioma)

            if args.saida:
                pasta = Path(args.saida)
            elif eh_url:
                pasta = RAIZ / "saida"
            else:
                pasta = arquivo.parent
            pasta.mkdir(parents=True, exist_ok=True)
            destino = pasta / f"{arquivo.stem}.{args.formato}"
            ESCRITORES[args.formato](dados, destino)
            print(f"✅ Salvo: {destino}")
            ok.append(destino)
        except KeyboardInterrupt:
            print("\nInterrompido.")
            break
        except Exception as erro:
            print(f"❌ Erro em {alvo}: {erro}")
            falhas.append(alvo)

    print(f"\nResumo: {len(ok)} ok, {len(falhas)} com erro.")
    for f in falhas:
        print(f"   ❌ {f}")
    sys.exit(1 if falhas and not ok else 0)


if __name__ == "__main__":
    main()
