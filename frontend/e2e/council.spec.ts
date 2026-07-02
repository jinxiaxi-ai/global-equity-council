import { expect, type Page, test } from "@playwright/test";

const markets = [
  ["AAPL", "Apple Inc.", "USD", "America/New_York"],
  ["600519.SS", "Kweichow Moutai", "CNY", "Asia/Shanghai"],
  ["0700.HK", "Tencent Holdings", "HKD", "Asia/Hong_Kong"],
  ["7203.T", "Toyota Motor", "JPY", "Asia/Tokyo"],
] as const;

function monitorBrowser(page: Page) {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("requestfailed", (request) => {
    if (request.url().includes("/api/")) {
      errors.push(
        `request: ${request.url()} ${request.failure()?.errorText ?? ""}`,
      );
    }
  });
  return () => expect(errors).toEqual([]);
}

test("five-market credential-free research flows expose provenance", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name.includes("mobile"),
    "desktop market-matrix test",
  );
  test.setTimeout(90_000);
  const expectCleanBrowser = monitorBrowser(page);
  await page.goto("/");
  await expect(
    page.getByRole("article", { name: /Apple Inc. research report/ }),
  ).toBeVisible();
  for (const [query, company, currency, timezone] of markets) {
    await page.getByRole("button", { name: query }).click();
    await expect(
      page.getByRole("heading", { name: new RegExp(company) }).first(),
    ).toBeVisible();
    await expect(page.getByText(new RegExp(`${currency} /`))).toBeVisible();
    await expect(page.getByText(timezone)).toBeVisible();
    await expect(
      page.getByText(/数据模式: fixture|Data mode: fixture/),
    ).toBeVisible();
    await expect(
      page
        .getByRole("link", { name: /Annual|Form|Investor|SEC|Stock Exchange/ })
        .first(),
    ).toHaveAttribute("href", /^https:\/\//);
  }
  await page.getByRole("button", { name: "SAP" }).click();
  await expect(
    page.getByRole("dialog", { name: /选择上市地|Choose a listing/ }),
  ).toBeVisible();
  await expect(page.getByText("Xetra · XETR · Germany")).toBeVisible();
  await page
    .getByRole("button", {
      name: "SA SAP · SAP SE Xetra · XETR · Germany EUR Primary",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("heading", { name: "SAP SE" }).first(),
  ).toBeVisible();
  await expect(page.getByText("Europe/Berlin")).toBeVisible();
  expectCleanBrowser();
});

test("language, theme, currency and share-card interactions work", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name.includes("mobile"),
    "desktop interaction test",
  );
  const expectCleanBrowser = monitorBrowser(page);
  await page.goto("/");
  await expect(
    page.getByRole("article", { name: /Apple Inc. research report/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Switch to English" }).click();
  await expect(page.getByText("Investment memo")).toBeVisible();
  await page.getByLabel("Base currency").selectOption("CNY");
  await expect(page.getByText(/1 USD = 7.2993 CNY/)).toBeVisible();
  await page.getByRole("button", { name: "Dark mode" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: /Create share card/ }).click();
  await expect(
    page.getByRole("dialog", { name: "Create share card" }),
  ).toBeVisible();
  await expect(
    page.getByText("Research & education only · Not investment advice"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  expectCleanBrowser();
});

test("mobile layout has no horizontal page overflow", async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.includes("mobile"), "mobile-only assertion");
  const expectCleanBrowser = monitorBrowser(page);
  await page.goto("/");
  await expect(
    page.getByRole("article", { name: /Apple Inc. research report/ }),
  ).toBeVisible();
  const dimensions = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(
    dimensions.clientWidth + 1,
  );
  await expect(
    page.getByRole("button", { name: /召集委员会|Convene council/ }),
  ).toBeVisible();
  expectCleanBrowser();
});
