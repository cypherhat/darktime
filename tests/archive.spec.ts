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
  await page.goto("/?collection=gemstone,scott#allen-dulles");
  await expect(
    page.getByRole("dialog", { name: "Allen W. Dulles" }),
  ).toBeVisible();
  await expect(page.getByLabel("Select collection")).toHaveValue("scott");
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
test("PDF markers explain source narrative, all date ticks show years, sources work offline", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?collection=scott");
  await page.getByLabel("Timeline period").selectOption("1939-1949");
  await expect(
    page.getByRole("button", { name: "Zoom in", exact: true }),
  ).toBeVisible();
  const labels = await page
    .locator(".chart-scroll .tick text")
    .allTextContents();
  expect(labels.length).toBeGreaterThan(2);
  for (const label of labels) expect(label).toMatch(/\d{4}/);
  const marker = page.getByRole("button", {
    name: "Dulles convenes CIA planning advisers, 1946, year precision",
    exact: true,
  });
  await expect(marker).toHaveCount(2);
  await marker.first().hover();
  await expect(page.locator(".timeline-tooltip")).toContainText(
    "all but one from Wall Street",
  );
  await marker.first().click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.locator(".highlighted-connection")).toHaveCount(1);
  await expect(marker.first()).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await expect(page.locator(".highlighted-connection")).toHaveCount(1);
  await page.getByRole("button", { name: "Show details", exact: true }).click();
  const dialog = page.getByRole("complementary", {
    name: "Timeline event details",
  });
  await dialog.getByRole("tab", { name: "Source account" }).click();
  await expect(dialog).toContainText("What the source says");
  await expect(dialog).toContainText("William H. Jackson");
  await expect(dialog).toContainText("revolving-door argument");
  await expect(dialog).toContainText("Why this point connects the threads");
  expect(await page.locator('a[href^="http"]').count()).toBe(0);
  await page.screenshot({
    path: "tmp/pdfs/dark-time-source-summary.png",
    fullPage: false,
  });
  await page.getByRole("button", { name: "Close timeline details" }).click();
  await page.locator(".timeline-layout").scrollIntoViewIfNeeded();
  await page.screenshot({
    path: "tmp/pdfs/dark-time-timeline.png",
    fullPage: false,
  });
  expect(errors).toEqual([]);
});
test("PDF source overlays retain shared identities and source-described influence", async ({
  page,
}) => {
  await page.goto("/?collection=anglo");
  await page
    .getByRole("checkbox", {
      name: "Include The State, the Deep State, and the Wall Street Overworld",
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
  ).toEqual(["anglo", "scott"]);
  await page
    .locator(".shared-entities")
    .getByRole("button", { name: "Winston Churchill", exact: true })
    .click();
  await expect(page.getByLabel("Timeline participant")).toHaveValue(
    "winston-churchill",
  );
  await page.reload();
  await expect(
    page.getByRole("checkbox", {
      name: "Include The State, the Deep State, and the Wall Street Overworld",
    }),
  ).toBeChecked();
  await page
    .getByRole("checkbox", { name: "Include The Yankee and Cowboy War" })
    .check();
  await expect(
    page.getByRole("button", { name: "Zoom in", exact: true }),
  ).toBeVisible();
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
  expect(exported.events).toHaveLength(450);
  expect(
    exported.events.every((e: { sourceSummaries?: { details: string[] }[] }) =>
      e.sourceSummaries?.some((s) => s.details.length >= 2),
    ),
  ).toBeTruthy();
});

test("timeline uses document scrolling and keeps source controls in view", async ({
  page,
}) => {
  await page.goto("/?collection=scott,anglo");
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
    page.getByRole("checkbox", {
      name: "Include The State, the Deep State, and the Wall Street Overworld",
    }),
  ).toBeVisible();
});

test("event panel explores connections alongside the highlighted timeline", async ({
  page,
}) => {
  await page.goto("/?collection=scott");
  await page.getByLabel("Timeline period").selectOption("1939-1949");
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await page.waitForTimeout(400);
  const marker = page.getByRole("button", {
    name: "Dulles convenes CIA planning advisers, 1946, year precision",
    exact: true,
  });
  await marker.first().click();
  const panel = page.getByRole("complementary", {
    name: "Timeline event details",
  });
  await expect(panel).toBeVisible();
  await expect(
    panel.getByRole("heading", {
      name: "Dulles convenes CIA planning advisers",
    }),
  ).toBeVisible();
  await expect(page.locator(".highlighted-connection")).toHaveCount(1);
  const zoomed = await page.locator(".chart-footer [aria-live]").innerText();
  await panel.getByRole("button", { name: /Allen W\. Dulles/ }).click();
  await expect(
    panel.getByRole("heading", { name: "Allen W. Dulles", exact: true }),
  ).toBeVisible();
  await expect(panel.getByText("Events involving this record")).toBeVisible();
  await expect(page.locator(".highlighted-connection")).toHaveCount(1);
  await panel.getByRole("button", { name: "Back in event details" }).click();
  await panel.getByRole("tab", { name: "Source account" }).click();
  await expect(panel).toContainText("revolving-door argument");
  await expect(panel).toContainText("Why this point connects the threads");
  await page.evaluate(() => window.scrollBy(0, 300));
  await expect(panel).toBeVisible();
  await expect(page.locator(".chart-footer [aria-live]")).toHaveText(zoomed);
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.screenshot({ path: "/tmp/darktime-inspector.png" });
  await panel.getByRole("button", { name: "Close timeline details" }).click();
  await expect(panel).not.toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await marker.first().click();
  await expect(panel).toBeVisible();
  const bounds = await panel.boundingBox();
  expect(bounds!.width).toBe(390);
  expect(bounds!.height).toBeLessThan(440);
});

test("removed source is absent from controls, exports and lazy bundles", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (request) => requests.push(request.url()));
  await page.goto("/?collection=gemstone");
  await expect(page.getByLabel("Select collection")).toHaveValue("anglo");
  await expect(page.locator(".source-selection input")).toHaveCount(4);
  await expect(page.getByRole("checkbox", { name: /Gemstone/ })).toHaveCount(0);
  await page.getByRole("button", { name: /^Sources/ }).click();
  await expect(page.locator(".source-card .source-byline")).toHaveCount(4);
  expect(
    requests.some((url) =>
      /assets\/gemstone-|collections\/gemstone|narratives\/gemstone/.test(url),
    ),
  ).toBe(false);
});

test("Tragedy and Hope loads alone, distinguishes Quigley books and overlays shared institutions", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const requests: string[] = [];
  page.on("request", (request) => requests.push(request.url()));
  await page.goto("/?collection=tragedy");
  await expect(page.getByLabel("Select collection")).toHaveValue("tragedy");
  await expect(page.locator(".result-count")).toHaveText("247 matching events");
  await expect(page.locator(".source-selection")).toContainText(
    "Quigley · Tragedy and Hope",
  );
  await expect(page.locator(".source-selection")).toContainText(
    "Quigley · Anglo-American Establishment",
  );
  expect(requests.some((url) => /assets\/tragedy-/.test(url))).toBe(true);
  expect(
    requests.some((url) => /assets\/(anglo|scott|yankee)-/.test(url)),
  ).toBe(false);
  await page
    .getByRole("checkbox", {
      name: "Include The State, the Deep State, and the Wall Street Overworld",
    })
    .check();
  await page.getByLabel("Timeline period").selectOption("1950-1979");
  await page.getByLabel("Timeline participant").selectOption("allen-dulles");
  const marker = page.getByRole("button", {
    name: "CIA-backed operation overthrows Mossadeq in Iran, 1953-08, month precision",
    exact: true,
  });
  await expect(marker).toHaveCount(3);
  await marker.first().click();
  const panel = page.getByRole("complementary", {
    name: "Timeline event details",
  });
  await expect(panel).toContainText("Allen W. Dulles");
  await expect(page.locator(".highlighted-connection")).not.toHaveCount(0);
  await panel.getByRole("tab", { name: "Source account" }).click();
  await expect(panel).toContainText("Tragedy and Hope");
  await expect(panel).toContainText("Why this point connects the threads");
  await panel.getByRole("button", { name: "Close timeline details" }).click();
  await page.getByRole("button", { name: /^Sources/ }).click();
  const source = page.locator(".source-card").filter({
    has: page.getByRole("heading", {
      name: "Tragedy and Hope: A History of the World in Our Time",
      exact: true,
    }),
  });
  await source
    .getByText("Source qualifications & conflicting accounts")
    .click();
  await expect(source).toContainText("bracketed editorial");
  await expect(source).toContainText("1,090-page PDF");
  expect(errors).toEqual([]);
});

test("any person and organization can be compared on aligned entity tracks", async ({
  page,
}) => {
  await page.goto("/?collection=anglo,tragedy");
  await page
    .getByRole("button", {
      name: "People & organization timelines",
      exact: true,
    })
    .click();
  await page.getByLabel("Add timeline entity").selectOption("fw-eggleston");
  await page.getByRole("button", { name: "Add timeline", exact: true }).click();
  await page.getByLabel("Add timeline entity").selectOption("ipr");
  await page.getByRole("button", { name: "Add timeline", exact: true }).click();
  await expect(page.locator(".lane-labels > div")).toHaveCount(2);
  await expect(page.locator(".lane-labels")).toContainText(
    "Frederic Eggleston",
  );
  await expect(page.locator(".lane-labels")).toContainText(
    "Institute of Pacific Relations",
  );
  await expect(page.locator(".lane-labels")).toContainText(
    "Lifespan dates not yet recorded",
  );
  const shared = page.getByRole("button", {
    name: "First listed IPR conference at Honolulu, 1925, year precision",
    exact: true,
  });
  await expect(shared).toHaveCount(2);
  await shared.first().click();
  await expect(page.locator(".highlighted-connection")).not.toHaveCount(0);
  await expect(
    page.getByRole("complementary", { name: "Timeline event details" }),
  ).toContainText("Frederic Eggleston");
  await page.getByRole("button", { name: "Close timeline details" }).click();
  expect(new URL(page.url()).searchParams.get("tracks")).toBe(
    "fw-eggleston,ipr",
  );
  await page.reload();
  await expect(page.locator(".lane-labels > div")).toHaveCount(2);
  const career = page.getByRole("button", {
    name: "Frederic Eggleston · Australian minister in Washington, 1944 – 1946, year precision",
    exact: true,
  });
  await career.click();
  const panel = page.getByRole("complementary", {
    name: "Timeline event details",
  });
  await panel.getByRole("tab", { name: "Source account" }).click();
  await expect(panel).toContainText("diplomatic service");
  await expect(panel).toContainText("The cited biographical footnote");
  await page.screenshot({ path: "/tmp/darktime-entity-tracks.png" });
});

test("record details open a lifecycle timeline with cited birth and death", async ({
  page,
}) => {
  await page.goto("/?collection=tragedy#rhodes");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "View timeline", exact: true })
    .click();
  await expect(page.locator(".lane-labels > div")).toHaveCount(1);
  const birth = page.getByRole("button", {
    name: "Cecil John Rhodes · Birth, 1853, year precision",
    exact: true,
  });
  const death = page.getByRole("button", {
    name: "Cecil John Rhodes · Death, 1902, year precision",
    exact: true,
  });
  await expect(birth).toBeVisible();
  await expect(death).toBeVisible();
  await birth.click();
  const panel = page.getByRole("complementary", {
    name: "Timeline event details",
  });
  await panel.getByRole("tab", { name: "Source account" }).click();
  await expect(panel).toContainText("Only the year is given");
  await expect(panel).toContainText("Tragedy and Hope");
  await expect(
    page.getByRole("button", { name: "Show details", exact: true }),
  ).toBeVisible();
});
