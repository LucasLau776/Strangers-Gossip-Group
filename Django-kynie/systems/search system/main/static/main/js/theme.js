const toggleBtn = document.getElementById('themeToggle'); // Ensure this matches your button ID
const html = document.documentElement;

function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

toggleBtn.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
});

window.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('theme');
    if (saved) {
        setTheme(saved); // Apply the saved theme
    } else {
        setTheme('light'); // Default theme if no saved preference
    }
});
