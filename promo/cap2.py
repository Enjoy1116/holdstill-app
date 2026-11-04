# Extra clips for feature videos: green-screen before/after frames. Usage: python3 cap2.py <app url> <out dir> [local]
import os, sys, json, base64
from playwright.sync_api import sync_playwright
URL, OUT = sys.argv[1], sys.argv[2]; LOCAL = len(sys.argv) > 3
D = os.path.dirname(os.path.abspath(__file__)); os.makedirs(OUT, exist_ok=True)
cam = open(D + "/cam3.js").read().replace("const cam=document.createElement('canvas');", "const cam=document.createElement('canvas');window.__cam=cam;")
space = "data:image/png;base64," + base64.b64encode(open(D + "/space.png", "rb").read()).decode()
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--disable-gpu", "--renderer-process-limit=1"])
    dev = dict(pw.devices["iPhone 14 Pro Max"]); dev["device_scale_factor"] = 2
    c = b.new_context(**dev)
    if LOCAL:
        css = "@font-face{font-family:'Bricolage Grotesque';font-weight:200 800;src:url(http://localhost:8765/fonts/brico.woff2) format('woff2')}"
        c.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=css))
    c.add_init_script(cam); c.add_init_script("try{localStorage.setItem('framey-tip','no')}catch(e){}")
    p = c.new_page(); errs = []; p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto(URL); p.evaluate("indexedDB.deleteDatabase('holdstill')"); p.reload(); p.wait_for_timeout(2500)
    getf = """async()=>{const g=(k)=>new Promise(ok=>{const o=indexedDB.open('holdstill',1);o.onsuccess=()=>{const q=o.result.transaction('p').objectStore('p').get(k);q.onsuccess=()=>ok(q.result)}});
      const r=await g('projects');const d=await g('proj:'+r[0].id);return d.frames.map(f=>f.src)}"""
    # 1) a clean movie: phone held perfectly still
    p.click('header button:has-text("New movie")'); p.wait_for_timeout(500)
    p.click('button:has-text("Allow camera")'); p.wait_for_timeout(1500)
    for i in range(14):
        p.click(".shutter"); p.wait_for_timeout(200)
        if i < 13: p.evaluate("()=>{window.__k++}"); p.wait_for_timeout(400)
    p.wait_for_timeout(1500); clean = p.evaluate(getf)
    p.click('header button:has-text("Movies")'); p.wait_for_timeout(700)
    # 2) the same scene in front of green paper
    p.click('header button:has-text("New movie")'); p.wait_for_timeout(500)
    p.evaluate("()=>{window.__green=true;window.__k=0;window.__vis=0}")
    p.click('button:has-text("Allow camera")'); p.wait_for_timeout(1500)
    for i in range(14):
        p.click(".shutter"); p.wait_for_timeout(200)
        if i < 13: p.evaluate("()=>{window.__k++}"); p.wait_for_timeout(400)
    p.wait_for_timeout(1500)
    data = p.evaluate("""async(bgsrc)=>{const g=(k)=>new Promise(ok=>{const o=indexedDB.open('holdstill',1);o.onsuccess=()=>{const q=o.result.transaction('p').objectStore('p').get(k);q.onsuccess=()=>ok(q.result)}});
      const r=await g('projects');const d=await g('proj:'+r[0].id);const srcs=d.frames.map(f=>f.src);
      // use Framey's own green-screen code on these photos
      const bc=document.createElement('canvas');bc.width=W;bc.height=H;cover(bc.getContext('2d'),await loadImg(bgsrc));
      const ims=await Promise.all(srcs.map(loadImg));
      const look=await prepareLook({imgs:ims,deflicker:false,chroma:true,chromaBg:bc.toDataURL('image/jpeg',0.9),chromaTol:0.5});
      const c=document.createElement('canvas');c.width=W;c.height=H;const gg=c.getContext('2d',{willReadFrequently:true});
      const keyed=[];for(let i=0;i<ims.length;i++){renderFrame(gg,ims[i],i,look,0);keyed.push(c.toDataURL('image/jpeg',0.85))}
      return {green:srcs,keyed};}""", space)
    data["clean"] = clean
    json.dump(data, open(f"{OUT}/green.json", "w"))
    print(json.dumps({"clean": len(clean), "green": len(data["green"]), "keyed": len(data["keyed"]), "errs": errs}))
    b.close()
