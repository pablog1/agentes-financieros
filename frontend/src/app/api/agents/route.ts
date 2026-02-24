import { NextResponse } from "next/server";
import { getAgents } from "@/lib/queries";

export async function GET() {
  const agents = await getAgents();
  return NextResponse.json(agents);
}
