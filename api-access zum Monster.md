August 26

# KI-Server API- & Netzwerk-Dokumentation

**Stand:** 10. August 2026  
**Server IP im lokalen Netzwerk:** `192.168.178.116`  
**Lokale Alias-Adresse:** `localhost` / `127.0.0.1`  
**Hardware:** NVIDIA GeForce RTX 4090 (24 GB VRAM) | 192 GB System-RAM  
**Hot Storage (NVMe SSD 2):** `/mnt/ai-hot-storage/`

---

## ![📌](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f4cc/32.png) 1. Übersicht aller Dienste & Endpunkte

| Dienst | Port | Base URL / Endpunkt | Protokoll / Format | Einsatzzweck |
| :--- | :--- | :--- | :--- | :--- |
| **Ollama API** | `11434` | `http://192.168.178.116:11434` | Ollama & OpenAI REST | Sprach- & Vision-Modelle, Embeddings |
| **vLLM Agent Server** | `8001` | `[http://192.168.178.116:8001/v1`](http://192.168.178.116:8001/v1) | OpenAI API Compatible | High-Throughput parallele Agenten |
| **ComfyUI (FLUX.1)** | `8188` | `http://192.168.178.116:8188` | HTTP Web / JSON API | Bild- & Videogenerierung auf RTX 4090 |
| **Open WebUI** | `3000` | `http://192.168.178.116:3000` | Web UI | Visuelle ChatGPT-Alternative |
| **Qdrant Vector DB** | `6333` | `http://192.168.178.116:6333` | REST / gRPC | Vektorspeicher für RAG-Gedächtnis |
| **n8n Automation** | `5678` | `http://192.168.178.116:5678` | Web UI / REST | Workflow- & Agenten-Orchestrierung |
| **Portainer Dashboard** | `9000` | `http://192.168.178.116:9000` | Web UI | Docker Container-Verwaltung |

---

## ![🧠](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f9e0/32.png) 2. Ollama API (Sprach-, Vision- & Embedding-Modelle)

Anbindung für Company-VM, Open WebUI und n8n Workflows.

### API-Endpunkte:
* **Native Ollama Chat API:** `[http://192.168.178.116:11434/api/chat`](http://192.168.178.116:11434/api/chat)
* **Native Ollama Generate API:** `[http://192.168.178.116:11434/api/generate`](http://192.168.178.116:11434/api/generate)
* **OpenAI-kompatibler Endpunkt:** `[http://192.168.178.116:11434/v1`](http://192.168.178.116:11434/v1)

### Modellnamen für Aufrufe:
* `deepseek-r1:32b` ➔ Logik, Reasoning & komplexe Problemlösung (128k Kontext)
* `qwen2.5-coder:32b` ➔ Code, Webseiten, JSON & Tool-Calling (128k Kontext)
* `mistral-nemo:12b` ➔ E-Mails, Blogs & deutsche Texte (128k Kontext)
* `hermes3:8b` ➔ Multi-Agenten Orchestrierung & Tool-Calling
* `llama3.2-vision:11b` ➔ OCR, Bild-, PDF- & Dokumentenanalyse
* `bge-m3` ➔ Multilinguales Embedding für Qdrant RAG

### Code-Beispiele (Ollama):

#### Bash (cURL):
```bash
curl [http://192.168.178.116:11434/api/chat](http://192.168.178.116:11434/api/chat) -d '{
  "model": "qwen2.5-coder:32b",
  "messages": [
    { "role": "user", "content": "Erstelle eine JSON-Struktur für Kalendereinträge." }
  ],
  "stream": false
}'
```

#### Python (Ollama Client):
```python
import requests

response = [requests.post](http://requests.post/)(
    "[http://192.168.178.116:11434/api/chat](http://192.168.178.116:11434/api/chat)",
    json={
        "model": "deepseek-r1:32b",
        "messages": [{"role": "user", "content": "Analysiere folgende Logikfrage..."}],
        "stream": False
    }
)
print(response.json()["message"]["content"])
```

---

## ![⚡](https://fonts.gstatic.com/s/e/notoemoji/17.0/26a1/32.png) 3. vLLM Agent Server (Parallele Agenten Inferenz)

High-Throughput Inferenz-Engine für hoch-parallele Agenten-Systeme (PagedAttention & KV-Cache Sharing).

### API-Endpunkte:
* **Base URL:** `[http://192.168.178.116:8001/v1`](http://192.168.178.116:8001/v1)
* **Chat Endpunkt:** `[http://192.168.178.116:8001/v1/chat/completions`](http://192.168.178.116:8001/v1/chat/completions)
* **Modellname:** `Qwen/Qwen2.5-Coder-14B-Instruct`
* **API-Key:** `none` (lokal nicht erforderlich)

### Code-Beispiele (vLLM via OpenAI SDK):

#### Python (OpenAI SDK):
```python
from openai import OpenAI

client = OpenAI(
    base_url="[http://192.168.178.116:8001/v1](http://192.168.178.116:8001/v1)",
    api_key="none"
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-14B-Instruct",
    messages=[{"role": "user", "content": "Generiere den Code für den E-Mail Agenten."}]
)
print(response.choices[0].message.content)
```

---

## ![🎨](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f3a8/32.png) 4. ComfyUI API (FLUX.1 Bildgenerierung)

* **Web UI:** `http://192.168.178.116:8188`
* **Prompt API Endpunkt:** `[http://192.168.178.116:8188/prompt`](http://192.168.178.116:8188/prompt)
* **Vorgefertigte Workflow JSON:** [`flux_schnell_workflow.json`](file:///home/peter/Schreibtisch/KI-Stack/flux_schnell_workflow.json)
* **Bild-Ausgabeordner (SSD 2):** `/mnt/ai-hot-storage/workspace/comfyui-output/`

---

## ![🗄️](https://fonts.gstatic.com/s/e/notoemoji/17.0/1f5c4_fe0f/32.png) 5. Qdrant Vektor-Datenbank (RAG-Gedächtnis)

* **REST API:** `http://192.168.178.116:6333`
* **Collections List:** `[http://192.168.178.116:6333/collections`](http://192.168.178.116:6333/collections)
* **Vektor-Speicherpfad (SSD 2):** `/mnt/ai-hot-storage/vector-db/`