# Backup — Ultimate Vocal Remover UVR v5.6.0

Backup rastreável da instalação local do Ultimate Vocal Remover usada para
separar voz falada de pandeiro e outros instrumentos.

Repositório remoto: <https://github.com/Rota50ia/Ultimate-Vocal-Remover-UVR-v5.6.0.>

## Registro da instalação

- Aplicativo: Ultimate Vocal Remover v5.6.0 para macOS Intel x86_64.
- Modelo usado na separação registrada: `UVR-MDX-NET Inst HQ 3`.
- Saída preparada para transcrição e tradução: `voz_para_elevenlabs.wav`.
- Manifesto sanitizado: `records/separacao-manifest.json`.
- Hashes dos artefatos locais: `checksums.sha256`.

## Conteúdo versionado

- `scripts/separate_audio.py`: adaptador de linha de comando baseado em `audio-separator`.
- `docs/uvr-workflow.md`: fluxo e critérios para avaliar a separação.
- `records/separacao-manifest.json`: registro da execução que gerou a voz isolada.
- `checksums.sha256`: comprovação dos arquivos locais preservados.

## Artefatos grandes

Os instaladores `.dmg` não foram incluídos no Git comum porque têm 561 MB e
1,3 GB, acima do limite de 100 MB por arquivo do GitHub. Eles permanecem no
computador local e são identificados pelos hashes em `checksums.sha256`.

Para armazená-los remotamente no futuro, use Git LFS ou uma GitHub Release.

## Aviso sobre a separação

A separação por IA é uma estimativa. `acompanhamento_residual.wav` não deve ser
tratado como uma faixa de pandeiro perfeitamente isolada; ele pode conter
vazamento de voz, ambiência e outros instrumentos.
