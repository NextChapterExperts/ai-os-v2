import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  let filePath = searchParams.get("path") || searchParams.get("fileUri") || "";

  if (filePath.startsWith("file://")) {
    filePath = filePath.replace("file://", "");
  }

  if (!filePath) {
    return new NextResponse("Fehlender Dateipfad", { status: 400 });
  }

  const normalizedPath = path.normalize(filePath);
  if (!normalizedPath.startsWith("/home/peter/Projekte")) {
    return new NextResponse("Zugriff verweigert", { status: 403 });
  }

  try {
    exec(`xdg-open "${normalizedPath}"`);
    return new NextResponse(`
      <!DOCTYPE html>
      <html>
      <head><title>Öffne Datei...</title></head>
      <body style="background:#0b0f17;color:#818cf8;font-family:sans-serif;padding:2rem;text-align:center;">
        <h2>🚀 Öffne Datei im System...</h2>
        <p style="color:#94a3b8;font-family:monospace;">${normalizedPath}</p>
        <script>setTimeout(() => window.close(), 1500);</script>
      </body>
      </html>
    `, { headers: { "Content-Type": "text/html; charset=utf-8" } });
  } catch (err: any) {
    return new NextResponse(`Fehler beim Öffnen: ${err.message}`, { status: 500 });
  }
}
