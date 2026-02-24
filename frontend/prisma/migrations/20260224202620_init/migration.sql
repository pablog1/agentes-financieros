-- CreateTable
CREATE TABLE "agents" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "full_alias" TEXT NOT NULL,
    "age" INTEGER NOT NULL,
    "report_name" TEXT NOT NULL,
    "motto" TEXT NOT NULL,
    "personality" TEXT NOT NULL,
    "risk_stance" TEXT NOT NULL,
    "audience" TEXT NOT NULL,
    "avatar_url" TEXT,
    "color" TEXT NOT NULL,
    "sort_order" INTEGER NOT NULL,
    "min_words" INTEGER NOT NULL,
    "max_words" INTEGER NOT NULL,

    CONSTRAINT "agents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "reports" (
    "id" SERIAL NOT NULL,
    "agent_id" TEXT NOT NULL,
    "date" DATE NOT NULL,
    "title" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "word_count" INTEGER NOT NULL,
    "excerpt" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "reports_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "daily_data" (
    "id" SERIAL NOT NULL,
    "date" DATE NOT NULL,
    "data" JSONB NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "daily_data_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "reports_agent_id_date_key" ON "reports"("agent_id", "date");

-- CreateIndex
CREATE UNIQUE INDEX "daily_data_date_key" ON "daily_data"("date");

-- AddForeignKey
ALTER TABLE "reports" ADD CONSTRAINT "reports_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "agents"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
