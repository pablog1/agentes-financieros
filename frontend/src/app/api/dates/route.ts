import { NextRequest, NextResponse } from "next/server";
import { getAvailableDates } from "@/lib/queries";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const limit = parseInt(searchParams.get("limit") || "30");

  const dates = await getAvailableDates(Math.min(limit, 365));
  return NextResponse.json(dates);
}
