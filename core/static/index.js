function checkPasswordStrength(password) {
    const strengthLabel = document.getElementById('strength-label');
    const strengthBar = document.getElementById('strength-bar');
    const passwordStrengthContainer = document.getElementById('password-strength');

    // Show or hide the strength container based on password length
    if (password.length === 0) {
        passwordStrengthContainer.style.display = 'none';
        return;
    } else {
        passwordStrengthContainer.style.display = 'block';
    }

    // Criteria for password strength
    const criteria = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        digit: /\d/.test(password),
        specialChar: /[!@#$%^&*()\-_=+]/.test(password),
    };

    // Count fulfilled criteria
    const fulfilledCriteria = Object.values(criteria).filter(Boolean).length;

    let strength = 'Weak';
    let strengthPercentage = 0;

    // Determine strength and percentage
    if (fulfilledCriteria === 5) {
        strength = 'Strong';
        strengthPercentage = 100;
    } else if (fulfilledCriteria >= 3) {
        strength = 'Moderate';
        strengthPercentage = 60;
    } else {
        strength = 'Weak';
        strengthPercentage = 30;
    }

    // Update the strength label and progress bar
    strengthLabel.textContent = strength;
    strengthBar.style.width = `${strengthPercentage}%`;
    strengthBar.className = `progress-bar ${
        strength === 'Strong' ? 'bg-success' : strength === 'Moderate' ? 'bg-warning' : 'bg-danger'
    }`;
}

// Hide the password strength container by default
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('password-strength').style.display = 'none';
});