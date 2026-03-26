// Animated Background - CodePen Style: https://codepen.io/Allan-Rodney/pen/QwKOVjb
(function() {
  let canvas = document.getElementById("bg");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "bg";
    canvas.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;";
    document.body.insertBefore(canvas, document.body.firstChild);
  }
  const ctx = canvas.getContext("2d");
  let w, h, mode = "dark", time = 0;
  
  function resize() { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight; }
  window.addEventListener("resize", resize);
  resize();
  
  // Toggle
  let btn = document.getElementById("themeToggle");
  if (!btn) {
    btn = document.createElement("button");
    btn.id = "themeToggle";
    btn.innerHTML = "🌙";
    btn.style.cssText = "position:fixed;left:260px;top:40%;transform:translateY(-50%);z-index:9999;padding:12px 8px;border-radius:0 8px 8px 0;border:none;cursor:pointer;background:#3b82f6;color:#fff;font-size:14px;";
    btn.onclick = () => { mode = mode === "light" ? "dark" : "light"; btn.innerHTML = mode === "dark" ? "🌙" : "☀️"; initClouds(); };
    document.body.appendChild(btn);
  }
  
  // Fluffy Clouds (multi-contour)
  class Cloud {
    constructor(y, scale, speed) {
      this.y = y;
      this.scale = scale;
      this.speed = speed;
      this.x = Math.random() * w;
      this.blobs = [];
      const numBlobs = Math.floor(Math.random() * 3) + 3;
      for (let i = 0; i < numBlobs; i++) {
        this.blobs.push({
          x: (Math.random() - 0.5) * 100 * scale,
          y: (Math.random() - 0.5) * 40 * scale,
          r: (Math.random() * 30 + 30) * scale
        });
      }
    }
    update() {
      this.x += this.speed;
      if (this.x > w + 200) this.x = -200;
    }
    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.fillStyle = mode === "dark" ? "rgba(99, 102, 241, 0.15)" : "rgba(59, 130, 246, 0.2)";
      ctx.shadowColor = mode === "dark" ? "rgba(99, 102, 241, 0.4)" : "rgba(59, 130, 246, 0.3)";
      ctx.shadowBlur = 40;
      this.blobs.forEach(blob => {
        ctx.beginPath();
        ctx.arc(blob.x, blob.y, blob.r, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    }
  }
  
  let clouds = [];
  function initClouds() {
    clouds = [];
    for (let i = 0; i < 8; i++) {
      const y = Math.random() * h;
      const scale = Math.random() * 0.8 + 0.4;
      const speed = (Math.random() * 0.3 + 0.1) * (Math.random() > 0.5 ? 1 : -1);
      clouds.push(new Cloud(y, scale, speed));
    }
  }
  
  function animate() {
    time += 0.01;
    ctx.fillStyle = mode === "dark" ? "#020203" : "#f0f4f8";
    ctx.fillRect(0, 0, w, h);
    clouds.forEach(c => { c.update(); c.draw(); });
    // Overlay
    ctx.fillStyle = mode === "dark" ? "rgba(15, 15, 15, 0.85)" : "rgba(255, 255, 255, 0.3)";
    ctx.fillRect(0, 0, w, h);
    requestAnimationFrame(animate);
  }
  
  initClouds();
  animate();
})();
