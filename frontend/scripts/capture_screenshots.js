import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const outputDir = path.resolve("..", "screenshots");

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

async function run() {
  console.log("Launching Edge headless browser...");
  const browser = await puppeteer.launch({
    executablePath: edgePath,
    headless: true,
    defaultViewport: { width: 1440, height: 900 },
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
  });

  try {
    const page = await browser.newPage();
    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    page.on("pageerror", (err) => console.log("PAGE ERROR:", err.message));

    console.log("Navigating to http://127.0.0.1:5173/ ...");
    await page.goto("http://127.0.0.1:5173/", { waitUntil: "domcontentloaded", timeout: 15000 });
    await new Promise((r) => setTimeout(r, 2000));

    // Fallback screenshot to inspect what is rendered
    await page.screenshot({ path: path.join(outputDir, "00_initial_state.png") });

    // Wait for incidents list
    await page.waitForSelector(".incident-card", { timeout: 10000 });
    console.log("Incidents loaded successfully.");

    // Screenshot 1: Dashboard Overview
    const s1Path = path.join(outputDir, "01_dashboard_overview.png");
    await page.screenshot({ path: s1Path, fullPage: false });
    console.log("Saved screenshot 1 to:", s1Path);

    // Switch to Overview tab
    const tabs = await page.$$(".tab-btn");
    if (tabs.length >= 2) {
      await tabs[1].click();
      await new Promise((r) => setTimeout(r, 600));
      const s2Path = path.join(outputDir, "02_incident_telemetry.png");
      await page.screenshot({ path: s2Path, fullPage: false });
      console.log("Saved screenshot 2 to:", s2Path);

      // Switch back to Investigation tab
      await tabs[0].click();
      await new Promise((r) => setTimeout(r, 600));
    }

    // Click "Investigate Incident" button
    console.log("Triggering Investigate Incident button...");
    const buttons = await page.$$("button");
    let investigateBtn = null;
    for (const b of buttons) {
      const text = await page.evaluate((el) => el.textContent, b);
      if (text && text.includes("Investigate Incident")) {
        investigateBtn = b;
        break;
      }
    }
    if (investigateBtn) {
      await investigateBtn.click();
      console.log("Clicked Investigate Incident button.");
    } else {
      console.warn("Could not find Investigate Incident button!");
    }

    // Wait for investigation result to appear
    await page.waitForSelector(".investigation-container", { timeout: 20000 });
    console.log("Investigation result rendered!");
    await new Promise((r) => setTimeout(r, 1000));

    // Screenshot 3: Investigation Result Top
    const s3Path = path.join(outputDir, "03_investigation_result.png");
    await page.screenshot({ path: s3Path, fullPage: false });
    console.log("Saved screenshot 3 to:", s3Path);

    // Scroll down to show Hypotheses and Remediation
    await page.evaluate(() => {
      const hList = document.querySelector(".hypothesis-list");
      if (hList) {
        hList.scrollIntoView();
      } else {
        const el = document.querySelector(".detail-panel");
        if (el) el.scrollTop = el.scrollHeight;
      }
    });
    await new Promise((r) => setTimeout(r, 600));

    const s4Path = path.join(outputDir, "04_investigation_hypotheses_remediation.png");
    await page.screenshot({ path: s4Path, fullPage: false });
    console.log("Saved screenshot 4 to:", s4Path);

  } catch (err) {
    console.error("Error during screenshot capture:", err);
  } finally {
    await browser.close();
    console.log("Browser closed.");
  }
}

run();
