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

    function initSidebarNav() {
        var body = document.body;
        var toggle = document.querySelector('[data-sidebar-toggle]');
        var backdrop = document.querySelector('.sidebar-backdrop');
        var sidebar = document.getElementById('sidebar');
        if (!toggle || !sidebar) return;

        function setOpen(open) {
            if (open) {
                body.classList.add('nav-sidebar-open');
                toggle.setAttribute('aria-expanded', 'true');
                if (backdrop) backdrop.setAttribute('aria-hidden', 'false');
            } else {
                body.classList.remove('nav-sidebar-open');
                toggle.setAttribute('aria-expanded', 'false');
                if (backdrop) backdrop.setAttribute('aria-hidden', 'true');
            }
        }

        function isMobileNav() {
            return window.matchMedia('(max-width: 768px)').matches;
        }

        toggle.addEventListener('click', function () {
            if (!isMobileNav()) return;
            setOpen(!body.classList.contains('nav-sidebar-open'));
        });

        document.querySelectorAll('[data-sidebar-close]').forEach(function (el) {
            el.addEventListener('click', function () {
                setOpen(false);
            });
        });

        sidebar.querySelectorAll('a.nav-link, .sidebar-footer a').forEach(function (a) {
            a.addEventListener('click', function () {
                if (isMobileNav()) setOpen(false);
            });
        });

        window.addEventListener('resize', function () {
            if (!isMobileNav()) setOpen(false);
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && body.classList.contains('nav-sidebar-open')) {
                setOpen(false);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        syncToggleUi();
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                toggleTheme();
            });
        });
        initSidebarNav();
    });

    window.addEventListener('storage', function (e) {
        if (e.key === KEY && (e.newValue === 'light' || e.newValue === 'dark')) {
            document.documentElement.setAttribute('data-theme', e.newValue);
            syncToggleUi();
        }
    });
})();
