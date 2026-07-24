import { NextResponse } from "next/server";
import { checkPlatformHealth } from "@/lib/platform-health";

export const dynamic = "force-dynamic";

export async function GET() {
  const health = await checkPlatformHealth();
  return NextResponse.json(health);
}
