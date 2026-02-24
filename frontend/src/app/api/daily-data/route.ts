import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

function checkSecret(req: NextRequest): boolean {
  const secret = req.headers.get("x-api-secret");
  return secret === process.env.API_SECRET;
}

export async function POST(req: NextRequest) {
  if (!checkSecret(req)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const { date, data } = body;

  if (!date || !data) {
    return NextResponse.json(
      { error: "Missing required fields: date, data" },
      { status: 400 }
    );
  }

  const entry = await prisma.dailyData.upsert({
    where: { date: new Date(date + "T00:00:00.000Z") },
    update: { data },
    create: { date: new Date(date + "T00:00:00.000Z"), data },
  });

  return NextResponse.json(entry, { status: 201 });
}
