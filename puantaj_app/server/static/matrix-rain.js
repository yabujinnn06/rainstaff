(function(){
  const chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン";
  
  class MatrixRain {
    constructor(canvas, opts) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.fontSize = opts.fontSize || 14;
      this.color = opts.color || "#00ff41";
      this.opacity = opts.opacity || 0.15;
      this.speed = opts.speed || 50;
      this.columns = [];
      this.init();
    }
    
    init() {
      this.resize();
      window.addEventListener("resize", () => this.resize());
      this.animate();
    }
    
    resize() {
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;
      const columnCount = Math.floor(this.canvas.width / this.fontSize);
      this.columns = Array(columnCount).fill(0).map(() => Math.random() * -100 | 0);
    }
    
    draw() {
      this.ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      this.ctx.fillStyle = this.color;
      this.ctx.font = this.fontSize + "px monospace";
      this.ctx.globalAlpha = this.opacity;
      
      for (let i = 0; i < this.columns.length; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)];
        const x = i * this.fontSize;
        const y = this.columns[i] * this.fontSize;
        
        this.ctx.fillText(char, x, y);
        
        if (y > this.canvas.height && Math.random() > 0.975) {
          this.columns[i] = 0;
        }
        this.columns[i]++;
      }
      
      this.ctx.globalAlpha = 1;
    }
    
    animate() {
      this.draw();
      setTimeout(() => requestAnimationFrame(() => this.animate()), this.speed);
    }
  }
  
  // Initialize on page load
  window.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('matrix-canvas');
    if (canvas) {
      new MatrixRain(canvas, {
        fontSize: 14,
        color: '#00ff41',
        opacity: 0.15,
        speed: 50
      });
    }
  });
})();
