import { test, expect } from "@playwright/test";
test("collection loading, timeline zoom, precision filters and linked records", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const requests: string[] = [];
  page.on("request", (r) => requests.push(r.url()));
  await page.goto("/?collection=anglo");
  await expect(page.getByLabel("Select collection")).toHaveValue("anglo");
  await expect(
    page.getByRole("button", { name: "Zoom in", exact: true }),
  ).toBeVisible();
  expect(
    requests.some(
      (url) =>
        url.includes("collections/anglo.json") || /assets\/anglo-/.test(url),
    ),
  ).toBeTruthy();
  expect(
    requests.some(
      (url) =>
        url.includes("collections/scott.json") ||
        url.includes("collections/yankee.json") ||
        /assets\/(scott|yankee)-/.test(url),
    ),
  ).toBeFalsy();
  const before = await page.locator(".chart-footer [aria-live]").innerText();
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await expect(page.locator(".chart-footer [aria-live]")).not.toHaveText(
    before,
  );
  await page.getByLabel("Timeline participant").selectOption("milner");
  await expect(page.locator(".result-count")).not.toHaveText(
    "90 matching events",
  );
  await page.getByLabel("Timeline participant").selectOption("");
  await page.getByLabel("Timeline period").selectOption("1919-1939");
  await expect(page.locator(".result-count")).not.toHaveText(
    "90 matching events",
  );
  await page.locator(".thread-controls > summary").click();
  await page.getByRole("button", { name: "Hide all", exact: true }).click();
  await expect(
    page.getByText("Select a timeline thread to start exploring."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Show all", exact: true }).click();
  await page.getByRole("button", { name: /^Characters/ }).click();
  await page.getByLabel("Search archive").fill("Cecil John Rhodes");
  await page
    .getByRole("heading", { name: "Cecil John Rhodes", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(
    page.getByText("Quigley’s tentative classification"),
  ).toBeVisible();
  await expect(
    page
      .getByRole("dialog")
      .getByText(/PDF pp\./)
      .first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Explore connections" }).click();
  await expect(page.getByLabel("Connection focus")).toHaveValue("rhodes");
  await expect(
    page.getByRole("button", { name: "Zoom in connections" }),
  ).toBeVisible();
  await page.screenshot({
    path: "tmp/pdfs/dark-time-connections.png",
    fullPage: false,
  });
  expect(errors).toEqual([]);
});
test("pagination, cross-source identities, source qualifications, old deep links", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?collection=yankee");
  await page.getByRole("button", { name: /^Characters/ }).click();
  await expect(page.locator(".record")).toHaveCount(24);
  await page.getByRole("button", { name: "Next page" }).first().click();
  await expect(page.locator(".pager").first()).toContainText("Page 2");
  await page.getByLabel("Search archive").fill("Howard Hughes");
  await page
    .getByRole("heading", { name: "Howard Hughes", exact: true })
    .click();
  await expect(
    page.getByRole("dialog").getByText("Accounts across sources"),
  ).toBeVisible();
  await expect(
    page
      .getByRole("dialog")
      .getByText("The Yankee and Cowboy War", { exact: true })
      .first(),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.getByLabel("Select collection").selectOption("scott");
  await expect(
    page.getByRole("heading", { name: "Hughes", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: /^Sources/ }).click();
  const scott = page.locator(".source-card").filter({
    has: page.getByRole("heading", {
      name: "The State, the Deep State, and the Wall Street Overworld",
      exact: true,
    }),
  });
  await scott.getByText("Source qualifications & conflicting accounts").click();
  await expect(scott).toContainText("no published evidence Copeland");
  await page.goto("/#nader");
  await expect(page.getByRole("dialog", { name: "Ralph Nader" })).toBeVisible();
  await expect(page.getByLabel("Select collection")).toHaveValue("gemstone");
  expect(errors).toEqual([]);
});
test("mobile navigation and responsive directories", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?collection=scott");
  await expect(
    page.getByRole("button", { name: "Open navigation" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: /^Events/ }).click();
  await expect(page.locator(".record")).toHaveCount(24);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "tmp/pdfs/dark-time-mobile.png",
    fullPage: false,
  });
});
test("Gemstone markers explain source narrative, all date ticks show years, sources work offline", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?collection=gemstone");
  await page.getByLabel("Timeline period").selectOption("1967-1972");
  await expect(
    page.getByRole("button", { name: "Zoom in", exact: true }),
  ).toBeVisible();
  const labels = await page
    .locator(".chart-scroll .tick text")
    .allTextContents();
  expect(labels.length).toBeGreaterThan(2);
  for (const label of labels) expect(label).toMatch(/\d{4}/);
  const marker = page.getByRole("button", {
    name: "Nixon’s election and Roberts’ claimed leverage, 1968-11-05, day precision",
    exact: true,
  });
  await expect(marker).toHaveCount(2);
  await marker.first().hover();
  await expect(page.locator(".timeline-tooltip")).toContainText(
    "became evasive afterward",
  );
  await marker.first().click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.locator(".highlighted-connection")).toHaveCount(1);
  await expect(marker.first()).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await expect(page.locator(".highlighted-connection")).toHaveCount(1);
  await page.getByRole("button", { name: "Read event account" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("What the source says");
  await expect(dialog).toContainText("Richard Carlson");
  await expect(dialog).toContainText("California vote shift");
  await expect(dialog).toContainText("Why this point connects the threads");
  expect(await page.locator('a[href^="http"]').count()).toBe(0);
  await page.screenshot({
    path: "tmp/pdfs/dark-time-source-summary.png",
    fullPage: false,
  });
  await page.getByRole("button", { name: "Close details" }).click();
  await page.locator(".timeline-layout").scrollIntoViewIfNeeded();
  await page.screenshot({
    path: "tmp/pdfs/dark-time-timeline.png",
    fullPage: false,
  });
  expect(errors).toEqual([]);
});
test("arbitrary source overlays expose cited shared actors and attributed influence", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?collection=anglo");
  await page
    .getByRole("checkbox", {
      name: "Include The Real Gemstone File · Part One",
    })
    .check();
  await expect(
    page.getByRole("checkbox", {
      name: "Include The Anglo-American Establishment",
    }),
  ).toBeChecked();
  await expect(page.locator(".shared-entities")).toContainText(
    "Winston Churchill",
  );
  await expect(page.locator(".chart-scroll path[marker-end]")).not.toHaveCount(
    0,
  );
  expect(
    new URL(page.url()).searchParams.get("collection")?.split(",").sort(),
  ).toEqual(["anglo", "gemstone"]);
  await page
    .locator(".shared-entities")
    .getByRole("button", { name: "Winston Churchill", exact: true })
    .click();
  await expect(page.getByLabel("Timeline participant")).toHaveValue(
    "winston-churchill",
  );
  await page.locator(".event-list-fold > summary").click();
  await expect(page.locator(".timeline-event-list")).toContainText(
    "Roberts alleges a 1932",
  );
  await page.reload();
  await expect(
    page.getByRole("checkbox", {
      name: "Include The Real Gemstone File · Part One",
    }),
  ).toBeChecked();
  await page
    .getByRole("checkbox", {
      name: "Include The State, the Deep State, and the Wall Street Overworld",
    })
    .check();
  await expect(
    page.getByRole("checkbox", {
      name: "Include The State, the Deep State, and the Wall Street Overworld",
    }),
  ).toBeChecked();
  await expect(
    page.getByRole("button", { name: "Zoom in", exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("complete export includes all sources and on-demand event narratives", async ({
  page,
}) => {
  await page.goto("/?collection=scott");
  await expect(
    page.getByRole("button", { name: "Zoom in", exact: true }),
  ).toBeVisible();
  const downloading = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export all collections" }).click();
  const download = await downloading;
  const file = await download.path();
  const fs = await import("node:fs/promises");
  const exported = JSON.parse(await fs.readFile(file!, "utf8"));
  expect(exported.sources).toHaveLength(4);
  expect(exported.events).toHaveLength(221);
  expect(
    exported.events.every((e: { sourceSummaries?: { details: string[] }[] }) =>
      e.sourceSummaries?.some((s) => s.details.length >= 2),
    ),
  ).toBeTruthy();
});

test("timeline uses document scrolling and keeps source controls in view", async ({
  page,
}) => {
  await page.goto("/?collection=gemstone,anglo");
  await expect(page.locator(".timeline svg")).toBeVisible();
  await page.locator(".timeline-layout").scrollIntoViewIfNeeded();
  const nestedScroll = await page
    .locator(".timeline-layout, .chart-scroll, .sidebar")
    .evaluateAll((elements) =>
      elements.some((el) => /auto|scroll/.test(getComputedStyle(el).overflowY)),
    );
  expect(nestedScroll).toBe(false);
  await page.evaluate(() => window.scrollBy(0, 700));
  const bounds = await page.locator(".timeline-selection-bar").boundingBox();
  expect(bounds!.y).toBeGreaterThanOrEqual(0);
  expect(bounds!.y).toBeLessThan(50);
  await expect(
    page.getByRole("checkbox", { name: /Include The Real Gemstone File/ }),
  ).toBeVisible();
});
