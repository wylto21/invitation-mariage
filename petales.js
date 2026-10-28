/* ============================================================
   Pétales et petits cœurs qui tombent sur tout le site.
   Un seul <canvas> fixe, transparent aux clics, au-dessus du contenu
   mais sous l'en-tête et les fenêtres (z-index réglable :
   <script src="petales.js" data-z="45" defer>).
   Rien ne s'anime si l'appareil demande de réduire les animations.
   ============================================================ */
(function () {
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var script = document.currentScript;
  var cv = document.createElement('canvas');
  cv.setAttribute('aria-hidden', 'true');
  cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:' +
    ((script && script.dataset.z) || 45);
  document.body.appendChild(cv);
  var ctx = cv.getContext('2d');

  /* ——— sprites pré-dessinés : pétales terracotta et cœurs ——— */
  var S = 64;
  function sprite(draw) {
    var c = document.createElement('canvas');
    c.width = c.height = S;
    draw(c.getContext('2d'));
    return c;
  }
  function petal(c1, c2) {
    return sprite(function (g) {
      var grad = g.createRadialGradient(S * .42, S * .38, 2, S / 2, S / 2, S * .5);
      grad.addColorStop(0, c1); grad.addColorStop(1, c2);
      g.fillStyle = grad;
      g.beginPath();
      g.moveTo(S / 2, S * .06);
      g.bezierCurveTo(S * .92, S * .2, S * .86, S * .78, S / 2, S * .95);
      g.bezierCurveTo(S * .14, S * .78, S * .08, S * .2, S / 2, S * .06);
      g.fill();
      g.strokeStyle = 'rgba(255,255,255,.35)'; g.lineWidth = 1.4;
      g.beginPath(); g.moveTo(S / 2, S * .16); g.quadraticCurveTo(S * .54, S * .5, S / 2, S * .86); g.stroke();
    });
  }
  function heart(c1, c2) {
    return sprite(function (g) {
      var grad = g.createLinearGradient(0, 0, S, S);
      grad.addColorStop(0, c1); grad.addColorStop(1, c2);
      g.fillStyle = grad;
      g.beginPath();
      g.moveTo(S / 2, S * .9);
      g.bezierCurveTo(S * .06, S * .58, S * .04, S * .14, S * .3, S * .14);
      g.bezierCurveTo(S * .42, S * .14, S * .5, S * .24, S / 2, S * .32);
      g.bezierCurveTo(S * .5, S * .24, S * .58, S * .14, S * .7, S * .14);
      g.bezierCurveTo(S * .96, S * .14, S * .94, S * .58, S / 2, S * .9);
      g.fill();
      g.fillStyle = 'rgba(255,255,255,.4)';
      g.beginPath(); g.ellipse(S * .32, S * .3, S * .07, S * .045, -.6, 0, Math.PI * 2); g.fill();
    });
  }
  var PETALS = [
    petal('#d98a62', '#b85c38'),
    petal('#e8b59a', '#c97b4e'),
    petal('#c46a43', '#8a3416'),
    petal('#f3d3bf', '#e0a383')
  ];
  var HEARTS = [
    heart('#e8cd97', '#a8761f'),
    heart('#e39a78', '#b85c38'),
    heart('#f0c2ab', '#d0805c')
  ];

  var W, H, dpr, items = [];
  function rand(a, b) { return a + Math.random() * (b - a); }
  function make(anywhere) {
    var isHeart = Math.random() < .28;
    var size = isHeart ? rand(11, 19) : rand(13, 24);
    return {
      img: isHeart ? HEARTS[(Math.random() * HEARTS.length) | 0] : PETALS[(Math.random() * PETALS.length) | 0],
      heart: isHeart,
      size: size,
      x: rand(0, W),
      y: anywhere ? rand(-H * .1, H) : rand(-60, -20),
      vy: rand(.35, .9) * (size / 14),
      sway: rand(14, 42),
      freq: rand(.004, .011),
      phase: rand(0, Math.PI * 2),
      rot: rand(0, Math.PI * 2),
      vr: rand(-.02, .02),
      flip: rand(.01, .03),
      alpha: rand(.55, .9)
    };
  }
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = innerWidth; H = innerHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var n = Math.round(Math.min(34, Math.max(14, W * H / 30000)));
    while (items.length < n) items.push(make(true));
    items.length = n;
  }

  var t = 0, running = true, last = 0;
  function frame(now) {
    if (!running) return;
    var dt = last ? Math.min(3, (now - last) / 16.7) : 1;
    last = now; t += dt;
    ctx.clearRect(0, 0, W, H);
    for (var i = 0; i < items.length; i++) {
      var p = items[i];
      p.y += p.vy * dt;
      p.rot += p.vr * dt;
      var x = p.x + Math.sin(t * p.freq + p.phase) * p.sway;
      if (p.y > H + 30) { items[i] = make(false); continue; }
      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.translate(x, p.y);
      ctx.rotate(p.heart ? Math.sin(t * p.freq * 2 + p.phase) * .35 : p.rot);
      /* les pétales tournoient (retournement), les cœurs se balancent */
      ctx.scale(p.heart ? 1 : Math.max(.15, Math.abs(Math.cos(t * p.flip + p.phase))), 1);
      ctx.drawImage(p.img, -p.size / 2, -p.size / 2, p.size, p.size);
      ctx.restore();
    }
    requestAnimationFrame(frame);
  }

  addEventListener('resize', resize);
  document.addEventListener('visibilitychange', function () {
    running = !document.hidden;
    if (running) { last = 0; requestAnimationFrame(frame); }
  });
  resize();
  requestAnimationFrame(frame);
})();
