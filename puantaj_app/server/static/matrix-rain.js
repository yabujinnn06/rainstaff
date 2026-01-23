(function(){
  const C = "01";
  
  class MatrixRain {
    constructor(canvas, opts) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.fs = opts.fs || 14;
      this.color = opts.color || "#22d3ee";
      this.op = opts.op || 0.15;
      this.spd = opts.spd || 80;
      this.cols = [];
      this.init();
    }
    
    init() {
      this.resize();
      window.addEventListener("resize", () => this.resize());
      this.loop();
    }
    
    resize() {
      let p = this.canvas.parentElement;
      this.canvas.width = p.offsetWidth;
      this.canvas.height = p.offsetHeight;
      let n = Math.floor(this.canvas.width / this.fs);
      this.cols = Array(n).fill(0).map(() => Math.random() * -20 | 0);
    }
    
    draw() {
      this.ctx.fillStyle = "rgba(0,0,0,0.05)";
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      this.ctx.font = this.fs + "px monospace";
      this.ctx.fillStyle = this.color;
      this.ctx.globalAlpha = this.op;
      
      for (let i = 0; i < this.cols.length; i++) {
        let ch = C[Math.random() * C.length | 0];
        let x = i * this.fs;
        let y = this.cols[i] * this.fs;
        this.ctx.fillText(ch, x, y);
        if (y > this.canvas.height && Math.random() > 0.98) this.cols[i] = 0;
        this.cols[i]++;
      }
      this.ctx.globalAlpha = 1;
    }
    
    loop() {
      this.draw();
      setTimeout(() => requestAnimationFrame(() => this.loop()), this.spd);
    }
  }
  
  function addRain(selector, opts) {
    let el = document.querySelector(selector);
    if (!el || el.querySelector(".matrix-bg")) return null;
    
    let wrapper = document.createElement("div");
    wrapper.className = "matrix-bg";
    wrapper.style.cssText = "position:absolute;top:0;left:0;right:0;bottom:0;overflow:hidden;pointer-events:none;z-index:0";
    
    let cv = document.createElement("canvas");
    cv.style.cssText = "display:block;width:100%;height:100%";
    wrapper.appendChild(cv);
    
    if (getComputedStyle(el).position === "static") {
      el.style.position = "relative";
    }
    el.appendChild(wrapper);
    
    return new MatrixRain(cv, opts);
  }
  
  function init() {
    // Login sayfası için - tüm body'ye yağmur
    if (document.querySelector(".login-body")) {
      addRain(".login-body", {
        fs: 16,
        color: "#22d3ee",
        op: 0.18,
        spd: 50
      });
    }
    
    // Dashboard sayfaları için - sidebar ve topbar
    addRain(".sidebar", { fs: 12, color: "#22d3ee", op: 0.12, spd: 70 });
    addRain(".topbar", { fs: 10, color: "#22d3ee", op: 0.08, spd: 60 });
  }
  
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
