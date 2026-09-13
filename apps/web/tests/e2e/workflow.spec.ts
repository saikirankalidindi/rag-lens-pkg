import { test, expect } from "@playwright/test";
import { randomUUID } from "node:crypto";
import { appendFileSync } from "node:fs";

const api = process.env.E2E_API_URL ?? "http://localhost:8000";

// Run against a disposable stack: the workflow creates an account and its data.
test("account, project, settings, keys, traces, filters and session lifecycle", async ({ page, request }) => {
  const email = `web-review-${randomUUID()}@example.com`;
  if (process.env.E2E_ACCOUNT_LOG) appendFileSync(process.env.E2E_ACCOUNT_LOG, email + "\n");
  const password = randomUUID();
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/register");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(page.getByText("No projects yet", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Create Project", exact: true }).click();
  await page.getByLabel("Project name", { exact: true }).fill("Browser verification");
  await page.getByLabel("Description (optional)").fill("Created through the web interface");
  await page.getByRole("dialog").getByRole("button", { name: "Create Project", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/proj[^/]+$/);
  const projectUrl = page.url();
  const pid = projectUrl.split("/").at(-1)!;
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  await expect(page.getByText("Total traces", { exact: true })).toBeVisible();
  await expect(page.getByRole("img", { name: /Requests over time/ })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Switch project" }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await page.getByRole("button", { name: "New Project", exact: true }).click();
  await page.getByLabel("Project name", { exact: true }).fill("  browser   VERIFICATION ");
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("already exists");
  await expect(page.getByRole("dialog").getByRole("button", { name: "Create Project", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.getByRole("textbox", { name: "Search projects", exact: true }).fill("missing project");
  await expect(page.getByText(/No projects match/)).toBeVisible();
  await page.getByRole("button", { name: "Clear search", exact: true }).first().click();
  await page.getByRole("button", { name: /Browser verification/ }).click();
  await expect(page).toHaveURL(projectUrl);

  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page.getByLabel("Project name", { exact: true }).fill("Browser verification updated");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("link", { name: "Switch project" })).toContainText("Browser verification updated");
  await page.reload();
  await expect(page.getByLabel("Project name", { exact: true })).toHaveValue("Browser verification updated");

  await page.getByRole("link", { name: "API Keys", exact: true }).click();
  await page.getByRole("button", { name: "Create API Key", exact: true }).click();
  await page.getByLabel("Key Name").fill("Browser test key");
  await page.getByRole("button", { name: "Create Key", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(1);
  await expect(page.getByRole("dialog")).toContainText("API Key Created");
  const key = await page.getByRole("dialog").locator("code").textContent();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByText(key!, { exact: true })).toHaveCount(0);

  const started = new Date().toISOString();
  const traceResponse = await request.post(`${api}/v1/traces`, {
    headers: { Authorization: `Bearer ${key}` }, data: {
      name: "Browser trace", started_at: started, ended_at: started, duration_ms: 1000,
      input: { query: "browser query" }, output: { answer: "browser answer" },
      metadata: { environment: "development" }, metrics: { input_tokens: 100, output_tokens: 10, total_tokens: 110 },
      spans: [{ id: `span_${randomUUID()}`, type: "retrieval", name: "browser retrieval", started_at: started, duration_ms: 600,
        retrieval_results: [{ rank: 1, chunk_id: "chunk", document_id: "doc", document_name: "Browser document", content: "Browser content", score: 0.2, selected: true }] }],
    },
  });
  expect(traceResponse.status()).toBe(201);
  for (let i = 0; i < 25; i++) {
    const result = await request.post(`${api}/v1/traces`, { headers: { Authorization: `Bearer ${key}` }, data: {
      name: `pagination ${i}`, started_at: started, duration_ms: i + 1,
      metadata: { environment: "development" }, metrics: { total_tokens: 1 },
    } });
    expect(result.status()).toBe(201);
  }
  const token = await page.evaluate(() => localStorage.getItem("raglens_token"));
  const stats = await request.get(`${api}/projects/${pid}/stats`, { headers: { Authorization: `Bearer ${token}` } });
  expect(stats.status()).toBe(200);
  const totals = await stats.json();
  expect(totals.total_traces).toBe(26);
  expect(totals.total_tokens).toBe(135);
  expect(totals.activity.reduce((n: number, day: { requests: number }) => n + day.requests, 0)).toBe(26);
  expect(totals.latency_buckets.reduce((n: number, bucket: { count: number }) => n + bucket.count, 0)).toBe(26);
  await page.getByRole("link", { name: "Traces", exact: true }).click();
  await page.getByLabel("Sort traces").selectOption("slowest");
  await expect(page.getByRole("link", { name: /browser query/ })).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("Page 2 of 2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Prev", exact: true }).click();
  await expect(page.getByText("Page 1 of 2", { exact: true })).toBeVisible();
  await page.getByLabel("Status filter").selectOption("error");
  await expect(page.getByText("No traces match your filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await page.getByLabel("From date").fill("2099-01-01");
  await expect(page.getByText("No traces match your filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await page.getByLabel("Environment filter").selectOption("production");
  await expect(page.getByText("No traces match your filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await page.getByPlaceholder("Search traces…").fill("missing query");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByText("No traces match your filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await page.getByRole("link", { name: /browser query/ }).click();
  await expect(page.getByText("Low retrieval confidence", { exact: true })).toBeVisible();
  await expect(page.getByText("Browser document", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "API Keys", exact: true }).click();
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Revoke Browser test key", exact: true }).click();
  await expect(page.getByText("Revoked", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Revoked", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Documentation", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Instrument your RAG pipeline." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Give every pipeline stage a span" })).toBeVisible();
  await page.getByRole("link", { name: "Back to projects" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto(projectUrl);
  await expect(page).toHaveURL(/\/login\?returnUrl=/);
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(projectUrl);
  await page.getByRole("link", { name: "Switch project" }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await page.route(`${api}/projects`, route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: { message: "Temporary project service failure" } }) }));
  await page.reload();
  await expect(page.getByRole("alert").filter({ hasText: "Temporary project service failure" })).toBeVisible();
  await page.unroute(`${api}/projects`);
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("button", { name: /Browser verification updated/ })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "/tmp/raglens-projects-mobile.png", fullPage: true });
  expect(errors).toEqual([]);
});

test("all seven seed traces and their inspectors render", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill("demo@raglens.dev");
  await page.getByLabel("Password", { exact: true }).fill("raglens-demo");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(page.getByRole("button", { name: /HR Knowledge Base/ })).toBeVisible();
  await page.screenshot({ path: "/tmp/raglens-workspace-desktop.png", fullPage: true });
  const token = await page.evaluate(() => localStorage.getItem("raglens_token"));
  const headers = { Authorization: `Bearer ${token}` };
  const projects = await (await request.get(`${api}/projects`, { headers })).json();
  const project = projects.find((p: { name: string }) => p.name === "HR Knowledge Base");
  expect(project).toBeTruthy();
  const traces = await (await request.get(`${api}/projects/${project.id}/traces`, { headers })).json();
  expect(traces.items.length).toBeGreaterThanOrEqual(7);
  for (const item of traces.items) {
    const trace = await (await request.get(`${api}/projects/${project.id}/traces/${item.id}`, { headers })).json();
    await page.goto(`/projects/${project.id}/traces/${item.id}`);
    for (const span of trace.spans) {
      const button = page.getByRole("button", { name: `Inspect ${span.name}`, exact: true });
      await button.click();
      await expect(button).toHaveAttribute("aria-pressed", "true");
      if (span.type === "reranking") await expect(page.getByText("Reranking Analysis", { exact: true })).toBeVisible();
    }
    const linked = trace.diagnostics.find((d: { span_id: string }) => d.span_id);
    if (linked) {
      await page.getByRole("button").filter({ hasText: linked.title }).click();
      const linkedSpan = trace.spans.find((s: { id: string }) => s.id === linked.span_id);
      await expect(page.getByRole("button", { name: `Inspect ${linkedSpan.name}`, exact: true })).toHaveAttribute("aria-pressed", "true");
    }
  }
  await page.goto(`/projects/${project.id}`);
  await expect(page.getByRole("img", { name: /Requests over time/ })).toBeVisible();
  await page.screenshot({ path: "/tmp/raglens-overview-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Project navigation").selectOption(`/projects/${project.id}/traces`);
  await expect(page.getByPlaceholder("Search traces…")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "/tmp/raglens-traces-mobile.png", fullPage: true });
  expect(errors).toEqual([]);
});
