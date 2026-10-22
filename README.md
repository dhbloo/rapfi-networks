# Rapfi's Networks Repo

This repository holds the latest network files for [Rapfi](https://github.com/dhbloo/rapfi) gomoku/renju engine. All weight files are released freely under the [CC0](https://creativecommons.org/share-your-work/public-domain/cc0/) license.

### Usage

To use the config with the weights, put the latest classical weight file and NNUE weight files, as well as `config.toml` to the directory containing the engine executable.

An example of the config file with latest weights is available in the config-example directory.

The latest Classical model is `classical/model260809.bin`, with its matching configuration at
`config-example/gomocalc-classical260809.toml`. It was trained and validated for freestyle f15 and
f20, standard 15, and renju 15.

All retained Classical binaries use the current v8 four-table policy format. The older-named
210901 and 220723 models retain their original base tables and scales, with zero policy residuals.
Use these files with the matching engine revision; historical formats remain in Git history.
