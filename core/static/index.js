function checkPasswordStrength(password) {
  if (password == null) {
    console.error("Password is null or undefined");
    return;
  }
  const strengthLabel = document.getElementById("strength-label");
  const strengthBar = document.getElementById("strength-bar");
  const passwordStrengthContainer =
    document.getElementById("password-strength");

  // Show or hide the strength container based on password length
  if (password.length === 0) {
    passwordStrengthContainer.style.display = "none";
    return;
  } else {
    passwordStrengthContainer.style.display = "block";
  }

  // Criteria for password strength
  const criteria = {
    specialChar: /[!@#$%^&*()\-_=+\[\]{};:'",.<>?\\|`~]/.test(password),
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    digit: /\d/.test(password),
    specialChar: /[!@#$%^&*()\-_=+]/.test(password),
  };

  // Count fulfilled criteria
  const fulfilledCriteria = Object.values(criteria).filter(Boolean).length;

  let strength = "Weak";
  let strengthPercentage = 0;

  // Determine strength and percentage
  if (fulfilledCriteria === 5) {
    strength = "Strong";
    strengthPercentage = 100;
  } else if (fulfilledCriteria >= 3) {
    strength = "Moderate";
    strengthPercentage = 60;
  } else {
    strength = "Weak";
    strengthPercentage = 30;
  }

  // Update the strength label and progress bar
  strengthLabel.textContent = strength;
  strengthBar.style.width = `${strengthPercentage}%`;
  strengthBar.className = `progress-bar ${getStrengthClass(strength)}`;
}

// Function to get the class name based on strength
function getStrengthClass(strength) {
  switch (strength) {
    case "Strong":
      return "bg-success";
    case "Moderate":
      return "bg-warning";
    default:
      return "bg-danger";
  }
}
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("password-strength").style.display = "none";
});

// Function to check if an element is in the viewport
function isInViewport(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

// Animate feature cards on scroll
const featureItems = document.querySelectorAll(".feature-item");

function handleScroll() {
  featureItems.forEach((item) => {
    if (isInViewport(item)) {
      item.classList.add("in-view");
    }
  });
}

// Debounce function to limit the rate at which a function can fire
function debounce(func, wait) {
  let timeout;
  return function (...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}

// Listen for scroll events with debounce
window.addEventListener("scroll", debounce(handleScroll, 100));
const menuToggle = document.getElementById("menu-toggle");
menuToggle.addEventListener("click", () => {
  if (mobileNav && menuToggleIcon) {
    mobileNav.classList.toggle("open");
    menuToggleIcon.classList.toggle("fa-bars");
    menuToggleIcon.classList.toggle("fa-times");
  }
});
const navList = document.getElementById("nav-list");
const closeMenu = document.getElementById("close-icon");
const mobileNav = document.querySelector(".mobile-nav");
const menuToggleIcon = document.getElementById("menu-toggle-icon");
closeMenu.addEventListener("click", () => {
  mobileNav.classList.remove("open");
  menuToggleIcon.classList.add("fa-bars");
  menuToggleIcon.classList.remove("fa-times");
});

// coming soon page

// Set the date we're counting down to
const countDownDate = new Date("Dec 31, 2025 23:59:59").getTime();

// Update the count down every 1 second
const countdownfunction = setInterval(() => {
    // Get today's date and time
    const now = new Date().getTime();

    // Find the distance between now and the count down date
    const distance = countDownDate - now;

    // Time calculations for days, hours, minutes and seconds
    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    // Output the result in an element with id="days", "hours", "minutes", "seconds"
    document.getElementById("days").innerText = days;
    document.getElementById("hours").innerText = hours;
    document.getElementById("minutes").innerText = minutes;
    document.getElementById("seconds").innerText = seconds;

    // If the count down is over, write some text
    if (distance < 0) {
        clearInterval(countdownfunction);
        document.querySelector(".countdown").innerHTML = "We have launched!";
    }
}, 1000);


document.addEventListener("DOMContentLoaded", function () {
  const features = document.querySelectorAll(".feature-card");
  features.forEach((feature, index) => {
      setTimeout(() => {
          feature.classList.add("fade-in");
      }, index * 200);
  });
});
