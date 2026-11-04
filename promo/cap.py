# Captures Framey screens + clips for the promo videos. Usage: python3 cap.py <app url> <out dir> [local]
import os, sys, json, random, time
from playwright.sync_api import sync_playwright
URL, OUT = sys.argv[1], sys.argv[2]; LOCAL = len(sys.argv) > 3
D = os.path.dirname(os.path.abspath(__file__)); os.makedirs(OUT, exist_ok=True)
cam = open(D + "/cam3.js").read().replace("const cam=document.createElement('canvas');", "const cam=document.createElement('canvas');window.__cam=cam;")
rnd = random.Random(7)
shakes = [{"x": 0, "y": 0, "a": 0, "s": 1}] + [{"x": rnd.uniform(-45, 45), "y": rnd.uniform(-45, 45), "a": rnd.uniform(-2.5, 2.5), "s": rnd.uniform(0.97, 1.03)} for _ in range(13)]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--disable-gpu", "--renderer-process-limit=1"])
    dev = dict(pw.devices["iPhone 14 Pro Max"]); dev["device_scale_factor"] = 2
    c = b.new_context(**dev)
    if LOCAL:
        css = "@font-face{font-family:'Bricolage Grotesque';font-weight:200 800;src:url(http://localhost:8765/fonts/brico.woff2) format('woff2')}"
        c.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=css))
        c.add_init_script("window.__CV_URL='/opencv.js'")
    c.add_init_script(cam); c.add_init_script("try{localStorage.setItem('framey-tip','no')}catch(e){}")
    p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto(URL); p.evaluate("indexedDB.deleteDatabase('holdstill')"); p.reload(); p.wait_for_timeout(2500)
    shot = lambda n: (p.wait_for_timeout(400), p.screenshot(path=f"{OUT}/{n}.png"))
    p.click('header button:has-text("New movie")'); p.wait_for_timeout(500)
    p.click('button:has-text("Allow camera")'); p.wait_for_timeout(1500)
    p.click('.rail button:has-text("Lock")')
    p.wait_for_function("() => /Locked\\.|Locked to|basic mode/.test((document.querySelector('[role=status]')||{}).textContent||'')", timeout=90000)
    lockmsg = p.locator("[role=status]").first.text_content()
    raws = []
    for i in range(14):
        p.evaluate("(j)=>{window.__shake=j}", shakes[i]); p.wait_for_timeout(250)
        raws.append(p.evaluate("()=>window.__cam.toDataURL('image/jpeg',0.85)"))
        p.click(".shutter"); p.wait_for_timeout(250)
        if i == 5: p.evaluate("()=>{window.__k++}"); p.wait_for_timeout(3600); shot("a_shoot"); continue
        if i < 13: p.evaluate("()=>{window.__k++}"); p.wait_for_timeout(350)
    p.evaluate("()=>{window.__shake={x:0,y:0,a:0,s:1}}")
    get = """async()=>{const g=(k)=>new Promise(ok=>{const o=indexedDB.open('holdstill',1);o.onsuccess=()=>{const q=o.result.transaction('p').objectStore('p').get(k);q.onsuccess=()=>ok(q.result)}});
      const r=await g('projects');const d=await g('proj:'+r[0].id);
      const wav=await new Promise(ok=>{const fr=new FileReader();fr.onload=()=>ok(fr.result);fr.readAsDataURL(synthTrack('bouncy'))});
      return {frames:d.frames.map(f=>f.src),wav};}"""
    p.wait_for_timeout(2500)
    data = p.evaluate(get); data["raw"] = raws; data["lockmsg"] = lockmsg
    json.dump(data, open(f"{OUT}/final.json", "w")); print("final.json saved", flush=True)
    # draw on a frame
    p.click(".th >> nth=9"); p.wait_for_timeout(400); p.click('.acts button:has-text("Draw")'); p.wait_for_timeout(700)
    bx = p.locator(".drawcv").bounding_box()
    p.click('.over button[aria-label="Color #FFFFFF"]'); p.click('.over button:has-text("Thick")')
    for x0, y0, x1, y1 in [[0.16, 0.44, 0.36, 0.45], [0.14, 0.52, 0.34, 0.53], [0.18, 0.6, 0.35, 0.6]]:
        p.mouse.move(bx["x"] + bx["width"] * x0, bx["y"] + bx["height"] * y0); p.mouse.down()
        p.mouse.move(bx["x"] + bx["width"] * x1, bx["y"] + bx["height"] * y1, steps=10); p.mouse.up()
    p.click('.over button[aria-label="Color #FFD60A"]'); p.click('.over button:has-text("Medium")')
    for cx, cy in [[0.62, 0.3], [0.7, 0.24], [0.56, 0.22]]:
        X, Y = bx["x"] + bx["width"] * cx, bx["y"] + bx["height"] * cy
        for dx, dy in [[-14, 0], [0, -14]]:
            p.mouse.move(X + dx, Y + dy); p.mouse.down(); p.mouse.move(X - dx, Y - dy, steps=4); p.mouse.up()
    shot("b_draw"); p.click('.over button:has-text("Save")'); p.wait_for_timeout(500)
    p.click('.acts button:has-text("Camera")'); p.wait_for_timeout(200)
    # title card
    p.click('button.tool:has-text("Settings")'); p.wait_for_timeout(400)
    p.click('.sheet button:has-text("Add title card")'); p.wait_for_timeout(500)
    p.fill(".ttext", "The Big Hop"); p.click('.over button[aria-label="Background #FE6100"]'); shot("c_title")
    p.click('.over button:has-text("Add")'); p.wait_for_timeout(500)
    # song search with the movie playing along
    p.click('header button:has-text("Create video")'); p.wait_for_timeout(500)
    p.click('button:has-text("Yes, find a song")'); p.wait_for_timeout(600); p.evaluate("()=>document.activeElement.blur()")
    p.click('.srow >> nth=0 >> button:has-text("Play")'); p.wait_for_timeout(2600); shot("song")
    p.click('.over button:has-text("Back")'); p.wait_for_timeout(300)
    # movie 2: green screen in space
    p.click('header button:has-text("Movies")'); p.wait_for_timeout(700)
    p.click('header button:has-text("New movie")'); p.wait_for_timeout(500)
    p.evaluate("()=>{window.__green=true;window.__k=3;window.__vis=3}")
    p.click('button:has-text("Allow camera")'); p.wait_for_timeout(1500)
    for i in range(5):
        p.click(".shutter"); p.wait_for_timeout(200); p.evaluate("()=>{window.__k++}"); p.wait_for_timeout(450)
    p.click('button.tool:has-text("Settings")'); p.wait_for_timeout(400)
    p.set_input_files('input[type=file][accept="image/*"]:not([multiple])', D + "/space.png"); p.wait_for_timeout(1000)
    p.locator('.sheet button:has-text("Done")').click(); p.wait_for_timeout(300)
    p.click('button.tool:has-text("Preview")'); p.wait_for_timeout(1800)
    p.click('.over button:has-text("Pause")'); p.locator(".over input[type=range]").first.fill("2"); shot("g_green")
    print(json.dumps({"lockmsg": lockmsg, "frames": len(data["frames"]), "raw": len(raws), "errs": errs}))
    b.close()
