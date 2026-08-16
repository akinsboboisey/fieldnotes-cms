// Reading progress bar, driven by scroll position over the post body.
(function () {
  const fill = document.getElementById("progressFill");
  const article = document.querySelector(".post-full");
  if (!fill || !article) return;

  function update() {
    const rect = article.getBoundingClientRect();
    const total = rect.height - window.innerHeight;
    const scrolled = Math.min(Math.max(-rect.top, 0), total);
    const pct = total > 0 ? (scrolled / total) * 100 : 0;
    fill.style.width = pct + "%";
  }

  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
})();

// Copy-to-clipboard button on fenced code blocks.
(function () {
  document.querySelectorAll(".post-body pre").forEach((pre) => {
    const btn = document.createElement("button");
    btn.textContent = "copy";
    btn.className = "link-btn";
    btn.style.position = "absolute";
    btn.style.top = "10px";
    btn.style.right = "12px";
    btn.style.fontSize = "0.72rem";
    pre.style.position = "relative";
    btn.addEventListener("click", () => {
      const code = pre.querySelector("code");
      navigator.clipboard.writeText(code ? code.innerText : pre.innerText);
      btn.textContent = "copied";
      setTimeout(() => (btn.textContent = "copy"), 1200);
    });
    pre.appendChild(btn);
  });
})();
