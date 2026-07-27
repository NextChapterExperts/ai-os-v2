import { NextRequest, NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  let filePath = searchParams.get("path") || searchParams.get("fileUri") || "";

  // Strip file:// prefix if present
  if (filePath.startsWith("file://")) {
    filePath = filePath.replace("file://", "");
  }

  if (!filePath) {
    return new NextResponse("Fehlender Dateipfad", { status: 400 });
  }

  // Security check: ensure path is within /home/peter/Projekte
  const normalizedPath = path.normalize(filePath);
  if (!normalizedPath.startsWith("/home/peter/Projekte")) {
    return new NextResponse("Zugriff verweigert (Pfad außerhalb von /home/peter/Projekte)", { status: 403 });
  }

  try {
    const stat = await fs.stat(normalizedPath);

    if (stat.isDirectory()) {
      const files = await fs.readdir(normalizedPath);
      const html = `
        <!DOCTYPE html>
        <html lang="de">
        <head>
          <meta charset="UTF-8">
          <title>Ordner: ${path.basename(normalizedPath)}</title>
          <style>
            body { font-family: -apple-system, sans-serif; background: #0b0f17; color: #e2e8f0; padding: 2rem; }
            h1 { color: #818cf8; font-size: 1.5rem; }
            ul { list-style: none; padding: 0; }
            li { margin: 0.5rem 0; font-family: monospace; }
            a { color: #38bdf8; text-decoration: none; }
            a:hover { text-decoration: underline; }
          </style>
        </head>
        <body>
          <h1>📁 Ordner: ${normalizedPath}</h1>
          <ul>
            ${files
              .map(
                (f) =>
                  `<li>📄 <a href="/api/view-file?path=${encodeURIComponent(
                    path.join(normalizedPath, f)
                  )}">${f}</a></li>`
              )
              .join("")}
          </ul>
        </body>
        </html>
      `;
      return new NextResponse(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }

    const content = await fs.readFile(normalizedPath, "utf-8");
    const ext = path.extname(normalizedPath).toLowerCase();

    if (ext === ".md" || ext === ".markdown" || ext === ".txt" || ext === ".canvas") {
      const html = `
        <!DOCTYPE html>
        <html lang="de">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>${path.basename(normalizedPath)} — VIRKI Viewer</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f17; color: #f1f5f9; margin: 0; padding: 2rem; line-height: 1.6; }
            .header { border-bottom: 1px solid #1e293b; padding-bottom: 1rem; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }
            .title { font-size: 1.25rem; font-weight: bold; color: #818cf8; font-family: monospace; }
            .path { font-size: 0.8rem; color: #94a3b8; font-family: monospace; margin-top: 0.25rem; }
            pre { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.5rem; overflow-x: auto; white-space: pre-wrap; font-family: "IBM Plex Mono", Consolas, monospace; font-size: 0.9rem; color: #e2e8f0; }
            .btn { background: #312e81; color: #c7d2fe; padding: 0.4rem 0.8rem; text-decoration: none; border-radius: 6px; font-size: 0.8rem; font-family: monospace; border: 1px solid #4338ca; }
            .btn:hover { background: #3730a3; color: white; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <div class="title">📄 ${path.basename(normalizedPath)}</div>
              <div class="path">${normalizedPath}</div>
            </div>
            <div>
              <a href="/api/open-local?path=${encodeURIComponent(normalizedPath)}" class="btn" target="_blank">💻 Im System/Editor öffnen</a>
            </div>
          </div>
          <pre>${content.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</pre>
        </body>
        </html>
      `;
      return new NextResponse(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }

    return new NextResponse(content, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
  } catch (err: any) {
    return new NextResponse(`Datei nicht gefunden oder lesbar: ${err.message}`, { status: 444 });
  }
}
