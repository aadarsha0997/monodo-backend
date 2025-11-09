document.addEventListener("DOMContentLoaded", () => {
  const nav = document.querySelector(".navbar-nav.ms-auto, .navbar-nav.me-auto");
  if (!nav) {
    return;
  }

  const storageKey = "jazzmin_nav_hidden";
  const hiddenSet = new Set(JSON.parse(localStorage.getItem(storageKey) || "[]"));

  const persistHidden = () => {
    localStorage.setItem(storageKey, JSON.stringify(Array.from(hiddenSet)));
  };

  const getNavId = (item) => {
    const link = item.querySelector("a.nav-link, a.dropdown-toggle");
    if (!link) {
      return null;
    }
    return link.textContent.trim().toLowerCase().replace(/\s+/g, "-");
  };

  const addCloseButton = (item) => {
    if (item.querySelector(".nav-close-btn")) {
      return;
    }

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "nav-close-btn";
    closeBtn.setAttribute("aria-label", "Hide navigation item");
    closeBtn.innerHTML = "&times;";

    closeBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const id = getNavId(item);
      if (!id) {
        return;
      }
      item.classList.add("nav-hidden");
      hiddenSet.add(id);
      persistHidden();
    });

    const link = item.querySelector("a.nav-link, a.dropdown-toggle");
    if (link) {
      link.appendChild(closeBtn);
    } else {
      item.appendChild(closeBtn);
    }
  };

  Array.from(nav.children).forEach((item) => {
    if (!item.classList.contains("nav-item")) {
      return;
    }

    const id = getNavId(item);
    if (!id) {
      return;
    }

    item.dataset.navId = id;
    addCloseButton(item);

    if (hiddenSet.has(id)) {
      item.classList.add("nav-hidden");
    }
  });

  const restoreBtn = document.createElement("button");
  restoreBtn.type = "button";
  restoreBtn.className = "btn btn-sm btn-outline-light nav-restore-btn";
  restoreBtn.textContent = "Restore Shortcuts";

  restoreBtn.addEventListener("click", () => {
    hiddenSet.clear();
    persistHidden();
    Array.from(nav.children).forEach((item) => item.classList.remove("nav-hidden"));
  });

  const navbar = document.querySelector(".navbar");
  if (navbar && !navbar.querySelector(".nav-restore-btn")) {
    navbar.appendChild(restoreBtn);
  }
});

