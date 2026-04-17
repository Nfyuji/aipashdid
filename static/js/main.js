/**
 * PhishDetector — تبديل الوضع الفاتح / الداكن (محفوظ في localStorage)
 */
(function () {
    var KEY = 'phish-theme';

    function currentTheme() {
        var t = document.documentElement.getAttribute('data-theme');
        if (t === 'light' || t === 'dark') return t;
        return 'dark';
    }

    function setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') theme = 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        try {
            localStorage.setItem(KEY, theme);
        } catch (e) { /* ignore */ }
        syncToggleUi();
    }

    function toggleTheme() {
        setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    }

    /** أيقونة الشمس = اضغط للذهاب للفاتح؛ القمر = للداكن */
    function syncToggleUi() {
        var light = currentTheme() === 'light';
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.setAttribute('aria-pressed', light ? 'true' : 'false');
            btn.setAttribute('title', light ? 'الوضع الداكن' : 'الوضع الفاتح');
            btn.setAttribute('aria-label', light ? 'تفعيل الوضع الداكن' : 'تفعيل الوضع الفاتح');
            var icon = btn.querySelector('i');
            if (icon) {
                icon.className = light ? 'fas fa-moon' : 'fas fa-sun';
            }
        });
    }

    window.PhishTheme = {
        setTheme: setTheme,
        toggle: toggleTheme,
        getTheme: currentTheme
    };

    document.addEventListener('DOMContentLoaded', function () {
        syncToggleUi();
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                toggleTheme();
            });
        });
    });

    window.addEventListener('storage', function (e) {
        if (e.key === KEY && (e.newValue === 'light' || e.newValue === 'dark')) {
            document.documentElement.setAttribute('data-theme', e.newValue);
            syncToggleUi();
        }
    });
})();
