import { NextResponse } from "next/server";
import { getPortfolioData } from "@/lib/portfolio-db";

export async function GET() {
  const projects = await getPortfolioData();
  return NextResponse.json({ projects });
}
