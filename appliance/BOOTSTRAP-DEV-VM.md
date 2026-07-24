# Bootstrap DEV-VM — Tools + Dokus (erster Tag)

**Ziel:** Nach Ubuntu-Installation sofort arbeitsfähig: Obsidian, Cursor, Antigravity, AI-OS-v2-Dokus.  
**VM:** `ai-os-dev` · Ubuntu 26.04 Desktop · NCE First-Party Company Brain (später Docker).

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
sudo usermod -aG docker $USER
# danach neu einloggen

mkdir -p ~/Projekte /opt/ai-os ~/Transfers
```

IP der VM notieren (`ip -4 a`) — vom Host aus erreichbar (NAT/Portweiterleitung oder Bridge).ip -4
ip -a

---

## 1. Dokus in die VM (AI-OS v2)

**Pfad in der VM (empfohlen):**

```text
~/Projekte/1100-AI-OS-V2/     # Arbeitskopie + Obsidian-Vault-Root
# optional später Symlink:
# sudo ln -s ~/Projekte/1100-AI-OS-V2 /opt/ai-os
```

### Variante A — vom Host per `rsync` (bevorzugt)

Auf dem **Tuxedo-Host** (VM muss laufen, SSH erreichbar):

```bash
# USER/IP der VM anpassen
export VM=peter@192.168.122.XX   # oder Hostname

rsync -av --progress \
  /home/peter/peters-brain/Projekte/1100-AI-OS-V2/ \
  "$VM:~/Projekte/1100-AI-OS-V2/"
```

Oder Skript:

```bash
cd /home/peter/peters-brain/Projekte/1100-AI-OS-V2
./appliance/sync-docs-to-vm.sh peter@192.168.122.XX
```

### Variante B — Spice/virt-manager Ordnerfreigabe

Host-Ordner `…/1100-AI-OS-V2` als Shared Folder einbinden → in der VM nach `~/Projekte/` kopieren.

### Variante C — Git (sobald Remote existiert)

```bash
git clone <ai-os-v2-remote> ~/Projekte/1100-AI-OS-V2
```

**Einstieg lesen:** `README.md` → `docs/11-PLATFORM-VM.md` → `docs/12-LEITPRINZIPIEN.md` → `ROADMAP.md` Kap. 5.

Optional zusätzlich (Referenz, nicht Pflicht Tag 1):

```bash
rsync -av /home/peter/peters-brain/Projekte/1000-AI-OS/docs/ \
  "$VM:~/Projekte/1000-AI-OS-docs-ref/"
```

---

## 2. Cursor

**Auf dem Host liegen bereits Debs**, z. B.:

- `/home/peter/Downloads/cursor_3.2.21_amd64.deb` (neueste der vorhandenen)

In die VM kopieren und installieren:

```bash
# Host:
scp /home/peter/Downloads/cursor_3.2.21_amd64.deb "$VM:~/Transfers/"

# VM:
sudo apt install -y ~/Transfers/cursor_*.deb
# oder: sudo dpkg -i ~/Transfers/cursor_*.deb && sudo apt -f install -y
```

Workspace öffnen: `~/Projekte/1100-AI-OS-V2`.

---

## 3. Antigravity

Host hat u. a. `/home/peter/Downloads/Antigravity.tar.gz` bzw. entpackt `Antigravity-x64/`.

```bash
# Host:
scp /home/peter/Downloads/Antigravity.tar.gz "$VM:~/Transfers/"

# VM:
cd ~
tar -xzf ~/Transfers/Antigravity.tar.gz
# Pfad je nach Archiv — typisch:
# ~/Antigravity-x64/antigravity  oder ähnlich
chmod +x ~/Antigravity*/antigravity 2>/dev/null || true
# Desktop-Starter optional selbst anlegen
```

**Inbox für späteres Capture (jetzt schon anlegen):**

```bash
sudo mkdir -p /opt/ai-os/ingest/inbox
sudo chown -R "$USER:$USER" /opt/ai-os
```

Antigravity/Cursor-Notizen später hier oder unter `~/Projekte/1100-AI-OS-V2/` ablegen.

---

## 4. Obsidian

```bash
# Flatpak (einfach, Updates über Flathub)
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub md.obsidian.Obsidian
flatpak run md.obsidian.Obsidian
```

Oder offizielles `.deb`/AppImage von https://obsidian.md/download → `~/Transfers/`.

**Vault öffnen:** Ordner `~/Projekte/1100-AI-OS-V2`  
(Markdown-Dokus liegen unter `docs/` + `ROADMAP.md` / `README.md` im Root.)

Empfohlen in Obsidian: „Detect all file extensions“ aus, Git später optional.

---

## 5. Checkliste „loslegen“

| # | Erledigt? | Schritt |
|---|-----------|---------|
| 1 | ☐ | Ubuntu aktualisiert, SSH, Docker-Gruppe |
| 2 | ☐ | `~/Projekte/1100-AI-OS-V2` vollständig synchron |
| 3 | ☐ | Cursor öffnet diesen Ordner |
| 4 | ☐ | Antigravity startet |
| 5 | ☐ | Obsidian-Vault = dieser Ordner |
| 6 | ☐ | Gelesen: `docs/11-PLATFORM-VM.md` + `docs/12-LEITPRINZIPIEN.md` |
| 7 | ☐ | Obsidian: Vault-Ordner inkl. `customers/nextchapter/knowledge/seed/` (Company Brain) |
| 8 | ☐ | (als Nächstes) `deploy/infra.yml` — noch nicht Tag-1-Pflicht |

---

## Reihenfolge heute

1. Ubuntu fertig installieren  
2. Dokus rsyncen  
3. Cursor + Antigravity + Obsidian installieren  
4. In Obsidian/Cursor Roadmap Phase 0 lesen  
5. **Danach** Docker-Compose-Infra im Repo anlegen/starten  

Netzwerk: Wenn SSH von Host nicht geht → in virt-manager für die VM Portweiterleitung `host 2222 → guest 22` oder Netzmodus **Bridge**.
