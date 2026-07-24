# Fix: virt-manager kennt Ubuntu 26.04 nicht

**Ursache:** Host ist TUXEDO/Ubuntu **24.04**. Paket `osinfo-db` kennt nur bis **25.10**. QEMU selbst ist ok — kein QEMU-Update nötig.

## Sofort-Workaround (ohne Update)

Beim Anlegen der VM:

1. ISO = Ubuntu **26.04** Desktop (wie geplant)
2. Betriebssystem manuell: **Ubuntu 25.10** oder **Ubuntu 24.04 LTS**
3. Installation läuft normal — die OS-Auswahl steuert nur Defaults (VirtIO etc.)

## Optional: Ubuntu 26.04 in der Liste (1× sudo)

```bash
sudo cp /home/peter/.local/share/osinfo/os/ubuntu.com/ubuntu-26.04.xml \
  /usr/share/osinfo/os/ubuntu.com/ubuntu-26.04.xml

# virt-manager komplett schließen und neu starten
virt-manager
```

Prüfen:

```bash
python3 - <<'PY'
import gi
gi.require_version('Libosinfo', '1.0')
from gi.repository import Libosinfo
loader = Libosinfo.Loader()
loader.process_default_path()
db = loader.get_db()
ids = [(db.get_os_list().get_nth(i).get_short_id()) for i in range(db.get_os_list().get_length())]
print('ubuntu26.04' in ids)
PY
```

Datei liegt bereits unter: `~/.local/share/osinfo/os/ubuntu.com/ubuntu-26.04.xml` (Upstream-Vorlage).
