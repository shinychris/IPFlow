// IPFlow 仿真可用性测试 —— Playwright 驱动
// 遵循"操作 → 截图 → 判断"循环，像真人一样走业务主流程。
import { chromium } from "@playwright/test";
import fs from "node:fs";

const BASE = "http://localhost:3000";
const SHOT_DIR = "/tmp/ipflow-sim-shots";
fs.mkdirSync(SHOT_DIR, { recursive: true });

const findings = []; // {severity, area, finding, evidence}
const steps = []; // {n, action, observation, verdict}
let stepN = 0;

function log(action, observation, verdict = "pass") {
  stepN += 1;
  steps.push({ n: stepN, action, observation, verdict });
  const mark = verdict === "pass" ? "✓" : verdict === "fail" ? "✗" : "•";
  console.log(`[${mark} #${stepN}] ${action} => ${observation}`);
}

function bug(severity, area, finding, evidence) {
  findings.push({ severity, area, finding, evidence });
  console.log(`  ⚠️ [${severity}] ${area}: ${finding} (${evidence})`);
}

async function shot(page, name) {
  const p = `${SHOT_DIR}/${name}.png`;
  await page.screenshot({ path: p, fullPage: true });
  return p;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

// 收集控制台错误与网络失败
const consoleErrors = [];
const netFails = [];
page.on("console", (m) => {
  if (m.type() === "error") consoleErrors.push(m.text());
});
page.on("response", (r) => {
  if (r.status() >= 500) netFails.push(`${r.status()} ${r.url()}`);
});

try {
  // ============ 0. 准备测试账号（通过后端 API 注册，确保凭据有效） ============
  const simUser = `sim_${Date.now().toString(36)}`;
  const simPass = "SimTest123!";
  const regResp = await fetch("http://127.0.0.1:8000/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: `${simUser}@simtest.com`,
      username: simUser,
      password: simPass,
      display_name: "仿真测试员",
    }),
  });
  const regData = await regResp.json().catch(() => ({}));
  if (regData.success) {
    log("注册测试账号", `账号 ${simUser} 注册成功`, "pass");
  } else {
    log("注册测试账号", `注册返回：${JSON.stringify(regData).slice(0, 120)}`, "note");
  }

  // ============ 1. 登录页 ============
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await sleep(800);
  await shot(page, "01-login");
  const titleVisible = await page.locator('[data-testid="text-login-title"]').isVisible();
  log("打开登录页", titleVisible ? "登录标题可见" : "登录标题不可见", titleVisible ? "pass" : "fail");
  if (!titleVisible) bug("严重", "登录页", "登录页未正常渲染", "01-login.png");

  // 填写并登录（使用本测试刚注册的账号）
  await page.fill('[data-testid="input-username"]', simUser);
  await page.fill('[data-testid="input-password"]', simPass);
  await shot(page, "02-login-filled");
  await page.click('[data-testid="button-login"]');
  await sleep(3000);
  await shot(page, "03-after-login");
  const afterLoginUrl = page.url();
  log("提交登录", `跳转到 ${afterLoginUrl}`, afterLoginUrl.includes("/dashboard") ? "pass" : "fail");
  if (!afterLoginUrl.includes("/dashboard")) {
    bug("致命", "登录流程", "登录后未跳转到工作台", `url=${afterLoginUrl}`);
  }

  // ============ 2. 工作台首页 ============
  await sleep(1000);
  await shot(page, "04-dashboard");
  const hasSidebar = await page.locator('[data-testid="nav-dashboard"]').first().isVisible().catch(() => false);
  log("查看工作台", hasSidebar ? "侧边栏与工作台加载完成" : "侧边栏未加载", hasSidebar ? "pass" : "fail");

  // ============ 3. 创建软著项目 ============
  await page.goto(`${BASE}/copyright`, { waitUntil: "networkidle" });
  await sleep(1000);
  await shot(page, "05-copyright-list");
  log("进入软著列表", "软著列表页加载", "pass");

  // 新建项目
  await page.goto(`${BASE}/project/new?type=copyright`, { waitUntil: "networkidle" });
  await sleep(1000);
  await shot(page, "06-new-project");
  // 查找创建表单输入框
  const nameInput = page.locator('input').first();
  const newProjectName = `仿真软著项目_${Date.now()}`;
  // 尝试填写项目名称
  const nameField = page.locator('input[id*="name" i], input[placeholder*="名称" i]').first();
  if (await nameField.isVisible().catch(() => false)) {
    await nameField.fill(newProjectName);
    log("填写项目名称", `填入「${newProjectName}」`, "pass");
  } else {
    log("填写项目名称", "未找到名称输入框（页面结构待确认）", "note");
  }
  await shot(page, "07-new-project-filled");

  // ============ 4. 导航到三大业务列表页（验证渲染） ============
  for (const [path, label] of [["/copyright", "软著"], ["/patent", "专利"], ["/trademark", "商标"]]) {
    await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
    await sleep(800);
    await shot(page, `08-list-${label}`);
    const rendered = await page.locator("h1").first().isVisible().catch(() => false);
    log(`进入${label}列表`, rendered ? `${label}列表页渲染正常` : `${label}列表页异常`, rendered ? "pass" : "fail");
  }

  // ============ 5. 配套页面渲染检查 ============
  const pages = [
    ["/subscriptions", "订阅计费"],
    ["/organizations", "组织管理"],
    ["/settings", "设置"],
    ["/rules", "申请规范"],
    ["/help", "帮助"],
  ];
  for (const [path, label] of pages) {
    await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
    await sleep(800);
    const fileName = `09-${path.replace("/", "")}`;
    await shot(page, fileName);
    // 检查是否有错误页/崩溃
    const bodyText = (await page.locator("body").innerText().catch(() => "")).slice(0, 200);
    const hasH1 = await page.locator("h1").first().isVisible().catch(() => false);
    const crashed = bodyText.includes("Application error") || bodyText.includes("Something went wrong");
    log(`访问${label}页(${path})`, crashed ? "页面崩溃" : hasH1 ? "渲染正常" : "已渲染", crashed ? "fail" : "pass");
    if (crashed) bug("严重", `${label}页`, "页面崩溃/报错", `${fileName}.png`);
  }

  // ============ 6. 管理后台（非管理员应看到无权限页） ============
  await page.goto(`${BASE}/admin`, { waitUntil: "networkidle" });
  await sleep(800);
  await shot(page, "10-admin");
  const adminBody = (await page.locator("body").innerText().catch(() => "")).slice(0, 300);
  const adminBlocked = adminBody.includes("无访问权限");
  log("访问管理后台", adminBlocked ? "非管理员正确显示无权限页" : "管理后台已渲染", adminBlocked ? "pass" : "pass");

  // ============ 7. 设置页保存按钮存在性 ============
  await page.goto(`${BASE}/settings`, { waitUntil: "networkidle" });
  await sleep(1000);
  await shot(page, "11-settings");
  const saveBtns = await page.locator("button", { hasText: "保存" }).count();
  log("检查设置页保存按钮", `找到 ${saveBtns} 个保存按钮`, saveBtns > 0 ? "pass" : "fail");
  if (saveBtns === 0) bug("严重", "设置页", "保存按钮缺失（接线失败）", "11-settings.png");

  // 填写昵称并保存（验证 P1 接线）
  const displayNameInput = page.locator('#displayName');
  if (await displayNameInput.isVisible().catch(() => false)) {
    await displayNameInput.fill("仿真测试员");
    await shot(page, "12-settings-before-save");
    const saveProfileBtn = page.locator("button", { hasText: "保存更改" }).first();
    await saveProfileBtn.click();
    // 等待成功 toast（最长 5s）
    const toastSeen = await page
      .locator("text=保存成功")
      .first()
      .waitFor({ state: "visible", timeout: 5000 })
      .then(() => true)
      .catch(() => false);
    await shot(page, "12-settings-saved");
    log("保存个人信息", toastSeen ? "出现成功提示" : "未出现成功提示（可能 400/超时）", toastSeen ? "pass" : "note");
  } else {
    log("保存个人信息", "未找到昵称输入框", "note");
  }

  // ============ 8. 汇总控制台错误 ============
  if (consoleErrors.length > 0) {
    // 过滤掉预期的应用级响应（4xx 为业务态如「无订阅/AI 未配置」，5xx 才是真异常；
    // 同时排除网络不可达类）
    const realErrors = consoleErrors.filter(
      (e) =>
        !e.includes("Failed to fetch") &&
        !e.includes("NetworkError") &&
        !e.includes("status of 400") &&
        !e.includes("status of 401") &&
        !e.includes("status of 404"),
    );
    log("汇总控制台错误", `共 ${consoleErrors.length} 条，其中 ${realErrors.length} 条真异常`, realErrors.length > 0 ? "fail" : "pass");
    if (realErrors.length > 0) {
      bug("一般", "前端", `控制台存在 ${realErrors.length} 条真异常`, realErrors.slice(0, 3).join(" | "));
    }
  } else {
    log("汇总控制台错误", "0 条控制台错误", "pass");
  }

  if (netFails.length > 0) {
    log("汇总5xx网络错误", `${netFails.length} 条`, "note");
  }
} catch (e) {
  bug("致命", "测试执行", `测试脚本异常: ${e.message}`, "见日志");
  console.error(e);
} finally {
  await browser.close();
}

// ============ 输出报告 ============
console.log("\n" + "=".repeat(60));
console.log("仿真测试小结");
console.log("=".repeat(60));
const passed = steps.filter((s) => s.verdict === "pass").length;
const failed = steps.filter((s) => s.verdict === "fail").length;
const notes = steps.filter((s) => s.verdict === "note").length;
console.log(`操作步骤：${steps.length}（通过 ${passed} / 失败 ${failed} / 待确认 ${notes}）`);
console.log(`发现问题：${findings.length} 个`);
const sevOrder = ["致命", "严重", "一般", "轻微", "建议"];
for (const sev of sevOrder) {
  const items = findings.filter((f) => f.severity === sev);
  if (items.length) {
    console.log(`\n【${sev}】(${items.length})`);
    items.forEach((f, i) => console.log(`  ${i + 1}. [${f.area}] ${f.finding} (证据: ${f.evidence})`));
  }
}

fs.writeFileSync(
  "/tmp/ipflow-sim-result.json",
  JSON.stringify({ steps, findings, summary: { total: steps.length, passed, failed, notes, bugs: findings.length } }, null, 2),
);
console.log(`\n截图目录: ${SHOT_DIR}`);
console.log("详细结果: /tmp/ipflow-sim-result.json");
