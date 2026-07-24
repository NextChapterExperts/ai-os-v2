import { NextResponse } from "next/server";
import { memoryStats } from "@/lib/memory";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(memoryStats());
}
