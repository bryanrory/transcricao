# 🎙️ transcricao

Transcreve vídeos e áudios **no seu próprio computador**, de graça e offline, usando o [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (uma versão otimizada do Whisper, da OpenAI).

Aceita **arquivos**, **pastas inteiras** e **links** (YouTube e [outros sites suportados pelo yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)), e gera a transcrição em **JSON**, **SRT**, **VTT** ou **TXT**.

---

## Sumário
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso rápido](#uso-rápido)
- [Opções](#opções)
- [Exemplos](#exemplos)
- [Formatos de saída](#formatos-de-saída)
- [Modelos](#modelos)
- [Onde os arquivos são salvos](#onde-os-arquivos-são-salvos)
- [Usando a GPU (opcional)](#usando-a-gpu-opcional)
- [Problemas comuns](#problemas-comuns)
- [Como funciona](#como-funciona)

---

## Requisitos
- **Windows** (testado no Windows 11). Também deve funcionar em Linux/macOS, trocando os caminhos do `venv`.
- **Python 3.10 ou mais novo** (testado no 3.14).
- Conexão com a internet **só** na primeira vez (para baixar o modelo) e para transcrever links.

> Não precisa instalar o ffmpeg: a biblioteca de áudio (PyAV) já vem com ele embutido.

## Instalação
```powershell
git clone https://github.com/bryanrory/transcricao.git
cd transcricao
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Uso rápido

### Arrastar e soltar
Arraste um vídeo, áudio ou pasta em cima do **`transcrever.bat`**. A transcrição (`.json`) é salva ao lado do vídeo.

> Dica: crie um atalho do `transcrever.bat` na Área de Trabalho e arraste os vídeos direto nele.

### Pelo terminal
```powershell
.\.venv\Scripts\python.exe transcrever.py <arquivo|pasta|link> [mais entradas...] [opções]
```
O `transcrever.bat` aceita os mesmos argumentos:
```powershell
.\transcrever.bat "C:\Videos\aula.mp4" -f srt
```

## Opções
| Opção | Descrição | Padrão |
|---|---|---|
| `-f`, `--formato` | Formato de saída: `json`, `srt`, `vtt` ou `txt` | `json` |
| `-i`, `--idioma` | Idioma do áudio (`pt`, `en`, `es`...) | detecta sozinho |
| `-m`, `--modelo` | Modelo do Whisper (veja [Modelos](#modelos)) | `small` |
| `-o`, `--saida` | Pasta onde salvar as transcrições | ao lado do vídeo |
| `--gpu` | Tenta usar a placa de vídeo NVIDIA | desligado |
| `-h`, `--help` | Mostra a ajuda | |

## Exemplos
```powershell
# Um vídeo → JSON
.\.venv\Scripts\python.exe transcrever.py "C:\Videos\aula.mp4"

# Legenda SRT em português
.\.venv\Scripts\python.exe transcrever.py "C:\Videos\aula.mp4" -f srt -i pt

# Link do YouTube
.\.venv\Scripts\python.exe transcrever.py "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# Pasta inteira → texto puro, salvando em outra pasta
.\.venv\Scripts\python.exe transcrever.py "C:\Videos" -f txt -o "C:\Transcricoes"

# Vários de uma vez (arquivos, pastas e links misturados)
.\.venv\Scripts\python.exe transcrever.py video1.mp4 "C:\Podcasts" "https://youtu.be/..." -f vtt

# Mais precisão (mais lento)
.\.venv\Scripts\python.exe transcrever.py entrevista.mp3 -m medium -i pt
```

Enquanto roda, cada trecho aparece na tela com o tempo e o progresso:
```
🧠 Carregando modelo 'small' na CPU...

🎬 aula.mp4
   idioma: pt (98%) · duração: 12:34
   [00:00 → 00:06]   0.8%  Bom dia, pessoal, hoje a gente vai falar sobre...
   ...
✅ Salvo: C:\Videos\aula.json

Resumo: 1 ok, 0 com erro.
```

Se um arquivo der erro, os outros continuam sendo processados. No fim aparece um resumo. Para interromper, use `Ctrl+C`.

## Formatos de saída

### JSON (padrão)
Ideal para processar depois (em outro script, planilha, IA etc.).
```json
{
  "arquivo": "aula.mp4",
  "idioma": "pt",
  "duracao": 754.2,
  "segmentos": [
    { "inicio": 0.0, "fim": 6.48, "texto": "Bom dia, pessoal, hoje a gente vai falar sobre..." }
  ],
  "texto": "Bom dia, pessoal, hoje a gente vai falar sobre... (texto completo)"
}
```
Os tempos (`inicio` e `fim`) estão em segundos.

### SRT
Legenda padrão, abre no VLC, no YouTube e em editores de vídeo. Para o VLC carregar sozinho, deixe o `.srt` com o mesmo nome do vídeo e na mesma pasta (que é o padrão).
```
1
00:00:00,000 --> 00:00:06,480
Bom dia, pessoal, hoje a gente vai falar sobre...
```

### VTT
Legenda para páginas web (tag `<track>` do HTML5).
```
WEBVTT

00:00:00.000 --> 00:00:06.480
Bom dia, pessoal, hoje a gente vai falar sobre...
```

### TXT
Só o texto, um trecho por linha.

## Modelos
Quanto maior o modelo, mais preciso e mais lento. Ele é baixado automaticamente na primeira vez em que é usado (fica em `%USERPROFILE%\.cache\huggingface\hub`).

| Modelo | Tamanho aprox. | Quando usar |
|---|---|---|
| `tiny` | 75 MB | testes rápidos; erra bastante |
| `base` | 145 MB | rascunhos |
| `small` | 480 MB | **padrão**: bom equilíbrio |
| `medium` | 1,5 GB | áudio difícil, sotaques, termos técnicos |
| `large-v3` | 3 GB | máxima precisão; bem lento na CPU |
| `turbo` | 1,6 GB | quase a precisão do `large-v3`, mais rápido que ele |

Dicas:
- Passar o idioma (`-i pt`) evita detecção errada no começo do áudio e acelera um pouco.
- Trechos de silêncio são pulados automaticamente (filtro VAD), o que economiza tempo e evita "alucinações" em partes sem fala.

## Onde os arquivos são salvos
| Entrada | Transcrição salva em |
|---|---|
| Arquivo ou pasta | mesma pasta do vídeo, com o mesmo nome (`aula.mp4` → `aula.json`) |
| Link | `saida\` dentro da pasta do projeto |
| Qualquer uma com `-o PASTA` | na `PASTA` informada |

O áudio baixado de links fica em `_downloads\` (pode apagar quando quiser).

> ⚠️ Se já existir uma transcrição com o mesmo nome e formato, ela é **sobrescrita**.

## Usando a GPU (opcional)
Com `--gpu`, o script tenta usar uma placa NVIDIA. Se não conseguir, **volta sozinho para a CPU** e avisa, então nada quebra.

Para a GPU funcionar de verdade, são necessárias as bibliotecas do CUDA 12 (cuBLAS e cuDNN 9):
```powershell
.\.venv\Scripts\python.exe -m pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```
Depois disso, as pastas `bin` desses pacotes (em `.venv\Lib\site-packages\nvidia\*\bin`) precisam estar no `PATH`.

> Em placas antigas ou com pouca memória (ex.: GTX 960M com 2 GB, que só aceita `float32`), a CPU com `int8` costuma ser tão rápida quanto a GPU. Vale mais a pena em placas com 4 GB ou mais.

## Problemas comuns
| Erro / sintoma | Solução |
|---|---|
| `open() got an unexpected keyword argument 'metadata_errors'` | PyAV novo demais. Rode `pip install -r requirements.txt` de novo (ele fixa `av<17`). |
| `Library cublas64_12.dll is not found` | Faltam as bibliotecas do CUDA: veja [Usando a GPU](#usando-a-gpu-opcional). Sem elas o script segue na CPU. |
| Transcrição no idioma errado | Informe o idioma com `-i pt`. |
| Muito lento | Use um modelo menor (`-m base` ou `-m tiny`). |
| Texto com muitos erros | Use um modelo maior (`-m medium`) e informe o idioma. |
| Link não baixa | Atualize o yt-dlp: `.\.venv\Scripts\python.exe -m pip install -U yt-dlp`. |
| Acentos estranhos no `.bat` | O `.bat` já força UTF-8 (`chcp 65001`). Se persistir, use o Windows Terminal. |

## Como funciona
1. **Entradas**: cada argumento pode ser um arquivo, uma pasta (pega todos os vídeos/áudios dela, sem subpastas) ou um link.
2. **Links**: o `yt-dlp` baixa só o áudio (mais rápido e leve que o vídeo).
3. **Transcrição**: o `faster-whisper` carrega o modelo uma vez e transcreve cada arquivo, pulando os silêncios.
4. **Saída**: os trechos com tempo são gravados no formato escolhido, em UTF-8.

Extensões aceitas em pastas: `mp4 mkv avi mov webm flv wmv m4v ts mp3 wav m4a aac ogg opus flac wma`. Arquivos passados diretamente podem ter qualquer formato que o ffmpeg entenda.

### Estrutura do projeto
```
transcricao/
├── transcrever.py     # o script
├── transcrever.bat    # atalho para Windows (arrastar e soltar)
├── requirements.txt   # dependências
└── README.md
```
