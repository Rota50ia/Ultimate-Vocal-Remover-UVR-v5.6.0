# Referência técnica: UVR para voz falada e pandeiro

## Por que usar um adaptador

O Ultimate Vocal Remover original é uma aplicação gráfica com modelos de separação. Para uma skill, um processo de linha de comando é mais previsível: recebe um arquivo, escreve as saídas em um diretório e registra o modelo utilizado.

O pacote `audio-separator` oferece uma CLI e usa modelos do ecossistema UVR, incluindo arquiteturas MDX-Net, VR e Demucs. O adaptador desta skill chama essa CLI e não controla a interface gráfica.

## Modelo inicial

Começar com:

```text
model_bs_roformer_ep_317_sdr_12.9755.ckpt
```

Trocar o modelo quando houver:

- vazamento forte do pandeiro na voz;
- consoantes removidas;
- som metálico ou aquático;
- falhas nos finais das palavras.

Não escolher um modelo apenas pelo nome. Comparar um trecho curto da mesma aula e ouvir a fala, não apenas a música residual.

## Saídas e nomenclatura

- `voz_isolada_raw.wav`: resultado vocal direto do separador;
- `voz_para_elevenlabs.wav`: cópia mono PCM 16-bit a 16 kHz para fala;
- `acompanhamento_residual.wav`: saída não vocal estimada;
- `separacao_manifest.json`: rastreabilidade da execução.

O acompanhamento residual pode conter pandeiro, ambiência, reverberação e vazamento de voz. Evitar apresentá-lo como uma track original ou como pandeiro perfeitamente isolado.

## Instalação

Instalar o adaptador dentro de um ambiente virtual do projeto quando possível:

```bash
python3.10 -m venv .venv-audio
source .venv-audio/bin/activate
python -m pip install "audio-separator[cpu]"
```

O `audio-separator` atual exige Python 3.10 ou superior. Confirmar a versão antes de criar o ambiente.

Instalar FFmpeg separadamente e verificar:

```bash
audio-separator --version
ffmpeg -version
```

O primeiro uso de um modelo pode fazer download dos pesos. Usar `--model-file-dir` para controlar o cache e evitar downloads repetidos.

## Teste mínimo

```bash
python3 scripts/separate_audio.py \
  "entrada/trecho-30s.wav" \
  --output-dir "saida/teste-uvr" \
  --dry-run
```

Depois de confirmar o comando:

```bash
python3 scripts/separate_audio.py \
  "entrada/trecho-30s.wav" \
  --output-dir "saida/teste-uvr"
```

## Critério de aprovação para tradução

Considerar o resultado aprovado quando:

1. o professor puder ser compreendido sem consultar o vídeo;
2. as palavras curtas e consoantes estiverem preservadas;
3. o pandeiro não dominar as pausas da fala;
4. a transcrição gerar frases completas;
5. os artefatos não alterarem nomes, números ou instruções musicais.

Quando falhar, comparar outro modelo ou aplicar uma segunda etapa de isolamento de fala. Não enviar automaticamente uma saída com palavras omitidas para tradução.

## Licença e atribuição

O projeto UVR é distribuído sob MIT. Manter a atribuição ao Ultimate Vocal Remover e aos desenvolvedores nos materiais técnicos da ferramenta. Verificar também a licença e as condições do pacote `audio-separator` antes de distribuir uma aplicação comercial.
