# Bootstrap DEV-VM — Tools + Dokus (erster Tag)

**Ziel:** Nach Ubuntu-Installation sofort arbeitsfähig: Obsidian, Cursor, Antigravity, AI-OS-v2-Dokus → danach Phase-0-Infra.  
**VM:** `ai-os-dev` · Ubuntu 26.04 Desktop · NCE First-Party Company Brain (`DEFAULT_TENANT=nextchapter`).

---

## 0. Nach dem ersten Login (Ubuntu)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget ca-certificates gnupg \
  build-essential flatpak gnome-software-plugin-flatpak \
  openssh-server
sudo systemctl enable --now ssh

# Docker (Compose v2 inklusive)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# danach neu einloggen (oder: newgrp docker)

mkdir -p ~/Projekte ~/Transfers /opt/ai-os/ingest/inbox
sudo chown -R "$USER:$USER" /opt/ai-os
```

IP der VM notieren (vom Host aus SSH):

```bash
ip -4 -br a
```

Netzwerk: Wenn SSH vom Host nicht geht → in virt-manager Portweiterleitung `host 2222 → guest 22` oder Netzmodus **Bridge**.

---

## 1. Dokus in die VM (AI-OS v2)

**Pfad in der VM (empfohlen):**

```text
~/Projekte/1100-AI-OS-V2/     # Arbeitskopie + Obsidian-Vault-Root
# optional:
# sudo ln -sfn ~/Projekte/1100-AI-OS-V2 /opt/ai-os/repo
```

### Variante A — vom Host per Sync-Skript (bevorzugt)

Auf dem **Tuxedo-Host** (VM läuft, SSH erreichbar). Repo-Root = wo `ROADMAP.md` liegt:

```bash
export VM=peter@192.168.122.XX   # IP der VM

cd /path/to/1100-AI-OS-V2
./appliance/sync-docs-to-vm.sh "$VM" --with-installers
```

Manuell:

```bash
rsync -av --progress --exclude '.git/' \
  /path/to/1100-AI-OS-V2/ \
  "$VM:~/Projekte/1100-AI-OS-V2/"
```

### Variante B — Spice/virt-manager Ordnerfreigabe

Host-Ordner `…/1100-AI-OS-V2` als Shared Folder → in der VM nach `~/Projekte/` kopieren.

### Variante C — Git (sobald Remote existiert)

```bash
git clone <ai-os-v2-remote> ~/Projekte/1100-AI-OS-V2
```

**Einstieg lesen:** `README.md` → `docs/11-PLATFORM-VM.md` → `docs/12-LEITPRINZIPIEN.md` → `ROADMAP.md` Kap. 5.

---

## 2. Cursor

Bevorzugt **`.deb`** (AppImage nur Fallback, siehe Roadmap §19).

```bash
# Host → VM (oder --with-installers am Sync-Skript):
scp ~/Downloads/cursor_*_amd64.deb "$VM:~/Transfers/"

# VM:
sudo apt install -y ~/Transfers/cursor_*_amd64.deb
# oder neuestes Deb aus ~/Downloads/
```

Workspace: `~/Projekte/1100-AI-OS-V2`.

---

## 3. Antigravity

```bash
# Host → VM (oder Sync --with-installers)
scp ~/Downloads/Antigravity*.tar.gz "$VM:~/Transfers/"

# VM:
cd ~
tar -xzf ~/Transfers/Antigravity*.tar.gz
# typisch: ~/Antigravity-x64/antigravity
chmod +x ~/Antigravity-x64/antigravity
# optional: ~/.local/share/applications/antigravity.desktop
```

**Inbox für späteres Capture:**

```bash
sudo mkdir -p /opt/ai-os/ingest/inbox
sudo chown -R "$USER:$USER" /opt/ai-os
```

---

## 4. Obsidian

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub md.obsidian.Obsidian
flatpak run md.obsidian.Obsidian
```

**Vault:** `~/Projekte/1100-AI-OS-V2`  
(Markdown unter `docs/` + `ROADMAP.md` / `README.md` im Root.)

---

## 5. Phase-0-Infra (nach Tools)

```bash
cd ~/Projekte/1100-AI-OS-V2
cp -n .env.example .env
# OLLAMA_HOST auf LAN-Ollama setzen (kein Ollama-Secret).
# Secrets nur für Postgres/LangFuse; OpenRouter-Key erst bei balanced/premium.

docker compose -f deploy/infra.yml -f deploy/monitoring.yml --env-file .env up -d
curl -sf http://localhost:3000/api/public/health   # LangFuse
```

Tenant-Default: `DEFAULT_TENANT=nextchapter` (NCE First-Party auf dieser VM).

---

## 6. Checkliste „loslegen“

| # | Erledigt? | Schritt |
|---|-----------|---------|
| 1 | ☐ | Ubuntu aktualisiert, SSH, Docker-Gruppe |
| 2 | ☐ | `~/Projekte/1100-AI-OS-V2` vollständig synchron |
| 3 | ☐ | Cursor öffnet diesen Ordner |
| 4 | ☐ | Antigravity startet |
| 5 | ☐ | Obsidian-Vault = dieser Ordner |
| 6 | ☐ | Gelesen: `docs/11-PLATFORM-VM.md` + `docs/12-LEITPRINZIPIEN.md` |
| 7 | ☐ | `.env` aus `.env.example` · `deploy/infra.yml` + `monitoring.yml` up |

---

## Reihenfolge

1. Ubuntu fertig installieren  
2. Dokus syncen  
3. Cursor + Antigravity + Obsidian  
4. Roadmap Phase 0 lesen  
5. Compose-Infra starten (Schritt 5)  

Host-Hinweis Ubuntu-26.04 in virt-manager: [`fix-osinfo-ubuntu-2604.md`](fix-osinfo-ubuntu-2604.md).
