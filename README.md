# pr-ship

Create and merge GitHub Pull Requests from the terminal in one command.

## Installation

### macOS (Apple Silicon and Intel)

Install and authenticate the GitHub CLI if needed:

```bash
brew install gh
gh auth login
```

Then install pr-ship with the Bash included in macOS:

```bash
git clone https://github.com/gabsdk/pr-ship.git
cd pr-ship
bash install.sh
```

On macOS, the default prefix is `~/.local`; no sudo is required. If
`~/.local/bin` is not already in your PATH, add this to `~/.zshrc` (or
`~/.bash_profile` when using Bash), then open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Linux: Via PPA (apt-get)

```bash
sudo add-apt-repository ppa:gabsdk/pr-ship
sudo apt-get update
sudo apt-get install pr-ship
```

### Linux: Quick install (from source)

```bash
git clone https://github.com/gabsdk/pr-ship.git
cd pr-ship
sudo bash install.sh
```

### Linux: Debian package (.deb)

```bash
git clone https://github.com/gabsdk/pr-ship.git
cd pr-ship
bash build-deb.sh
sudo dpkg -i build/pr-ship_1.0.3.deb
```

### Custom prefix (macOS and Linux)

The Linux default prefix is `/usr`. Both platforms support a custom prefix
for installation without root privileges:

```bash
PREFIX="$HOME/.local" bash install.sh
```

### Makefile (macOS and Linux)

On macOS:

```bash
make install
```

On Linux:

```bash
sudo make install
```

You can override the default with `make install PREFIX="$HOME/.local"`.
`DESTDIR` is supported for package staging.

## Prerequisites

- **bash** >= 3.2 (the version included in macOS is supported)
- **git**
- **[gh](https://cli.github.com)** (GitHub CLI) — installed and authenticated (`gh auth login`)

## Setup

After installing, run the interactive setup:

```bash
pr-ship --setup
```

This will ask you:

1. **Language** — auto-detects your system language (falls back to English)
2. **Default GitHub owner** — your username or org (e.g. `gabsdk`)
3. **Default head branch** — source branch (default: `development`)
4. **Default base branch** — target branch (default: `sandbox`)
5. **Default PR title** — optional custom title
6. **Default PR body** — optional custom body

Config is saved at `~/.config/pr-ship/config`.

## Usage

```bash
pr-ship <repo> [head] [base] [--title "..."] [--body "..."]
```

### Examples

```bash
# Uses configured owner, default branches
pr-ship my-repo

# Custom branches
pr-ship my-repo feature/login main

# Full owner/repo
pr-ship gabsdk/my-repo development sandbox

# Custom title and body
pr-ship my-repo --title "Release v2.0" --body "Production release"
```

### Flags

| Flag | Description |
|---|---|
| `--setup` | Run interactive setup |
| `--title "..."` | Custom PR title |
| `--body "..."` | Custom PR body |
| `--help` | Show help |
| `--version` | Show version |

## Languages

pr-ship auto-detects your system language. Supported:

- **en** — English
- **pt_BR** — Português (Brasil)
- **es** — Español
- **fr** — Français
- **de** — Deutsch
- **it** — Italiano

To add a new language, create a file at `<prefix>/share/pr-ship/lang/<locale>.sh`
following the existing format, or add it to `lib/pr-ship/lang/` before installing.

## Publishing to PPA

To distribute via `sudo apt-get install pr-ship`:

1. Create a [Launchpad](https://launchpad.net) account
2. Create a PPA at `https://launchpad.net/~YOUR_USER/+activate-archive`
3. Set up GPG key and upload it to Ubuntu keyserver
4. Build the source package:

```bash
export DEBEMAIL="your@email.com"
export DEBFULLNAME="Your Name"
debuild -S -sa
```

5. Upload to your PPA:

```bash
dput ppa:YOUR_USER/pr-ship ../pr-ship_1.0.2-1_source.changes
```

Users can then install with:

```bash
sudo add-apt-repository ppa:YOUR_USER/pr-ship
sudo apt-get update
sudo apt-get install pr-ship
```

## Uninstall

On macOS:

```bash
bash uninstall.sh
# or
make uninstall
```

On Linux:

```bash
# If installed via install.sh or make
sudo bash uninstall.sh
# or
sudo make uninstall

# If installed via .deb
sudo apt-get remove pr-ship
```

For a custom prefix, use the same `PREFIX` value when uninstalling:

```bash
PREFIX="$HOME/.local" bash uninstall.sh
```

Configuration is kept unless you confirm its removal or pass `--purge`.

## Development

Run the regression suite with Python 3 (only needed for development):

```bash
make test
```

## License

[MIT](LICENSE)
