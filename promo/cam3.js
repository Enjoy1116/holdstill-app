(()=>{
  const N=14;window.__k=0;window.__vis=0;
  const c=document.createElement('canvas');c.width=960;c.height=1280;const g=c.getContext('2d');
  const path=(k)=>{const t=k/(N-1);const x=290+t*350;const hop=(k%(N-1))%3; // hop every 3 frames
    const ph=((k%3)/3);const y=Math.sin(ph*Math.PI)*170;const sq=ph===0?0.78:1.0+0.06*Math.sin(ph*Math.PI);return {x,y,sq};};
  function draw(){
    const now=performance.now();window.__vis+=(window.__k-window.__vis)*0.35;
    const k=window.__vis;const a=path(Math.floor(k)),b=path(Math.min(N-1,Math.floor(k)+1)),f=k-Math.floor(k);
    const p={x:a.x+(b.x-a.x)*f,y:a.y+(b.y-a.y)*f,sq:a.sq+(b.sq-a.sq)*f};
    let gr=g.createLinearGradient(0,0,0,760);if(window.__green){gr.addColorStop(0,'#19D63A');gr.addColorStop(1,'#14C832');}else{gr.addColorStop(0,'#E9DCC6');gr.addColorStop(1,'#D8C7AA');}g.fillStyle=gr;g.fillRect(0,0,960,760);
    if(!window.__green){g.fillStyle='rgba(0,0,0,.05)';for(let i=0;i<960;i+=120)g.fillRect(i,0,4,760);}
    gr=g.createLinearGradient(0,760,0,1280);gr.addColorStop(0,'#A66A3C');gr.addColorStop(1,'#7A4A28');g.fillStyle=gr;g.fillRect(0,760,960,520);
    g.strokeStyle='rgba(60,30,10,.25)';g.lineWidth=3;for(let i=0;i<6;i++){g.beginPath();g.moveTo(0,820+i*80);g.bezierCurveTo(300,800+i*80,600,850+i*80,960,815+i*80);g.stroke();}
    // props: a mug and a block (so Lock has something to hold on to)
    g.fillStyle='#3F6FD8';g.fillRect(60,560,130,210);g.fillStyle='#2F57B0';g.fillRect(60,560,130,24);
    g.fillStyle='#FFD24A';g.beginPath();g.moveTo(760,780);g.lineTo(900,780);g.lineTo(900,660);g.lineTo(830,600);g.lineTo(760,660);g.closePath();g.fill();
    // the clay character
    const gx=p.x,base=900;const r=78;
    g.fillStyle='rgba(0,0,0,'+(0.32-0.0012*p.y)+')';g.beginPath();g.ellipse(gx,base+8,r*(1-p.y/600),18,0,0,7);g.fill();
    const cy=base-p.y-r*p.sq;g.save();g.translate(gx,cy);g.scale(1/Math.sqrt(p.sq),p.sq);
    gr=g.createRadialGradient(-25,-30,10,0,0,r*1.1);gr.addColorStop(0,'#FF9A4D');gr.addColorStop(1,'#E04E00');g.fillStyle=gr;g.beginPath();g.arc(0,0,r,0,7);g.fill();
    g.fillStyle='#fff';g.beginPath();g.arc(-24,-14,18,0,7);g.arc(24,-14,18,0,7);g.fill();
    g.fillStyle='#111';g.beginPath();g.arc(-20,-12,8,0,7);g.arc(28,-12,8,0,7);g.fill();
    g.strokeStyle='#5a1e00';g.lineWidth=6;g.lineCap='round';g.beginPath();g.arc(2,14,20,0.2,Math.PI-0.2);g.stroke();
    g.restore();
    shoot();
    requestAnimationFrame(draw);
  }
  // the "phone": looks at the scene, can wobble (window.__shake = {x,y,a,s})
  const cam=document.createElement('canvas');cam.width=960;cam.height=1280;const gc=cam.getContext('2d');
  function shoot(){const j=window.__shake||{x:0,y:0,a:0,s:1};gc.setTransform(1,0,0,1,0,0);gc.fillStyle='#7A4A28';gc.fillRect(0,0,960,1280);
    gc.translate(480+j.x,640+j.y);gc.rotate(j.a*Math.PI/180);gc.scale(1.12*j.s,1.12*j.s);gc.translate(-480,-640);gc.drawImage(c,0,0);}
  draw();
  navigator.mediaDevices.getUserMedia=async(cs)=>{ if(cs&&cs.video) return cam.captureStream(30); const ac=new AudioContext();return ac.createMediaStreamDestination().stream; };
})();