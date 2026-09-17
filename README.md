# Custom MF 🖱️✨

**Personalizador de Windows com cara de app moderno.** Troque o cursor do mouse
(macOS, Bibata, BreezeX ou **uma imagem sua**), adicione **efeitos de clique** e
**trilhas animadas**, mude a **fonte do sistema** do Windows 10/11 e use
**pacotes de ícones** na interface — tudo com tema escuro/claro e cores
totalmente personalizáveis.

![plataforma](https://img.shields.io/badge/plataforma-Windows%2010%20%7C%2011-blue)
![build](https://github.com/neresbielxx2-ai/CustomMF/actions/workflows/build.yml/badge.svg)

---

## ⬇️ Como baixar o .exe

1. Vá na aba **[Actions](../../actions)** deste repositório
2. Abra o workflow **“Build CustomMF.exe”**
3. Baixe o artefato **`CustomMF-Windows`** (contém o `CustomMF.exe`)
4. Quando houver uma tag `v1.0.0`, o .exe também sai na aba
   **[Releases](../../releases)** automaticamente

> O .exe é **portable** (não precisa instalar): só executar. Na primeira abertura
> ele mostra uma animação de boas-vindas e **baixa os componentes com uma barra
> de progresso** (“Baixando componentes, aguarde…”).

### O Windows reclamou do arquivo?
É porque o executável não tem assinatura digital (evita pagar certificado 💸).
Clique em **“Mais informações” → “Executar assim mesmo”**.

---

## ✨ Funcionalidades

| Recurso | Detalhes |
|---|---|
| 🖱️ **Pacotes de cursor** | **macOS** (branco e escuro, iguais aos do Mac), **Bibata Modern** (Ice/Amber) e **BreezeX** (Dark/Black/Light) — baixados direto das releases oficiais do [ful1e5](https://github.com/ful1e5) |
| 🖼️ **Sua imagem como cursor** | Escolha qualquer PNG/JPG/GIF/BMP/ICO, ajuste o tamanho e clique na prévia para definir a ponta (hotspot) |
| ✨ **Efeitos de clique** | Onda, Pulso, Faíscas, Estrelas, Corações, Flash e Fogos — com cor, tamanho e duração ajustáveis (e modo arco-íris 🌈) |
| 🌈 **Trilhas animadas** | Neon, Arco-íris, Bolhas, Estrelas, Corações, Fogo e Pó de estrela — densidade e velocidade configuráveis |
| 🔤 **Fonte do Windows** | Troque a Segoe UI por qualquer fonte instalada (Windows 10 e 11) e **instale fontes .ttf/.otf** com 1 clique |
| 🎨 **Pacotes de ícones** | 4 pacotes integrados + importe o seu (.zip com PNGs nomeados) |
| 🌗 **Temas** | Escuro (3 tons de fundo), **Claro** (3 tons) e Sistema — com **cor de destaque e cor dos botões personalizáveis** |
| ↩️ **Segurança** | Seus cursores são salvos (backup) antes de cada troca; botão para voltar ao padrão do Windows a qualquer momento |
| 🧪 **Autoteste** | `python run.py --selftest` valida núcleo e interface antes de cada build |

> ℹ️ Os efeitos de clique e as trilhas funcionam **enquanto o Custom MF estiver
> aberto** — e **nunca atrapalham**: cliques, scroll e arrastos passam direto
> através das animações (overlay 100% click-through).
> A troca de cursor e a fonte **fixam no sistema** — a fonte aparece por completo
> após sair da sessão do Windows.

---

## 🛠️ Compilar você mesmo

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean CustomMF.spec
# → dist/CustomMF.exe
```

Ou apenas faça push — o **GitHub Actions** compila sozinho (veja
`.github/workflows/build.yml`).

### Rodar direto do código (dev)

```bash
pip install -r requirements.txt
python run.py
python run.py --selftest --no-ui   # testes rápidos, sem abrir janela
```

---

## 📁 Estrutura

```
app/
├── main.py            # aplicação principal (janela, animação de abertura)
├── selftest.py        # autotestes (núcleo + UI)
├── core/              # lógica sem dependência de UI
│   ├── cursors.py     # pacotes, INF parser, registro, backup
│   ├── curio.py       # leitura/escrita de .cur/.ico (sem dependências)
│   ├── fonts.py       # fonte do sistema + instalação .ttf
│   ├── particles.py   # motor de partículas (cliques e trilhas)
│   ├── effects.py     # overlay transparente em tela cheia
│   ├── downloader.py  # download dos pacotes (GitHub releases)
│   ├── iconpacks.py   # pacotes de ícones da interface
│   ├── theme.py       # motor de temas (escuro/claro/accent)
│   ├── config.py      # configuração persistente
│   ├── winapi.py      # ctypes: registro, SPI, UAC, etc.
│   └── paths.py       # caminhos (%APPDATA%/CustomMF)
└── ui/
    ├── main_window.py # sidebar + navegação
    ├── splash.py      # abertura animada + barra de download
    ├── widgets.py     # cartões, sliders, seletor de cor…
    └── pages/         # Início, Mouse, Clique, Trilhas, Fonte, Ícones, Config
```

---

## 💜 Créditos

- Cursores **macOS / Bibata / BreezeX** — [ful1e5](https://github.com/ful1e5)
  (licença Apache 2.0 / MIT — veja os repositórios respectivos)
- Feito com Python + CustomTkinter
