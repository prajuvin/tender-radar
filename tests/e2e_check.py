"""Browser check against real data: run `python -m radar.fetch` first, then `python tests/e2e_check.py`.
Serves docs/ locally, drives the app like a user, and checks that the website's matches equal the Python matcher's."""
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from radar.match import match

data = json.loads((ROOT / "docs/data/tenders.json").read_text())["tenders"]
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "-d", str(ROOT / "docs")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
fails = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for width in (390, 1280):
            pg = b.new_page(viewport={"width": width, "height": 900})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto("http://localhost:8765/")
            pg.wait_for_function("document.getElementById('fresh').textContent.indexOf('open tenders')>-1")
            cases = [(["cleaning", "printing"], "ontario"), (["software"], "anywhere"), (["snow"], "ncr"), (["zzqxv"], "ontario")]
            for words, where in cases:
                pg.evaluate("localStorage.clear()")
                pg.goto(f"http://localhost:8765/?words={','.join(words)}&where={where}")
                pg.wait_for_function("document.getElementById('fresh').textContent.indexOf('open tenders')>-1")
                pg.click("#to2")
                heading = pg.inner_text("#mh")
                expected = len(match(data, words, where))
                got = 0 if heading.startswith("No matches") else int(heading.split()[0])
                if got != expected:
                    fails.append(f"{width}px {words}/{where}: page {got} vs python {expected}")
                print(f"{width}px {words}/{where}: {got} (python {expected})")
            # user flow: add an idea chip, bad input error, show more, keep step
            pg.goto("http://localhost:8765/?words=software&where=anywhere")
            pg.wait_for_function("document.getElementById('fresh').textContent.indexOf('open tenders')>-1")
            pg.fill("#word", "a"); pg.click("#addForm button")
            if pg.is_hidden("#wordErr"): fails.append("short word shows no error")
            pg.click(".idea >> text=training")
            pg.click("#to2")
            if pg.is_visible("#more"):
                before = pg.locator("article.tender").count(); pg.click("#more")
                if pg.locator("article.tender").count() <= before: fails.append("show more did nothing")
            links = pg.eval_on_selector_all("article.tender a.open", "a=>a.map(x=>x.href)")
            if not links or not all(l.startswith("https://") for l in links): fails.append("bad notice links")
            pg.click("#t3")
            if "words=software%2Ctraining" not in pg.input_value("#share"): fails.append("share link missing words: " + pg.input_value("#share"))
            if "open tender" not in pg.input_value("#digest"): fails.append("digest empty")
            overflow = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            if overflow: fails.append(f"horizontal scroll at {width}px")
            pg.click("#t2"); pg.screenshot(path=f"/tmp/tr_real_{width}.png", full_page=False)
            if errs: fails.append(f"JS errors: {errs}")
        b.close()
finally:
    srv.terminate()
print("FAILURES:" if fails else "ALL CHECKS PASSED", *fails, sep="\n")
sys.exit(1 if fails else 0)
