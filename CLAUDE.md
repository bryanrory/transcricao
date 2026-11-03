# transcricao

Script Python que transcreve vídeos/áudios **localmente** com [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Aceita arquivos, pastas e links (YouTube etc., via yt-dlp).

## Arquivos
- `transcrever.py` — CLI única (entradas → download se URL → transcrição → escritor do formato).
- `transcrever.bat` — atalho que usa o `.venv`; dá pra arrastar vídeos/pastas em cima.
- `requirements.txt` — `faster-whisper`, `yt-dlp`, `av>=16,<17`.
- Gerados (no `.gitignore`): `.venv/`, `_downloads/` (áudios baixados de links), `saida/` (transcrições de links).

## Uso
```powershell
.\.venv\Scripts\python.exe transcrever.py <arquivo|pasta|url> [...] [opções]
```
- `-f/--formato json|srt|vtt|txt` — padrão **json** (`arquivo`, `idioma`, `duracao`, `segmentos[{inicio,fim,texto}]`, `texto`).
- `-m/--modelo` — padrão `small`. Opções: `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`. Baixados do Hugging Face na 1ª vez para `~\.cache\huggingface\hub`.
- `-i/--idioma pt` — sem isso, detecta automaticamente.
- `-o/--saida DIR` — padrão: ao lado do arquivo de entrada; links vão para `saida/`.
- `--gpu` — tenta CUDA; se falhar, cai para CPU sozinho.

## Setup
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
Funciona no Python 3.14. Não precisa de ffmpeg no PATH (PyAV embute; yt-dlp baixa o áudio sem converter).

## Testar
```powershell
.\.venv\Scripts\python.exe transcrever.py "https://www.youtube.com/watch?v=jNQXAC9IVRw" -m tiny
.\.venv\Scripts\python.exe transcrever.py _downloads -m tiny -f srt
```

## Pegadinhas
- **PyAV fixado em `<17`**: faster-whisper 1.2.1 chama `av.open(metadata_errors=...)`, que não existe no PyAV 17+ (erro `unexpected keyword argument 'metadata_errors'`). Ao atualizar o faster-whisper, testar se dá pra soltar.
- **GPU (GTX 960M, Maxwell)**: só suporta `float32` (sem int8/float16) → `compute_type="auto"`. Além disso faltam as DLLs do CUDA 12 (`cublas64_12.dll`, cuDNN 9) — o erro só aparece na hora de transcrever, por isso o fallback para CPU fica no laço de transcrição. Para habilitar: `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` e pôr as pastas `bin` desses pacotes no PATH. Com 2 GB de VRAM, CPU int8 costuma ser tão bom quanto; não é prioridade.
- CPU (i7-6700HQ) com `int8`: `small` é o equilíbrio; `medium`/`large-v3` ficam bem lentos em vídeos longos.
- Aviso de symlink do Hugging Face é silenciado no script (Windows sem modo desenvolvedor).

## Git
Repo local com `user.email=bryanrory13@gmail.com` / `user.name=bryanrory` configurados **no repo** (a máquina tem também a conta `rorysystems` no `gh` e no SSH `github-rory` — não usar aqui).
