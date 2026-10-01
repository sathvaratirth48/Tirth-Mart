const RUPEE = "\u20B9";


/* ----------------------------- Wishlist (backend-backed) ----------------------------- */
function toggleWishServer(id, btnEl) {
  fetch("/api/wishlist/toggle/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: `product_id=${id}`
  })
    .then(res => {
      if (res.status === 302 || res.redirected) {
        window.location.href = "/login/";
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      showToast(data.message);
      updateWishBadge(data.wishlist_count);
      if (btnEl) {
        btnEl.classList.toggle("active", data.added);
        const icon = btnEl.querySelector("i");
        if (icon) icon.className = data.added ? "bi bi-heart-fill" : "bi bi-heart";
      }
    })
    .catch(() => { window.location.href = "/login/"; });
}

function updateWishBadge(count) {
  document.querySelectorAll("[data-wish-badge]")
    .forEach(el => el.textContent = count);
}

/* ----------------------------- AJAX Add To Cart ----------------------------- */
function addToCart(productId) {

  fetch("/api/cart/add/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: `product_id=${productId}`
  })
    .then(res => {
      if (res.redirected || res.status === 302) {
        window.location.href = "/login/";
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (!data) return;
      showToast(data.message);
      updateCartBadge(data.cart_count);
    })
    .catch(() => { window.location.href = "/login/"; });
}

function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");

    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();

      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(
          cookie.substring(name.length + 1)
        );
        break;
      }
    }
  }

  return cookieValue;
}

/* ----------------------------- Cart Functions ----------------------------- */
function loadCart() {

  const wrap = document.getElementById("cartWrap");

  if (!wrap) return;

  fetch("/api/cart/")
    .then(res => res.json())
    .then(data => {

      const cart = data.cart;

      if (!cart.length) {

        wrap.innerHTML = `
            <div class="empty-state text-center">
                <i class="bi bi-cart-x"></i>
                <h3>Your cart is empty</h3>
            </div>`;

        return;
      }

      let rows = "";

      cart.forEach(i => {

        rows += `
            <tr>
                <td>
                    <img src="${i.img}" width="50">
                    ${i.name}
                </td>

                <td>₹${i.price}</td>

                <td>
                    <button onclick="updateQty(${i.id}, ${i.qty - 1})">-</button>

                    ${i.qty}

                    <button onclick="updateQty(${i.id}, ${i.qty + 1})">+</button>
                </td>

                <td>₹${i.subtotal}</td>

                <td>
                    <button onclick="removeItem(${i.id})">
                        🗑
                    </button>
                </td>
            </tr>`;
      });

      wrap.innerHTML = `
        <table class="table">
            <tbody>${rows}</tbody>
        </table>

        <h4>Total: ₹${data.total}</h4>
        `;
    });
}

function loadCartCount() {

  fetch("/api/cart/")
    .then(res => res.json())
    .then(data => {

      let count = 0;

      data.cart.forEach(i => {
        count += i.qty;
      });

      updateCartBadge(count);
    });
}

/* ----------------------------- Add updateQty ----------------------------- */
function updateQty(itemId, qty) {

  fetch("/api/cart/update/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: `item_id=${itemId}&quantity=${qty}`
  })
    .then(res => res.json())
    .then(() => loadCart());
}


/* ----------------------------- Add removeItem ----------------------------- */
function removeItem(itemId) {

  fetch("/api/cart/remove/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: `item_id=${itemId}`
  })
    .then(res => res.json())
    .then(() => loadCart());
}


/* ----------------------------- Badges ----------------------------- */
function updateCartBadge(count) {
  document.querySelectorAll("[data-cart-badge]")
    .forEach(el => el.textContent = count);
}

/* ----------------------------- Toast ----------------------------- */
function showToast(msg) {
  let stack = document.querySelector(".toast-stack");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "toast-stack";
    document.body.appendChild(stack);
  }
  const t = document.createElement("div");
  t.className = "toast-msg";
  t.innerHTML = `<i class="bi bi-check-circle-fill"></i><span>${msg}</span>`;
  stack.appendChild(t);
  setTimeout(() => {
    t.style.transition = "opacity .3s, transform .3s";
    t.style.opacity = "0";
    t.style.transform = "translateX(120%)";
    setTimeout(() => t.remove(), 300);
  }, 2400);
}

/* ----------------------------- Star rendering ----------------------------- */
function starHtml(rating, reviews) {
  let s = "";
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  for (let i = 0; i < 5; i++) {
    if (i < full) s += '<i class="bi bi-star-fill"></i>';
    else if (i === full && half) s += '<i class="bi bi-star-half"></i>';
    else s += '<i class="bi bi-star"></i>';
  }
  return `<div class="stars">${s}${reviews != null ? `<span class="count">(${reviews})</span>` : ""}</div>`;
}


/* ----------------------------- Delegated events ----------------------------- */
document.addEventListener("click", e => {
  const add = e.target.closest(".add-btn");

  if (add) {
    addToCart(add.dataset.id);
    return;
  }


  const wish = e.target.closest(".wish-btn");
  if (wish) {
    toggleWishServer(wish.dataset.id, wish);
    return;
  }

  const quick = e.target.closest(".quick-btn");
  if (quick) { openQuickView(quick.dataset.id); return; }
});

/* ----------------------------- Quick view ----------------------------- */
function openQuickView(id) {
  const p = findProduct(id);
  if (!p) return;
  let modal = document.getElementById("quickModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "quickModal";
    modal.className = "modal fade";
    modal.tabIndex = -1;
    modal.innerHTML = `<div class="modal-dialog modal-lg modal-dialog-centered"><div class="modal-content" style="border:none;border-radius:16px;overflow:hidden"><div class="modal-body p-0" id="quickBody"></div></div></div>`;
    document.body.appendChild(modal);
  }
  const discount = Math.round(((p.old - p.price) / p.old) * 100);
  document.getElementById("quickBody").innerHTML = `
    <button type="button" class="btn-close position-absolute" style="top:14px;right:14px;z-index:5" data-bs-dismiss="modal"></button>
    <div class="row g-0">
      <div class="col-md-5"><div class="pd-gallery-main" style="border-radius:0"><img src="${p.img}" alt="${p.name}"></div></div>
      <div class="col-md-7"><div class="p-4">
        <span class="product-info" style="padding:0"><span class="cat">${p.cat}</span></span>
        <h3 class="mt-1 mb-2">${p.name}</h3>
        ${starHtml(p.rating, p.reviews)}
        <div class="pd-price my-3"><span class="price" style="font-size:1.6rem;color:var(--peacock)">${RUPEE}${p.price}</span>${p.old > p.price ? `<span class="price-old">${RUPEE}${p.old}</span>` : ""}${discount > 0 ? `<span class="badge-pill badge-discount">-${discount}%</span>` : ""}</div>
        <p class="pd-desc">Net weight ${p.weight}. A premium quality treat from Tirth Mart, sourced fresh and delivered to your doorstep.</p>
        <div class="d-flex gap-2 flex-wrap">
          <button class="btn btn-peacock add-btn" data-id="${p.id}"><i class="bi bi-bag-plus"></i> Add to Cart</button>
          <a href="product-details.html?id=${p.id}" class="btn btn-outline-peacock">View Details</a>
        </div>
      </div></div>
    </div>`;
  if (window.bootstrap) new bootstrap.Modal(modal).show();
}

/* ----------------------------- Hero slider ----------------------------- */
function initHero() {
  const slides = document.querySelectorAll(".hero-slide");
  if (!slides.length) return;
  const dots = document.querySelectorAll(".hero-dots span");
  let idx = 0, timer;
  function go(n) {
    slides[idx].classList.remove("active");
    if (dots[idx]) dots[idx].classList.remove("active");
    idx = (n + slides.length) % slides.length;
    slides[idx].classList.add("active");
    if (dots[idx]) dots[idx].classList.add("active");
  }
  function next() { go(idx + 1); }
  function start() { timer = setInterval(next, 5000); }
  function reset() { clearInterval(timer); start(); }

  const nextBtn = document.querySelector(".hero-next");
  const prevBtn = document.querySelector(".hero-prev");
  if (nextBtn) nextBtn.addEventListener("click", () => { next(); reset(); });
  if (prevBtn) prevBtn.addEventListener("click", () => { go(idx - 1); reset(); });
  dots.forEach((d, i) => d.addEventListener("click", () => { go(i); reset(); }));
  start();
}

/* ----------------------------- Tabs ----------------------------- */
function initTabs() {
  const nav = document.querySelector(".tab-nav");
  if (!nav) return;
  nav.addEventListener("click", e => {
    const btn = e.target.closest("button");
    if (!btn) return;
    nav.querySelectorAll("button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const target = btn.dataset.tab;
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.dataset.panel === target));
    initReveal();
  });
}

/* ----------------------------- Testimonials ----------------------------- */
function initTesti() {
  const track = document.querySelector(".testi-track");
  if (!track) return;
  const cards = track.children.length;
  const dots = document.querySelectorAll(".testi-dots span");
  let i = 0, timer;
  function go(n) {
    i = (n + cards) % cards;
    track.style.transform = `translateX(-${i * 100}%)`;
    dots.forEach((d, k) => d.classList.toggle("active", k === i));
  }
  dots.forEach((d, k) => d.addEventListener("click", () => { go(k); reset(); }));
  function start() { timer = setInterval(() => go(i + 1), 4500); }
  function reset() { clearInterval(timer); start(); }
  start();
}

/* ----------------------------- Reveal on scroll ----------------------------- */
let revealObserver;
function initReveal() {
  if (!revealObserver) {
    revealObserver = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add("visible"); revealObserver.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
  }
  document.querySelectorAll(".reveal:not(.visible)").forEach(el => revealObserver.observe(el));
}

/* ----------------------------- Header / loader / drawer ----------------------------- */
function initChrome() {
  // loader
  window.addEventListener("load", () => {
    const loader = document.getElementById("loader");
    if (loader) setTimeout(() => loader.classList.add("hidden"), 500);
  });

  // sticky shadow
  const header = document.querySelector(".site-header");
  const toTop = document.querySelector(".to-top");
  window.addEventListener("scroll", () => {
    if (header) header.classList.toggle("scrolled", window.scrollY > 10);
    if (toTop) toTop.classList.toggle("show", window.scrollY > 400);
  });
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  // drawer
  const drawer = document.querySelector(".mobile-drawer");
  const overlay = document.querySelector(".drawer-overlay");
  const openBtn = document.querySelector(".menu-toggle");
  const closeBtn = document.querySelector(".drawer-close");
  function open() { drawer && drawer.classList.add("open"); overlay && overlay.classList.add("open"); }
  function close() { drawer && drawer.classList.remove("open"); overlay && overlay.classList.remove("open"); }
  if (openBtn) openBtn.addEventListener("click", open);
  if (closeBtn) closeBtn.addEventListener("click", close);
  if (overlay) overlay.addEventListener("click", close);

  // search submit -> shop
  document.querySelectorAll(".search-bar").forEach(bar => {
    bar.addEventListener("submit", e => {
      e.preventDefault();
      const q = bar.querySelector("input").value.trim();
      window.location.href = "shop.html" + (q ? "?q=" + encodeURIComponent(q) : "");
    });
  });

  // newsletter
  document.querySelectorAll(".newsletter-form").forEach(f => {
    f.addEventListener("submit", e => {
      e.preventDefault();
      showToast("Thanks for subscribing to Tirth Mart!");
      f.reset();
    });
  });
}


/* ----------------------------- Page: Checkout ----------------------------- */
// function initCheckout() {
//   const sumWrap = document.getElementById("orderItems");
//   if (!sumWrap) return;
//   sumWrap.innerHTML = cart.map(i => {
//     const p = findProduct(i.id);
//     if (!p) return "";
//     return `<div class="order-item"><img src="${p.img}" alt="${p.name}"><div><div class="oi-name">${p.name}</div><div class="oi-qty">Qty: ${i.qty}</div></div><div class="oi-price">${RUPEE}${p.price * i.qty}</div></div>`;
//   }).join("") || `<p class="text-muted">Your cart is empty. <a href="shop.html">Shop now</a></p>`;

//   const sub = cartSubtotal();
//   const shipping = sub > 499 || sub === 0 ? 0 : 40;
//   const total = sub + shipping;
//   const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
//   set("coSub", RUPEE + sub);
//   set("coShip", shipping === 0 ? "Free" : RUPEE + shipping);
//   set("coTotal", RUPEE + total);

//   document.querySelectorAll(".pay-option").forEach(opt => {
//     opt.addEventListener("click", () => {
//       document.querySelectorAll(".pay-option").forEach(o => o.classList.remove("selected"));
//       opt.classList.add("selected");
//       const radio = opt.querySelector("input");
//       if (radio) radio.checked = true;
//     });
//   });

//   const form = document.getElementById("checkoutForm");
//   if (form) {
//     form.addEventListener("submit", e => {
//       e.preventDefault();
//       if (!form.checkValidity()) { form.reportValidity(); return; }
//       if (!cart.length) { showToast("Your cart is empty"); return; }
//       showToast("Order placed successfully! Thank you.");
//       setTimeout(() => {
//         document.querySelector(".checkout-main").innerHTML = `<div class="empty-state"><i class="bi bi-bag-check" style="color:var(--success)"></i><h3>Order Confirmed!</h3><p>Thank you for shopping with Tirth Mart. A confirmation has been sent to your email.</p><a href="index.html" class="btn btn-peacock"><i class="bi bi-house"></i> Back to Home</a></div>`;
//       }, 1200);
//     });
//   }

//   // contact form (on contact page)
// }

/* ----------------------------- Contact form ----------------------------- */
function initContact() {
  const cf = document.getElementById("contactForm");
  if (!cf) return;
  cf.addEventListener("submit", e => {
    e.preventDefault();
    if (!cf.checkValidity()) { cf.reportValidity(); return; }
    showToast("Message sent! We'll get back to you soon.");
    cf.reset();
  });
}

/* ----------------------------- Init ----------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  initChrome();
  initHero();
  initTabs();
  initTesti();
  loadCart();
  loadCartCount();
  // initCheckout();
  initContact();
  initReveal();
});
