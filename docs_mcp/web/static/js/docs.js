/* ==========================================================================
   Your Docs - Documentation Site JavaScript
   ========================================================================== */

(function () {
  "use strict";

  /* ------------------------------------------------------------------------
     Theme Toggle
     ------------------------------------------------------------------------ */
  function initTheme() {
    var stored = localStorage.getItem("theme");
    var prefersDark =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    var theme = stored || (prefersDark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
    updateThemeIcon(theme);
  }

  function updateThemeIcon(theme) {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    btn.textContent = theme === "dark" ? "\u2600\uFE0F" : "\uD83C\uDF19";
    btn.setAttribute(
      "aria-label",
      theme === "dark" ? "Switch to light theme" : "Switch to dark theme"
    );
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute("data-theme");
    var next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeIcon(next);
  }

  /* ------------------------------------------------------------------------
     Mobile Menu
     ------------------------------------------------------------------------ */
  function initMobileMenu() {
    var menuBtn = document.querySelector(".mobile-menu-btn");
    var sidebar = document.querySelector(".sidebar");
    if (!menuBtn || !sidebar) return;

    // Create overlay element if it does not exist
    var overlay = document.querySelector(".sidebar-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "sidebar-overlay";
      document.body.appendChild(overlay);
    }

    function openSidebar() {
      sidebar.classList.add("open");
      overlay.classList.add("active");
      menuBtn.setAttribute("aria-expanded", "true");
    }

    function closeSidebar() {
      sidebar.classList.remove("open");
      overlay.classList.remove("active");
      menuBtn.setAttribute("aria-expanded", "false");
    }

    menuBtn.addEventListener("click", function () {
      var isOpen = sidebar.classList.contains("open");
      if (isOpen) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    // Close when clicking outside (on the overlay)
    overlay.addEventListener("click", closeSidebar);

    // Escape key closes sidebar
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("open")) {
        closeSidebar();
      }
    });
  }

  /* ------------------------------------------------------------------------
     Copy Button for Code Blocks
     ------------------------------------------------------------------------ */
  function initCopyButtons() {
    var codeBlocks = document.querySelectorAll("pre > code");

    codeBlocks.forEach(function (codeEl) {
      var pre = codeEl.parentElement;
      // Skip if a copy button already exists (e.g., server-rendered)
      if (pre.querySelector(".copy-btn")) return;

      var btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.textContent = "Copy";
      btn.type = "button";
      btn.setAttribute("aria-label", "Copy code to clipboard");

      // Position the button inside the pre block
      pre.style.position = "relative";
      btn.style.position = "absolute";
      btn.style.top = "8px";
      btn.style.right = "8px";

      btn.addEventListener("click", function () {
        var text = codeEl.textContent;
        navigator.clipboard.writeText(text).then(
          function () {
            btn.textContent = "Copied!";
            btn.classList.add("copied");
            setTimeout(function () {
              btn.textContent = "Copy";
              btn.classList.remove("copied");
            }, 2000);
          },
          function () {
            // Fallback for older browsers
            var textarea = document.createElement("textarea");
            textarea.value = text;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.select();
            try {
              document.execCommand("copy");
              btn.textContent = "Copied!";
              btn.classList.add("copied");
              setTimeout(function () {
                btn.textContent = "Copy";
                btn.classList.remove("copied");
              }, 2000);
            } catch (_) {
              btn.textContent = "Error";
            }
            document.body.removeChild(textarea);
          }
        );
      });

      pre.appendChild(btn);
    });
  }

  /* ------------------------------------------------------------------------
     Page TOC Active State (IntersectionObserver)
     ------------------------------------------------------------------------ */
  function initTocActiveState() {
    var tocLinks = document.querySelectorAll(".page-toc a");
    if (!tocLinks.length) return;

    // Gather all heading IDs referenced by the TOC links
    var headingIds = [];
    tocLinks.forEach(function (link) {
      var href = link.getAttribute("href");
      if (href && href.startsWith("#")) {
        headingIds.push(href.substring(1));
      }
    });

    if (!headingIds.length) return;

    var headings = headingIds
      .map(function (id) {
        return document.getElementById(id);
      })
      .filter(Boolean);

    if (!headings.length) return;

    // Track visible headings
    var visibleHeadings = new Set();

    function updateActiveLink() {
      // Find the topmost visible heading
      var active = null;
      for (var i = 0; i < headings.length; i++) {
        if (visibleHeadings.has(headings[i].id)) {
          active = headings[i].id;
          break;
        }
      }

      // If none visible, find the last heading above the viewport center
      if (!active) {
        var scrollY = window.scrollY + 120;
        for (var j = headings.length - 1; j >= 0; j--) {
          if (headings[j].offsetTop <= scrollY) {
            active = headings[j].id;
            break;
          }
        }
      }

      tocLinks.forEach(function (link) {
        var href = link.getAttribute("href");
        if (href === "#" + active) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      });
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            visibleHeadings.add(entry.target.id);
          } else {
            visibleHeadings.delete(entry.target.id);
          }
        });
        updateActiveLink();
      },
      {
        rootMargin: "-80px 0px -60% 0px",
        threshold: 0,
      }
    );

    headings.forEach(function (heading) {
      observer.observe(heading);
    });
  }

  /* ------------------------------------------------------------------------
     Search Keyboard Shortcut
     ------------------------------------------------------------------------ */
  function initSearchShortcut() {
    var searchInput = document.querySelector(".search-input");
    if (!searchInput) return;

    document.addEventListener("keydown", function (e) {
      // "/" focuses search (unless user is already typing in an input)
      if (
        e.key === "/" &&
        !isInputFocused()
      ) {
        e.preventDefault();
        searchInput.focus();
      }

      // Escape blurs search input
      if (e.key === "Escape" && document.activeElement === searchInput) {
        searchInput.blur();
      }
    });
  }

  function isInputFocused() {
    var el = document.activeElement;
    if (!el) return false;
    var tag = el.tagName.toLowerCase();
    return (
      tag === "input" ||
      tag === "textarea" ||
      tag === "select" ||
      el.isContentEditable
    );
  }

  /* ------------------------------------------------------------------------
     Sidebar Nav Toggles (Collapsible Sections)
     ------------------------------------------------------------------------ */
  function initNavToggles() {
    var toggles = document.querySelectorAll(".nav-toggle");

    toggles.forEach(function (toggle) {
      toggle.addEventListener("click", function () {
        var expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));

        // Find the next sibling that is .nav-children
        var children = toggle.nextElementSibling;
        if (children && children.classList.contains("nav-children")) {
          children.style.display = expanded ? "none" : "block";
        }
      });
    });
  }

  /* ------------------------------------------------------------------------
     Initialize Everything on DOMContentLoaded
     ------------------------------------------------------------------------ */
  function init() {
    initTheme();
    initMobileMenu();
    initCopyButtons();
    initTocActiveState();
    initSearchShortcut();
    initNavToggles();
  }

  // Apply theme immediately to avoid flash of wrong theme
  initTheme();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-init copy buttons after HTMX content swaps
  document.addEventListener("htmx:afterSwap", function () {
    initCopyButtons();
    initTocActiveState();
    initNavToggles();
  });

  // Expose theme toggle for the button's onclick
  window.toggleTheme = toggleTheme;
})();
