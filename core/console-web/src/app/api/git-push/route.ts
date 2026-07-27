import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export async function POST() {
  try {
    const scriptPath = "/home/peter/Projekte/active/git-push-active.sh";
    const { stdout, stderr } = await execAsync(`bash ${scriptPath}`, {
      cwd: "/home/peter/Projekte/active",
      env: { ...process.env, PATH: `${process.env.PATH}:/usr/bin:/bin` },
    });

    return NextResponse.json({
      ok: true,
      timestamp: new Date().toISOString(),
      output: stdout,
      errors: stderr,
    });
  } catch (error: any) {
    console.error("Git Push execution failed:", error);
    return NextResponse.json(
      {
        ok: false,
        error: error.message || "Execution failed",
        output: error.stdout || "",
        stderr: error.stderr || "",
      },
      { status: 500 }
    );
  }
}
