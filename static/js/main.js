// Toggle mobile menu
const mobileMenuButton = document.getElementById("mobile-menu-button");
const mobileMenu = document.getElementById("mobile-menu");

if (mobileMenuButton && mobileMenu) {
  mobileMenuButton.addEventListener("click", () => {
    mobileMenu.classList.toggle("hidden");
  });

  // Close menu when clicking outside
  document.addEventListener("click", (event) => {
    const isClickInside =
      mobileMenuButton.contains(event.target) ||
      mobileMenu.contains(event.target);

    if (!isClickInside && !mobileMenu.classList.contains("hidden")) {
      mobileMenu.classList.add("hidden");
    }
  });

  // Close menu when resizing to desktop
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 1024) {
      mobileMenu.classList.add("hidden");
    }
  });
}

// Mobile dropdown toggles
const mobileDropdownToggles = document.querySelectorAll('.mobile-dropdown-toggle');

mobileDropdownToggles.forEach(toggle => {
  toggle.addEventListener('click', () => {
    const content = toggle.nextElementSibling;
    const arrow = toggle.querySelector('svg');

    content.classList.toggle('hidden');
    arrow.classList.toggle('rotate-180');
  });
});


/// hero page content slider

