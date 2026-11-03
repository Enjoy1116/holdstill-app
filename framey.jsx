// Framey: a free stop-motion studio in the browser. Plain React (global React/ReactDOM), no build step needed at runtime.
const { useState, useRef, useEffect, useMemo } = React;

let W = 800, H = 1200;
const RATIOS = { tall: [720, 1280], square: [1080, 1080], wide: [1280, 720] };
const LABELS = { fit: "Fit screen", tall: "Tall 9:16", square: "Square", wide: "Wide 16:9" };
const DEFAULTS = { frames: [], fps: 8, ratio: "fit", dims: [800, 1200], voice: null, deflicker: true, pingpong: false };
const uid = () => Math.random().toString(36).slice(2, 9);

// ---------- storage (same database name as before, so old work is kept) ----------
const dbOpen = () => new Promise((ok, no) => {
  const o = indexedDB.open("holdstill", 1);
  o.onupgradeneeded = () => o.result.createObjectStore("p");
  o.onerror = () => no(o.error);
  o.onsuccess = () => ok(o.result);
});
const dbGet = async (k) => {
  const d = await dbOpen();
  return new Promise((ok, no) => {
    const r = d.transaction("p", "readonly").objectStore("p").get(k);
    r.onsuccess = () => ok(r.result);
    r.onerror = () => no(r.error);
  });
};
const dbPut = async (k, v) => {
  const d = await dbOpen();
  return new Promise((ok, no) => {
    const t = d.transaction("p", "readwrite");
    t.objectStore("p").put(v, k);
    t.oncomplete = () => ok();
    t.onerror = () => no(t.error);
  });
};
const dbDel = async (k) => {
  const d = await dbOpen();
  return new Promise((ok) => {
    const t = d.transaction("p", "readwrite");
    t.objectStore("p").delete(k);
    t.oncomplete = () => ok();
    t.onerror = () => ok();
  });
};

const loadImg = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = src; });
const cover = (g, el, w = W, h = H) => {
  const sw = el.videoWidth || el.naturalWidth || el.width, sh = el.videoHeight || el.naturalHeight || el.height;
  const s = Math.max(w / sw, h / sh);
  g.drawImage(el, (w - sw * s) / 2, (h - sh * s) / 2, sw * s, sh * s);
};
const makeThumb = async (src) => {
  try {
    const im = await loadImg(src);
    const c = document.createElement("canvas"); c.width = 240; c.height = 320;
    cover(c.getContext("2d"), im, 240, 320);
    return c.toDataURL("image/jpeg", 0.7);
  } catch { return null; }
};

// ---------- Lock: find the shift, tilt and zoom that line the camera up with the locked view ----------
// Works on edge images (robust to light changes), searched coarse to fine over three sizes.
const LOCK_LV = [80, 160, 320];
const lvSize = (L, aw, ah) => (aw >= ah ? [L, Math.max(20, Math.round((L * ah) / aw))] : [Math.max(20, Math.round((L * aw) / ah)), L]);
const gcv = {};
function sample(src, w, h, a = 0, s = 1) {
  const k = w + "x" + h;
  const c = gcv[k] || (gcv[k] = Object.assign(document.createElement("canvas"), { width: w, height: h }));
  const g = c.getContext("2d", { willReadFrequently: true });
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = "#808080"; g.fillRect(0, 0, w, h);
  g.translate(w / 2, h / 2); g.rotate((a * Math.PI) / 180); g.scale(s, s); g.translate(-w / 2, -h / 2);
  cover(g, src, w, h);
  const d = g.getImageData(0, 0, w, h).data, n = w * h, L = new Float32Array(n), E = new Float32Array(n);
  for (let i = 0; i < n; i++) L[i] = d[i * 4] * 0.3 + d[i * 4 + 1] * 0.59 + d[i * 4 + 2] * 0.11;
  let m = 0;
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
    const i = y * w + x;
    const v = Math.abs(L[i + 1] - L[i - 1]) + Math.abs(L[i + w] - L[i - w]);
    E[i] = v; m += v;
  }
  m /= n;
  let q = 0;
  for (let i = 0; i < n; i++) { E[i] -= m; q += E[i] * E[i]; }
  q = Math.sqrt(q / n) || 1;
  for (let i = 0; i < n; i++) E[i] /= q;
  return E;
}
function corr(A, B, w, h, dx, dy, M) {
  let s = 0, n = 0;
  for (let y = M; y < h - M; y++) {
    const ya = y * w, yb = (y - dy) * w - dx;
    for (let x = M; x < w - M; x++) s += A[ya + x] * B[yb + x];
    n += w - 2 * M;
  }
  return n ? s / n : 0;
}
function makeRef(src) {
  return { lv: LOCK_LV.map((L) => { const [w, h] = lvSize(L, W, H); return { w, h, E: sample(src, w, h) }; }) };
}
function align(src, R) {
  const [c0, c1, c2] = R.lv;
  let b0 = { v: -9 };
  for (const s of [0.96, 1, 1.04]) for (let a = -3; a <= 3; a++) {
    const E = sample(src, c0.w, c0.h, a, s);
    for (let dy = -8; dy <= 8; dy++) for (let dx = -8; dx <= 8; dx++) {
      const v = corr(c0.E, E, c0.w, c0.h, dx, dy, 11);
      if (v > b0.v) b0 = { v, a, s, dx, dy };
    }
  }
  if (Math.abs(b0.dx) >= 8 || Math.abs(b0.dy) >= 8 || b0.v < 0.2) return null;
  let b1 = { v: -9 };
  for (const s of [b0.s - 0.02, b0.s, b0.s + 0.02]) for (const a of [b0.a - 0.5, b0.a, b0.a + 0.5]) {
    const E = sample(src, c1.w, c1.h, a, s);
    for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
      const X = b0.dx * 2 + dx, Y = b0.dy * 2 + dy;
      const v = corr(c1.E, E, c1.w, c1.h, X, Y, 22);
      if (v > b1.v) b1 = { v, a, s, dx: X, dy: Y };
    }
  }
  const E2 = sample(src, c2.w, c2.h, b1.a, b1.s);
  let b2 = { v: -9 };
  for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
    const X = b1.dx * 2 + dx, Y = b1.dy * 2 + dy;
    const v = corr(c2.E, E2, c2.w, c2.h, X, Y, 44);
    if (v > b2.v) b2 = { v, dx: X, dy: Y };
  }
  return { a: b1.a, s: b1.s, x: b2.dx / c2.w, y: b2.dy / c2.w, q: b2.v };
}
// Draw a camera picture corrected by a Lock result (edges filled with a zoomed copy so nothing is blank).
function drawCorrected(g, v, fx) {
  if (!fx) { cover(g, v); return; }
  g.save(); g.translate(W / 2, H / 2); g.scale(1.12, 1.12); g.translate(-W / 2, -H / 2); cover(g, v); g.restore();
  g.save();
  g.translate(fx.x * W, fx.y * W); g.translate(W / 2, H / 2); g.rotate((fx.a * Math.PI) / 180); g.scale(fx.s, fx.s); g.translate(-W / 2, -H / 2);
  cover(g, v); g.restore();
}

// ---------- Flicker fix: even out brightness jumps between frames ----------
function flickerGains(imgs) {
  const c = document.createElement("canvas"); c.width = 32; c.height = 32;
  const g = c.getContext("2d", { willReadFrequently: true });
  const means = imgs.map((im) => {
    g.drawImage(im, 0, 0, 32, 32);
    const d = g.getImageData(0, 0, 32, 32).data; let s = 0;
    for (let i = 0; i < d.length; i += 4) s += d[i] * 0.3 + d[i + 1] * 0.59 + d[i + 2] * 0.11;
    return s / 1024 || 1;
  });
  return means.map((m, i) => {
    let s = 0, n = 0;
    for (let j = Math.max(0, i - 3); j <= Math.min(means.length - 1, i + 3); j++) { s += means[j]; n++; }
    return Math.min(1.25, Math.max(0.8, s / n / m));
  });
}
function drawFrame(g, img, k) {
  g.drawImage(img, 0, 0, W, H);
  if (k && Math.abs(k - 1) > 0.01) {
    const d = g.getImageData(0, 0, W, H), a = d.data;
    for (let j = 0; j < a.length; j += 4) { a[j] *= k; a[j + 1] *= k; a[j + 2] *= k; }
    g.putImageData(d, 0, 0);
  }
}
const sequence = (n, pingpong) => {
  const s = [...Array(n).keys()];
  return pingpong && n > 2 ? [...s, ...s.slice(1, -1).reverse()] : s;
};

// ---------- Create video: join every frame into one movie file ----------
async function renderVideo({ frames, fps, voice, vol, deflicker, pingpong, onProgress }) {
  const imgs = await Promise.all(frames.map((f) => loadImg(f.src)));
  const gains = deflicker ? flickerGains(imgs) : null;
  const seq = sequence(imgs.length, pingpong);
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const g = c.getContext("2d", { willReadFrequently: true });
  drawFrame(g, imgs[seq[0]], gains && gains[seq[0]]);
  const stream = c.captureStream(fps);
  let ac, node;
  if (voice) {
    ac = new AudioContext(); await ac.resume();
    const buf = await ac.decodeAudioData(await voice.arrayBuffer());
    const gain = ac.createGain(), dest = ac.createMediaStreamDestination();
    node = ac.createBufferSource(); node.buffer = buf; gain.gain.value = vol;
    node.connect(gain).connect(dest);
    dest.stream.getAudioTracks().forEach((t) => stream.addTrack(t));
  }
  const mime = ["video/mp4;codecs=avc1", "video/mp4", "video/webm;codecs=vp9", "video/webm"].find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) || "";
  const mr = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: 8e6 } : undefined), out = [];
  mr.ondataavailable = (e) => e.data.size && out.push(e.data);
  const done = new Promise((ok) => (mr.onstop = ok));
  mr.start(); if (node) node.start();
  for (let i = 0; i < seq.length; i++) {
    drawFrame(g, imgs[seq[i]], gains && gains[seq[i]]);
    onProgress && onProgress((i + 1) / seq.length);
    await new Promise((r) => setTimeout(r, 1000 / fps));
  }
  mr.stop(); await done; if (ac) ac.close();
  const type = mr.mimeType || mime || "video/webm";
  return { blob: new Blob(out, { type }), ext: type.includes("mp4") ? "mp4" : "webm" };
}

// ================= Movies screen =================
function Projects({ list, onNew, onOpen, onRename, onDuplicate, onDelete }) {
  const [editing, setEditing] = useState(null);
  const [name, setName] = useState("");
  const [confirm, setConfirm] = useState(null);
  return (
    <div className="hs">
      <style>{css}</style>
      <header className="top">
        <div className="titles"><h1>Framey</h1><span className="sub">Your movies</span></div>
        <button className="pill go" onClick={onNew}>New movie</button>
      </header>
      <main className="plist">
        {!list.length && (
          <div className="empty">
            <p>Make your first stop-motion movie. Every movie saves on this phone automatically.</p>
            <button className="pill go" onClick={onNew}>New movie</button>
          </div>
        )}
        {list.map((p) => (
          <div className="pcard" key={p.id}>
            <button className="pthumb" onClick={() => onOpen(p.id)} aria-label={`Open ${p.name}`}>
              {p.thumb ? <img src={p.thumb} alt="" /> : <span>No frames yet</span>}
            </button>
            {editing === p.id ? (
              <form onSubmit={(e) => { e.preventDefault(); onRename(p.id, name.trim() || p.name); setEditing(null); }}>
                <input autoFocus value={name} onChange={(e) => setName(e.target.value)} onBlur={() => { onRename(p.id, name.trim() || p.name); setEditing(null); }} aria-label="Movie name" />
              </form>
            ) : (
              <div className="pname">{p.name}</div>
            )}
            <div className="sub">{p.count || 0} {p.count === 1 ? "frame" : "frames"}</div>
            {confirm === p.id ? (
              <div className="pacts">
                <span className="sub">Delete this movie?</span>
                <button className="danger" onClick={() => { onDelete(p.id); setConfirm(null); }}>Delete</button>
                <button onClick={() => setConfirm(null)}>Keep</button>
              </div>
            ) : (
              <div className="pacts">
                <button onClick={() => { setName(p.name); setEditing(p.id); }}>Rename</button>
                <button onClick={() => onDuplicate(p.id)}>Copy</button>
                <button onClick={() => setConfirm(p.id)}>Delete</button>
              </div>
            )}
          </div>
        ))}
      </main>
    </div>
  );
}

// ================= Full-screen preview =================
function Preview({ frames, fps, setFps, voiceUrl, vol, deflicker, pingpong, setPingpong, onClose, onCreate }) {
  const cv = useRef(), aud = useRef();
  const [imgs, setImgs] = useState(null);
  const [i, setI] = useState(0);
  const [play, setPlay] = useState(true);
  const [loop, setLoop] = useState(true);
  const seq = useMemo(() => sequence(frames.length, pingpong), [frames.length, pingpong]);
  const gains = useMemo(() => (imgs && deflicker ? flickerGains(imgs) : null), [imgs, deflicker]);
  useEffect(() => { Promise.all(frames.map((f) => loadImg(f.src))).then(setImgs).catch(() => {}); }, [frames]);
  useEffect(() => {
    if (!imgs || !cv.current) return;
    const c = cv.current; c.width = W; c.height = H;
    const k = seq[Math.min(i, seq.length - 1)];
    drawFrame(c.getContext("2d", { willReadFrequently: true }), imgs[k], gains && gains[k]);
  }, [i, imgs, gains, seq]);
  useEffect(() => {
    if (!play || !imgs) { if (aud.current) aud.current.pause(); return; }
    const a = aud.current;
    const sound = () => { if (voiceUrl && a) { a.volume = vol; a.currentTime = 0; a.play().catch(() => {}); } };
    if (i === 0) sound();
    const t = setInterval(() => {
      setI((n) => {
        if (n + 1 < seq.length) return n + 1;
        if (loop) { sound(); return 0; }
        setPlay(false); return n;
      });
    }, 1000 / fps);
    return () => clearInterval(t);
  }, [play, imgs, fps, loop, seq.length]);
  return (
    <div className="over" role="dialog" aria-label="Preview">
      <audio ref={aud} src={voiceUrl || undefined} preload="auto" />
      <div className="bar">
        <button className="pill" onClick={onClose}>Back</button>
        <strong className="otitle">Preview</strong>
        <button className="pill go" onClick={onCreate}>Create video</button>
      </div>
      <div className="pv">
        <canvas ref={cv} style={{ aspectRatio: `${W} / ${H}`, width: `min(100cqw, ${W / H} * 100cqh)` }} />
      </div>
      <div className="pctl">
        <div className="bar">
          <button className="pill go" onClick={() => { if (!play && i >= seq.length - 1) setI(0); setPlay(!play); }}>{play ? "Pause" : "Play"}</button>
          <input type="range" min="0" max={Math.max(0, seq.length - 1)} value={i} aria-label="Scrub through frames"
            onChange={(e) => { setPlay(false); setI(+e.target.value); }} />
          <span className="sub">{seq[i] + 1} / {frames.length}</span>
        </div>
        <label className="field">Speed
          <input type="range" min="1" max="24" value={fps} onChange={(e) => setFps(+e.target.value)} /><b>{fps} fps</b></label>
        <div className="row">
          <button aria-pressed={loop} onClick={() => setLoop(!loop)}>Loop</button>
          <button aria-pressed={pingpong} onClick={() => { setPingpong(!pingpong); setI(0); }}>Ping-pong</button>
          <span className="sub">{(seq.length / fps).toFixed(1)} s long</span>
        </div>
      </div>
    </div>
  );
}

// ================= Studio (one movie) =================
function Studio({ project, onBack, onMeta }) {
  const d = { ...DEFAULTS, ...project.data };
  const [frames, setFrames] = useState(d.frames);
  const [past, setPast] = useState([]);
  const [sel, setSel] = useState(null);
  const [fps, setFps] = useState(d.fps);
  const [ghosts, setGhosts] = useState(2);
  const [ghostOp, setGhostOp] = useState(0.5);
  const [grid, setGrid] = useState(false);
  const [facing, setFacing] = useState("environment");
  const [camErr, setCamErr] = useState("");
  const [camOn, setCamOn] = useState(false);
  const [lock, setLock] = useState(false);
  const [fix, setFix] = useState(null);
  const [lockOk, setLockOk] = useState(true);
  const [sheet, setSheet] = useState(false);
  const [ratio, setRatio] = useState(d.frames.length ? d.ratio || "wide" : d.ratio);
  const [dims, setDims] = useState(d.dims || [800, 1200]);
  const [deflicker, setDeflicker] = useState(d.deflicker);
  const [pingpong, setPingpong] = useState(d.pingpong);
  const [playing, setPlaying] = useState(false);
  const [pi, setPi] = useState(0);
  const [lapse, setLapse] = useState(0);
  const [clap, setClap] = useState(false);
  const [timer, setTimer] = useState(0);
  const [timerRepeat, setTimerRepeat] = useState(true);
  const [count, setCount] = useState(null);
  const [flash, setFlash] = useState(0);
  const [rec, setRec] = useState(false);
  const [voice, setVoice] = useState(d.voice);
  const [vol, setVol] = useState(1);
  const [msg, setMsg] = useState("");
  const [preview, setPreview] = useState(false);
  const [making, setMaking] = useState(null);
  const [video, setVideo] = useState(null);
  const vid = useRef(), cvs = useRef(), aud = useRef(), pick = useRef(), recorder = useRef(), viewRef = useRef();
  const pos = useRef(0), dragFrom = useRef(null), live = useRef({}), lockRef = useRef(null), countT = useRef(null), beepCtx = useRef(null);
  const voiceUrl = useMemo(() => (voice ? URL.createObjectURL(voice) : null), [voice]);
  [W, H] = ratio === "fit" ? dims : RATIOS[ratio];

  const edit = (next) => { setPast((p) => [...p.slice(-19), frames]); setFrames(next); };
  const undo = () => { if (!past.length) return; setFrames(past[past.length - 1]); setPast(past.slice(0, -1)); setSel(null); };

  const snap = () => {
    const v = vid.current;
    if (!v || !v.videoWidth) { setMsg("The camera isn't on yet. Tap Allow camera, or import photos."); return; }
    const c = cvs.current; c.width = W; c.height = H;
    const g = c.getContext("2d");
    let fx = null;
    if (lockRef.current) {
      fx = align(v, lockRef.current);
      if (!fx) setMsg("The phone moved too far for Lock to fix this frame. Move it back toward the locked view.");
    }
    drawCorrected(g, v, fx);
    edit([...frames, { id: uid(), src: c.toDataURL("image/jpeg", 0.85) }]);
    setSel(null); setFlash((n) => n + 1);
  };
  const beep = (f, ms = 120) => {
    try {
      const ac = beepCtx.current || (beepCtx.current = new (window.AudioContext || window.webkitAudioContext)());
      if (ac.state === "suspended") ac.resume();
      const o = ac.createOscillator(), g = ac.createGain();
      o.frequency.value = f; g.gain.value = 0.15;
      o.connect(g).connect(ac.destination); o.start(); o.stop(ac.currentTime + ms / 1000);
    } catch {}
  };
  const stopCount = () => { clearInterval(countT.current); countT.current = null; setCount(null); };
  const shoot = () => {
    if (count !== null) { stopCount(); return; }
    if (!timer) { snap(); return; }
    let n = timer; setCount(n); beep(880);
    countT.current = setInterval(() => {
      n -= 1;
      if (n > 0) { setCount(n); beep(880); return; }
      beep(1320, 250); live.current.snap();
      if (live.current.timerRepeat && live.current.timer) { n = live.current.timer; setCount(n); }
      else stopCount();
    }, 1000);
  };
  useEffect(() => () => clearInterval(countT.current), []);
  const holdCam = (on) => {
    const t = vid.current && vid.current.srcObject && vid.current.srcObject.getVideoTracks()[0];
    const m = on ? "manual" : "continuous";
    if (t && t.applyConstraints) t.applyConstraints({ advanced: [{ exposureMode: m, whiteBalanceMode: m, focusMode: m }] }).catch(() => {});
  };
  const toggleLock = async () => {
    if (lock) { setLock(false); lockRef.current = null; holdCam(false); return; }
    try {
      let src = vid.current;
      if (frames.length) src = await loadImg(frames[0].src);
      else if (!src || !src.videoWidth) { setMsg("Turn on the camera first, then tap Lock."); return; }
      lockRef.current = makeRef(src);
      holdCam(true); setLock(true); setLockOk(true);
      setMsg(frames.length ? "Locked to your first frame. Small bumps and tilts are corrected." : "Locked. New frames will line up with this view.");
    } catch { setMsg("Lock couldn't start. Try again with the camera on."); }
  };
  const move = (i, j) => { if (j < 0 || j >= frames.length) return; const n = [...frames]; n.splice(j, 0, n.splice(i, 1)[0]); edit(n); setSel(j); };
  const dup = () => { const f = { ...frames[sel], id: uid() }; edit([...frames.slice(0, sel + 1), f, ...frames.slice(sel + 1)]); setSel(sel + 1); };
  const del = () => { edit(frames.filter((_, i) => i !== sel)); setSel(null); };
  const stopPlay = () => { if (recorder.current && recorder.current.state === "recording") recorder.current.stop(); setPlaying(false); };
  const openPreview = () => { if (!frames.length) { setMsg("Take a few frames first."); return; } stopPlay(); setSel(null); setPreview(true); };
  live.current = { snap, shoot, del, undo, openPreview, sel, frames, playing, timer, timerRepeat };
  useEffect(() => { if (preview || playing) stopCount(); }, [preview, playing]);

  const importFiles = async (files) => {
    const c = cvs.current; c.width = W; c.height = H;
    const added = [];
    for (const f of files) {
      try {
        const im = await loadImg(URL.createObjectURL(f));
        const g = c.getContext("2d"); g.fillStyle = "#000"; g.fillRect(0, 0, W, H); cover(g, im);
        added.push({ id: uid(), src: c.toDataURL("image/jpeg", 0.85) });
      } catch {}
    }
    if (added.length) edit([...frames, ...added]);
  };

  const voiceOver = async () => {
    if (rec) { if (recorder.current) recorder.current.stop(); return; }
    if (!frames.length) { setMsg("Take some frames first, then record over them."); return; }
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(s), chunks = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = () => { s.getTracks().forEach((t) => t.stop()); setVoice(new Blob(chunks, { type: mr.mimeType })); setRec(false); setPlaying(false); setMsg("Voice-over saved."); };
      recorder.current = mr; mr.start(); setRec(true); setSheet(false); pos.current = 0; setSel(null); setPlaying(true);
    } catch { setMsg("The microphone is blocked. Allow it in your browser to record a voice-over."); }
  };

  const createVideo = async () => {
    if (!frames.length) { setMsg("Take a few frames first."); return; }
    setPreview(false); stopPlay(); setMaking(0);
    try {
      const r = await renderVideo({ frames, fps, voice, vol, deflicker, pingpong, onProgress: setMaking });
      setVideo({ ...r, url: URL.createObjectURL(r.blob) });
    } catch { setMsg("Couldn't create the video. Your frames are safe. Try again in Safari or Chrome."); }
    setMaking(null);
  };
  const fileName = () => (project.name || "framey").replace(/[^\w-]+/g, "-").replace(/^-|-$/g, "").toLowerCase() || "framey";
  const saveVideo = async () => {
    const file = new File([video.blob], `${fileName()}.${video.ext}`, { type: video.blob.type });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], title: project.name }); return; } catch (e) { if (e && e.name === "AbortError") return; }
    }
    const a = document.createElement("a"); a.href = video.url; a.download = file.name; a.click();
    setMsg(`Saved ${file.name} to your downloads.`);
  };

  // autosave this movie, and tell the movies list about it
  useEffect(() => {
    const t = setTimeout(() => {
      dbPut("proj:" + project.id, { frames, fps, voice, ratio, dims, deflicker, pingpong }).catch(() => setMsg("Couldn't save. Your phone may be out of space."));
      onMeta(project.id, { count: frames.length });
    }, 600);
    return () => clearTimeout(t);
  }, [frames, fps, voice, ratio, dims, deflicker, pingpong]);
  const firstId = frames[0] && frames[0].id;
  useEffect(() => {
    if (!firstId) { onMeta(project.id, { thumb: null }); return; }
    makeThumb(frames[0].src).then((thumb) => onMeta(project.id, { thumb }));
  }, [firstId]);

  // "Fit screen": the frame shape follows the camera area (only before the first frame)
  useEffect(() => {
    const el = viewRef.current;
    if (!el || ratio !== "fit" || frames.length) return;
    const ro = new ResizeObserver(() => {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const k = 1280 / Math.max(r.width, r.height);
      setDims([Math.round((r.width * k) / 2) * 2, Math.round((r.height * k) / 2) * 2]);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [ratio, frames.length]);

  // camera
  useEffect(() => {
    if (!camOn) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { setCamErr("This browser can't open a camera. Import photos instead."); setCamOn(false); return; }
    let stream, dead = false;
    setCamErr("");
    navigator.mediaDevices.getUserMedia({ video: { facingMode: facing, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false })
      .then((s) => { if (dead) { s.getTracks().forEach((t) => t.stop()); return; } stream = s; vid.current.srcObject = s; })
      .catch((e) => {
        const why = {
          NotAllowedError: "The browser denied camera access. If this page is inside a preview or another app, open it in its own Safari or Chrome tab.",
          SecurityError: "The browser denied camera access. Open this page in its own Safari or Chrome tab over https.",
          NotFoundError: "No camera was found on this device.",
          NotReadableError: "Another app or tab is using the camera. Close it and try again.",
        }[e && e.name] || `Camera error: ${(e && e.name) || "unknown"}.`;
        setCamErr(why); setCamOn(false);
      });
    return () => { dead = true; if (stream) stream.getTracks().forEach((t) => t.stop()); };
  }, [facing, camOn]);

  // live Lock preview: keep the viewfinder lined up, smoothly
  useEffect(() => {
    if (!lock || !camOn || playing || preview) { setFix(null); return; }
    const t = setInterval(() => {
      const v = vid.current;
      if (!v || !v.videoWidth || !lockRef.current) return;
      const f = align(v, lockRef.current);
      setLockOk(!!f);
      setFix((p) => (f && p ? { a: p.a + (f.a - p.a) * 0.6, s: p.s + (f.s - p.s) * 0.6, x: p.x + (f.x - p.x) * 0.6, y: p.y + (f.y - p.y) * 0.6 } : f));
    }, 250);
    return () => clearInterval(t);
  }, [lock, camOn, playing, preview]);

  useEffect(() => {
    if (!lapse || playing || preview) return;
    const t = setInterval(() => live.current.snap(), lapse * 1000);
    return () => clearInterval(t);
  }, [lapse, playing, preview]);

  useEffect(() => {
    if (!clap) return;
    let ctx, raf, stream, last = 0, dead = false;
    navigator.mediaDevices.getUserMedia({ audio: true }).then((s) => {
      if (dead) { s.getTracks().forEach((t) => t.stop()); return; }
      stream = s; ctx = new AudioContext();
      const an = ctx.createAnalyser(); an.fftSize = 512;
      ctx.createMediaStreamSource(s).connect(an);
      const buf = new Uint8Array(an.fftSize);
      const tick = () => {
        an.getByteTimeDomainData(buf);
        let peak = 0; for (const b of buf) peak = Math.max(peak, Math.abs(b - 128));
        if (peak > 70 && Date.now() - last > 1500) { last = Date.now(); live.current.snap(); }
        raf = requestAnimationFrame(tick);
      };
      tick();
    }).catch(() => { setClap(false); setMsg("The microphone is blocked. Allow it in your browser to shoot by clapping."); });
    return () => { dead = true; cancelAnimationFrame(raf); if (ctx) ctx.close(); if (stream) stream.getTracks().forEach((t) => t.stop()); };
  }, [clap]);

  // playback on the stage (used while recording a voice-over)
  useEffect(() => {
    if (!playing) return;
    if (!frames.length) { setPlaying(false); return; }
    let i = 0; pos.current = 0; setPi(0);
    const t = setInterval(() => {
      i += 1;
      if (i >= frames.length) { stopPlay(); return; }
      pos.current = i; setPi(i);
    }, 1000 / fps);
    return () => clearInterval(t);
  }, [playing, fps]);

  useEffect(() => {
    const onKey = (e) => {
      const L = live.current;
      if (/^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(e.target.tagName)) return;
      if ((e.metaKey || e.ctrlKey) && e.key === "z") { e.preventDefault(); L.undo(); }
      else if (e.metaKey || e.ctrlKey || e.altKey) return;
      else if (e.code === "Space" || e.code === "Enter") { e.preventDefault(); if (!L.playing) L.shoot(); }
      else if (e.key === "ArrowLeft") setSel(L.frames.length ? Math.max(0, (L.sel === null ? L.frames.length : L.sel) - 1) : null);
      else if (e.key === "ArrowRight") setSel(L.sel === null || L.sel >= L.frames.length - 1 ? null : L.sel + 1);
      else if ((e.key === "Delete" || e.key === "Backspace") && L.sel !== null) L.del();
      else if (e.key === "p") L.openPreview();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(""), 5000);
    return () => clearTimeout(t);
  }, [msg]);

  const cur = playing ? pi : sel;
  const shown = cur !== null ? frames[cur] : null;
  const ghostFrames = cur === null ? frames.slice(-ghosts).reverse() : [];
  const fixStyle = fix ? { transform: `translate(${fix.x * 100}%, ${fix.y * (W / H) * 100}%) rotate(${fix.a}deg) scale(${fix.s})` } : undefined;
  const timerNext = { 0: 3, 3: 5, 5: 10, 10: 0 };

  return (
    <div className="hs" onClick={(e) => { if (e.detail) { const b = e.target.closest && e.target.closest("button"); if (b) b.blur(); } }}>
      <style>{css}</style>
      <canvas ref={cvs} hidden />
      <input ref={pick} type="file" accept="image/*" multiple hidden onChange={(e) => { importFiles([...e.target.files]); e.target.value = ""; }} />

      <header className="top">
        <div className="lead">
          <button className="pill" onClick={onBack} aria-label="Back to your movies">Movies</button>
          <div className="titles">
            <h1>{project.name}</h1>
            <span className="sub">{frames.length} {frames.length === 1 ? "frame" : "frames"}, {(sequence(frames.length, pingpong).length / fps).toFixed(1)} s</span>
          </div>
        </div>
        <button className="pill go" onClick={createVideo} disabled={!frames.length || making !== null}>Create video</button>
      </header>

      <main className="view" ref={viewRef}>
        <div className="stage" style={{ aspectRatio: `${W} / ${H}`, width: `min(100cqw, ${W / H} * 100cqh)` }}>
          <video ref={vid} autoPlay playsInline muted style={fixStyle} />
          {ghostFrames.map((f, i) => <img key={f.id} className="ghost" src={f.src} alt="" style={{ opacity: ghostOp / (i + 1) }} />)}
          {shown && <img src={shown.src} alt={`Frame ${cur + 1}`} />}
          {grid && <div className="grid" />}
          {!camOn && !shown && (
            <div className="ask">
              <p>{camErr || "Framey needs your camera to take frames. Tap Allow camera, then choose Allow in the browser prompt."}</p>
              <button className="pill go" onClick={() => setCamOn(true)}>{camErr ? "Try again" : "Allow camera"}</button>
            </div>
          )}
          {lock && camOn && (lockOk ? <span className="badge lockb">Locked</span> : <span className="badge warnb">Move back to lock</span>)}
          {rec && <button className="badge recb" onClick={voiceOver}>Recording. Tap to stop</button>}
          {count !== null && (
            <div className="count" aria-live="assertive">
              <div className="ring" key={count}><span>{count}</span></div>
              <p>{timerRepeat ? "Keeps going after each photo. Tap the shutter to stop." : "Get ready. Tap the shutter to cancel."}</p>
            </div>
          )}
          {timer > 0 && count === null && !rec && <span className="badge timerb">Timer {timer}s{timerRepeat ? ", repeat" : ""}</span>}
          {flash > 0 && <div className="flash" key={flash} />}
          <div className="rail">
            <button aria-pressed={lock} onClick={toggleLock}>Lock</button>
            <button aria-pressed={grid} onClick={() => setGrid(!grid)}>Grid</button>
            <button aria-pressed={timer > 0} onClick={() => setTimer(timerNext[timer])}>{timer ? `${timer}s` : "Timer"}</button>
            <button aria-pressed={clap} onClick={() => setClap(!clap)}>Clap</button>
            <button onClick={() => setFacing(facing === "environment" ? "user" : "environment")}>Flip</button>
          </div>
          <p className="toast" role="status" aria-live="polite">{msg}</p>
        </div>
      </main>

      <footer className="dock">
        {sel !== null && (
          <div className="acts">
            <button className="pill" onClick={() => move(sel, sel - 1)} disabled={sel === 0}>Earlier</button>
            <button className="pill" onClick={() => move(sel, sel + 1)} disabled={sel === frames.length - 1}>Later</button>
            <button className="pill" onClick={dup}>Hold</button>
            <button className="pill" onClick={del}>Delete</button>
            <button className="pill" onClick={() => setSel(null)}>Camera</button>
          </div>
        )}
        <div className="strip" aria-label="Timeline">
          {frames.map((f, i) => (
            <button key={f.id} className="th" draggable style={{ aspectRatio: `${W} / ${H}` }} aria-current={cur === i ? "true" : undefined}
              onClick={() => { setPlaying(false); setSel(i); }}
              onDragStart={() => (dragFrom.current = i)} onDragOver={(e) => e.preventDefault()}
              onDrop={() => { if (dragFrom.current !== null && dragFrom.current !== i) move(dragFrom.current, i); dragFrom.current = null; }}>
              <img src={f.src} alt={`Frame ${i + 1}`} draggable={false} /><b>{i + 1}</b>
            </button>
          ))}
          {!frames.length && <p className="sub">Your frames appear here. Press Space to shoot.</p>}
        </div>
        <div className="ctrl">
          <button className="tool" onClick={() => pick.current.click()}>Import</button>
          <button className="tool" onClick={undo} disabled={!past.length}>Undo</button>
          <button className="shutter" onClick={shoot} disabled={playing} aria-label={count !== null ? "Stop timer" : "Take frame"}><i>{count !== null ? count : null}</i></button>
          <button className="tool" onClick={openPreview} disabled={!frames.length}>Preview</button>
          <button className="tool" aria-pressed={sheet} onClick={() => setSheet(!sheet)}>Settings</button>
        </div>
      </footer>

      {sheet && (
        <div className="sheet" role="dialog" aria-label="Settings">
          <div className="grab" />
          <label className="field">Speed<input type="range" min="1" max="24" value={fps} onChange={(e) => setFps(+e.target.value)} /><b>{fps} fps</b></label>
          <label className="field">Ghost frames<input type="range" min="0" max="3" value={ghosts} onChange={(e) => setGhosts(+e.target.value)} /><b>{ghosts}</b></label>
          <label className="field">Ghost strength<input type="range" min="0.1" max="0.9" step="0.05" value={ghostOp} onChange={(e) => setGhostOp(+e.target.value)} /></label>
          <div className="row" role="group" aria-label="Frame shape">
            {["fit", ...Object.keys(RATIOS)].map((k) => (
              <button key={k} aria-pressed={ratio === k} disabled={!!frames.length && ratio !== k} onClick={() => { setRatio(k); setPast([]); }}>{LABELS[k]}</button>
            ))}
          </div>
          <div className="row">
            <button aria-pressed={deflicker} onClick={() => setDeflicker(!deflicker)}>Fix flicker</button>
            <button aria-pressed={pingpong} onClick={() => setPingpong(!pingpong)}>Ping-pong</button>
          </div>
          <div className="row">
            <label className="field">Self-timer
              <select value={timer} onChange={(e) => setTimer(+e.target.value)}>
                <option value="0">Off</option><option value="3">3 seconds</option><option value="5">5 seconds</option><option value="10">10 seconds</option>
              </select></label>
            <button aria-pressed={timerRepeat} onClick={() => setTimerRepeat(!timerRepeat)}>Repeat timer</button>
            <label className="field">Time-lapse
              <select value={lapse} onChange={(e) => setLapse(+e.target.value)}>
                <option value="0">Off</option>
                {[1, 2, 5, 10].map((s) => <option key={s} value={s}>Every {s} s</option>)}
              </select></label>
          </div>
          <div className="row">
            <button aria-pressed={rec} onClick={voiceOver} disabled={!frames.length && !rec}>{rec ? "Stop recording" : voice ? "Re-record voice-over" : "Record voice-over"}</button>
            {voice && (
              <>
                <label className="field">Voice volume<input type="range" min="0" max="1" step="0.05" value={vol} onChange={(e) => setVol(+e.target.value)} /></label>
                <button onClick={() => setVoice(null)}>Remove voice-over</button>
              </>
            )}
            <button onClick={() => { edit([]); setSel(null); }} disabled={!frames.length}>Clear frames</button>
          </div>
          <p className="sub">Fix flicker evens out brightness jumps between frames in Preview and in your video. Ping-pong plays forward, then backward. Repeat timer keeps counting down and taking photos until you tap the shutter. Space or Enter takes a frame, P opens Preview, Ctrl+Z undoes. The frame shape can only change while the timeline is empty.</p>
          <button className="pill go" onClick={() => setSheet(false)}>Done</button>
        </div>
      )}

      {preview && (
        <Preview frames={frames} fps={fps} setFps={setFps} voiceUrl={voiceUrl} vol={vol} deflicker={deflicker}
          pingpong={pingpong} setPingpong={setPingpong} onClose={() => setPreview(false)} onCreate={createVideo} />
      )}

      {making !== null && (
        <div className="over center" role="dialog" aria-label="Creating video">
          <strong className="otitle">Creating your video</strong>
          <div className="prog"><i style={{ width: `${Math.round(making * 100)}%` }} /></div>
          <p className="sub">{Math.round(making * 100)}%. Keep this screen open.</p>
        </div>
      )}

      {video && (
        <div className="over" role="dialog" aria-label="Your video">
          <div className="bar">
            <button className="pill" onClick={() => { URL.revokeObjectURL(video.url); setVideo(null); }}>Back</button>
            <strong className="otitle">Your video</strong>
            <button className="pill go" onClick={saveVideo}>Save or share</button>
          </div>
          <div className="pv">
            <video src={video.url} controls playsInline autoPlay loop style={{ aspectRatio: `${W} / ${H}`, width: `min(100cqw, ${W / H} * 100cqh)` }} />
          </div>
          <p className="sub center-text">On iPhone, tap Save or share, then Save Video to put it in Photos.</p>
        </div>
      )}
    </div>
  );
}

// ================= App: movies list + studio =================
function App() {
  const [list, setList] = useState(null);
  const [open, setOpen] = useState(null);
  const saveList = (fn) => setList((l) => { const n = fn(l || []); dbPut("projects", n).catch(() => {}); return n; });

  useEffect(() => {
    (async () => {
      let l = null;
      try { l = await dbGet("projects"); } catch {}
      if (!l) {
        l = [];
        try {
          const old = await dbGet("project");
          if (old && old.frames && old.frames.length) {
            const id = uid();
            await dbPut("proj:" + id, { ...DEFAULTS, ...old, ratio: old.ratio || "wide" });
            l = [{ id, name: "My first movie", updated: Date.now(), count: old.frames.length, thumb: await makeThumb(old.frames[0].src) }];
          }
          await dbPut("projects", l);
        } catch {}
      }
      setList(l);
    })();
  }, []);

  const onNew = async () => {
    const id = uid();
    const name = `Movie ${(list ? list.length : 0) + 1}`;
    const data = { ...DEFAULTS };
    await dbPut("proj:" + id, data).catch(() => {});
    saveList((l) => [{ id, name, updated: Date.now(), count: 0, thumb: null }, ...l]);
    setOpen({ id, name, data });
  };
  const onOpen = async (id) => {
    const p = list.find((x) => x.id === id);
    let data = null;
    try { data = await dbGet("proj:" + id); } catch {}
    setOpen({ id, name: p.name, data: data || { ...DEFAULTS } });
  };
  const onMeta = (id, meta) => saveList((l) => l.map((p) => (p.id === id ? { ...p, ...meta, updated: Date.now() } : p)));
  const onRename = (id, name) => saveList((l) => l.map((p) => (p.id === id ? { ...p, name } : p)));
  const onDuplicate = async (id) => {
    const p = list.find((x) => x.id === id);
    const data = await dbGet("proj:" + id).catch(() => null);
    const nid = uid();
    await dbPut("proj:" + nid, data || { ...DEFAULTS }).catch(() => {});
    saveList((l) => { const i = l.findIndex((x) => x.id === id); const n = [...l]; n.splice(i + 1, 0, { ...p, id: nid, name: `${p.name} copy`, updated: Date.now() }); return n; });
  };
  const onDelete = async (id) => { await dbDel("proj:" + id); saveList((l) => l.filter((p) => p.id !== id)); };

  if (!list) return <div className="hs"><style>{css}</style></div>;
  if (open) {
    const p = list.find((x) => x.id === open.id);
    return <Studio key={open.id} project={{ ...open, name: (p && p.name) || open.name }} onMeta={onMeta} onBack={() => setOpen(null)} />;
  }
  return <Projects list={list} onNew={onNew} onOpen={onOpen} onRename={onRename} onDuplicate={onDuplicate} onDelete={onDelete} />;
}

const css = `
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;600;800&display=swap');
.hs{--panel:#1C1C1E;--line:#3A3A3C;--ink:#F2F2F2;--dim:#9A9AA0;--clay:#FE6100;--ghost:#648FFF;--rec:#FF453A;
  position:fixed;inset:0;display:flex;flex-direction:column;overflow:hidden;background:#111111;color:var(--ink);
  font-family:'Bricolage Grotesque',system-ui,sans-serif;padding-top:env(safe-area-inset-top)}
.hs *{box-sizing:border-box}
.hs h1{margin:0;font-size:1.15rem;font-weight:800;letter-spacing:-.02em;line-height:1.1;color:var(--clay);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hs .sub{margin:0;color:var(--dim);font-size:.8rem}
.hs button,.hs select{font:inherit;color:inherit;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px 12px;min-height:44px;cursor:pointer;touch-action:manipulation}
.hs button:disabled{opacity:.4;cursor:default}
.hs button:focus-visible,.hs input:focus-visible,.hs select:focus-visible{outline:3px solid #fff;outline-offset:2px}
.hs button[aria-pressed=true]{background:var(--ghost);border-color:var(--ghost);color:#111;font-weight:700}
.hs button.go{background:var(--clay);border-color:var(--clay);color:#111;font-weight:800}
.hs button.pill{border-radius:999px;min-height:40px;padding:6px 16px}
.hs input[type=range]{accent-color:var(--clay);min-width:100px;flex:1}
.hs .top{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 12px;border-bottom:2px solid var(--clay)}
.hs .top .sub{color:var(--clay)}
.hs .lead{display:flex;align-items:center;gap:10px;min-width:0}
.hs .titles{min-width:0}
.hs .titles .sub{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hs .top button{white-space:nowrap;flex:0 0 auto;font-size:.85rem;padding:6px 12px;min-height:38px}
.hs .lead{flex:1 1 auto}
@media (max-width:380px){.hs .top button{padding:6px 9px;font-size:.8rem}.hs h1{font-size:1rem}.hs button.tool{padding:2px 1px;font-size:.64rem;text-overflow:clip;border-radius:12px}.hs .ctrl{gap:4px}}
.hs .view{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;container-type:size;padding:6px 4px 0}
.hs .stage{position:relative;overflow:hidden;border-radius:20px;background:#0B0B0B;border:2px solid var(--clay);max-height:100%}
.hs .stage>video,.hs .stage>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hs .stage>img.ghost{pointer-events:none;filter:grayscale(1) sepia(1) saturate(6) hue-rotate(185deg) brightness(1.05)}
.hs .grid{position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(#fff4 1px,transparent 1px),linear-gradient(90deg,#fff4 1px,transparent 1px);background-size:33.333% 33.333%}
.hs .ask{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:20px;text-align:center;background:#0B0B0B}
.hs .ask p{margin:0;max-width:30ch}
.hs .ask p::before{content:"";display:block;width:56px;height:6px;border-radius:3px;background:var(--clay);margin:0 auto 14px}
.hs .badge{position:absolute;top:12px;z-index:3;padding:4px 10px;border-radius:999px;font-size:.75rem;font-weight:800;min-height:0}
.hs .lockb{left:12px;background:var(--ghost);color:#111}
.hs .warnb{left:12px;background:var(--clay);color:#111}
.hs .recb{right:12px;background:var(--rec);border:0;color:#fff}
.hs .rail{position:absolute;right:8px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:8px;z-index:1}
.hs .rail button{min-width:58px;min-height:44px;padding:4px 8px;font-size:.78rem;background:#000b;border-color:var(--clay);color:var(--clay)}
.hs .rail button[aria-pressed=true]{background:var(--ghost);border-color:var(--ghost);color:#111}
.hs .toast{position:absolute;left:12px;right:12px;bottom:12px;z-index:3;margin:0;padding:8px 12px;border-radius:12px;background:#000d;border:2px solid var(--clay);font-size:.82rem;text-align:center}
.hs .toast:empty{display:none}
.hs .count{position:absolute;inset:0;z-index:4;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;pointer-events:none;text-align:center}
.hs .count .ring{display:flex;align-items:center;justify-content:center;animation:hspulse 1s ease-out}
.hs .count span{font-size:clamp(6rem,34cqw,13rem);font-weight:800;color:#fff;line-height:1;text-shadow:0 0 3px #000,0 4px 18px #000b}
.hs .count p{margin:0;padding:6px 12px;border-radius:14px;background:#000c;font-size:.82rem;color:var(--ink);max-width:calc(100% - 130px)}
@keyframes hspulse{from{transform:scale(1.12)}to{transform:scale(1)}}
.hs .timerb{right:12px;background:#000c;color:var(--clay);border:2px solid var(--clay)}
.hs .flash{position:absolute;inset:0;z-index:3;background:#fff;pointer-events:none;animation:hsflash .3s ease-out forwards}
@keyframes hsflash{from{opacity:.75}to{opacity:0}}
.hs .dock{display:flex;flex-direction:column;gap:8px;padding:6px 12px max(10px,env(safe-area-inset-bottom))}
.hs .acts{display:flex;gap:6px;overflow-x:auto}
.hs .acts button.pill{border-color:var(--clay);color:var(--clay)}
.hs .strip{display:flex;gap:6px;overflow-x:auto;min-height:58px;align-items:center;scrollbar-width:none}
.hs button.th{position:relative;flex:0 0 auto;height:56px;width:auto;padding:0;overflow:hidden;border-radius:8px}
.hs .th img{display:block;width:100%;height:100%;object-fit:cover}
.hs .th b{position:absolute;left:3px;bottom:2px;padding:0 5px;border-radius:5px;background:var(--clay);color:#111;font-size:.65rem}
.hs button.th[aria-current=true]{outline:3px solid var(--ghost)}
.hs .ctrl{display:flex;align-items:center;justify-content:space-between;gap:6px}
.hs button.tool{flex:1 1 0;min-width:0;max-width:84px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-height:50px;padding:4px 3px;font-size:.74rem;border-radius:14px;border-color:var(--clay);color:var(--clay)}
.hs button.tool:disabled{border-color:var(--line);color:var(--ink)}
.hs button.tool[aria-pressed=true]{color:#111}
.hs button.shutter{flex:0 0 76px;width:76px;height:76px;padding:4px;border-radius:50%;background:transparent;border:4px solid var(--clay)}
.hs .shutter i{display:flex;align-items:center;justify-content:center;width:100%;height:100%;border-radius:50%;background:var(--clay);box-shadow:inset 0 0 0 4px #111;transition:transform .08s;font-size:1.8rem;font-weight:800;font-style:normal;color:#111}
.hs .shutter:active:not(:disabled) i{transform:scale(.88)}
.hs .sheet{position:absolute;left:0;right:0;bottom:0;z-index:5;max-height:80dvh;overflow:auto;display:grid;gap:12px;padding:10px 16px max(16px,env(safe-area-inset-bottom));background:var(--panel);border-radius:22px 22px 0 0;border-top:2px solid var(--clay);box-shadow:0 -24px 48px #000a}
.hs .grab{width:40px;height:4px;border-radius:2px;background:var(--clay);margin:0 auto}
.hs .row{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.hs .field{display:flex;align-items:center;gap:8px;color:var(--ink);font-size:.85rem}
.hs .field b{color:var(--clay);font-weight:700;min-width:3em}
.hs .sheet button,.hs .sheet select{background:#2C2C2E}
.hs .sheet button:not([aria-pressed=true]):not(.go):not(:disabled),.hs .sheet select{border-color:var(--clay);color:var(--clay)}
.hs .sheet button[aria-pressed=true]{background:var(--ghost);color:#111}
.hs .sheet button.go{background:var(--clay);color:#111}
.hs .over{position:absolute;inset:0;z-index:8;display:flex;flex-direction:column;gap:10px;background:#111;padding:max(10px,env(safe-area-inset-top)) 12px max(14px,env(safe-area-inset-bottom))}
.hs .over.center{align-items:center;justify-content:center;text-align:center;padding:24px}
.hs .over .bar{display:flex;align-items:center;justify-content:space-between;gap:8px}
.hs .otitle{font-size:1.05rem;color:var(--clay)}
.hs .over .pv{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;container-type:size}
.hs .over canvas,.hs .over video{display:block;border-radius:16px;border:2px solid var(--clay);background:#000;max-height:100%}
.hs .pctl{display:grid;gap:10px}
.hs .pctl .bar input{flex:1}
.hs .pctl .row button:not([aria-pressed=true]){border-color:var(--clay);color:var(--clay)}
.hs .prog{width:min(320px,80vw);height:12px;border-radius:6px;background:var(--line);overflow:hidden}
.hs .prog i{display:block;height:100%;background:var(--clay);transition:width .2s}
.hs .center-text{text-align:center}
.hs .plist{flex:1;overflow:auto;padding:14px 12px max(14px,env(safe-area-inset-bottom));display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;align-content:start}
.hs .empty{grid-column:1/-1;display:grid;justify-items:center;gap:14px;text-align:center;padding:48px 12px}
.hs .empty p{margin:0;max-width:28ch;font-size:1.05rem}
.hs .pcard{display:flex;flex-direction:column;gap:6px;min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:8px}
.hs button.pthumb{display:flex;align-items:center;justify-content:center;aspect-ratio:3/4;width:100%;padding:0;border-radius:10px;background:#0B0B0B;border:2px solid var(--clay);overflow:hidden;color:var(--dim);font-size:.8rem}
.hs .pthumb img{width:100%;height:100%;object-fit:cover;display:block}
.hs .pname{font-weight:700;font-size:.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hs .pcard input{font:inherit;width:100%;background:#0B0B0B;color:var(--ink);border:2px solid var(--clay);border-radius:8px;padding:6px 8px}
.hs .pacts{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.hs .pacts button{min-height:34px;padding:4px 8px;font-size:.75rem;border-radius:9px;border-color:var(--clay);color:var(--clay)}
.hs .pacts button.danger{background:var(--rec);border-color:var(--rec);color:#fff}
@media (prefers-reduced-motion:reduce){.hs .shutter i,.hs .prog i{transition:none}.hs .flash{animation-duration:.01s}.hs .count .ring{animation:none}}
`;

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
