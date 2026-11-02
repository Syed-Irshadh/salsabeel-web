// Salsabeel Academy - Main Frontend Script & Design System

// Global Toast Notification Helper
window.showToast = function(message, type = 'info', duration = 3800) {
    const container = document.getElementById('toastContainer');
    if (!container) {
        console.warn('Toast:', message);
        return;
    }
    const toast = document.createElement('div');
    toast.className = 'toast-item pointer-events-auto flex items-start p-4 rounded-2xl shadow-xl border text-sm transition-all duration-300 transform';
    
    let iconClass = 'fa-info-circle text-navy';
    let bgBorder = 'bg-white border-gray-200 text-gray-800';
    
    if (type === 'success') {
        iconClass = 'fa-check-circle text-emerald';
        bgBorder = 'bg-white border-emerald/50 text-gray-800 shadow-glow-teal';
    } else if (type === 'error') {
        iconClass = 'fa-exclamation-circle text-red-500';
        bgBorder = 'bg-white border-red-200 text-gray-800 shadow-lg';
    } else if (type === 'warning') {
        iconClass = 'fa-exclamation-triangle text-amber-500';
        bgBorder = 'bg-white border-amber-300 text-gray-800 shadow-glow-gold';
    }
    
    toast.className += ` ${bgBorder}`;
    toast.innerHTML = `
        <div class="mr-3 text-lg flex-shrink-0 mt-0.5">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="flex-grow pr-2 leading-relaxed">
            ${message}
        </div>
        <button type="button" class="text-gray-400 hover:text-gray-700 ml-2 text-sm cursor-pointer p-0.5" aria-label="Close">
            <i class="fas fa-times"></i>
        </button>
    `;

    const closeBtn = toast.querySelector('button');
    let dismissed = false;
    function dismissToast() {
        if (dismissed) return;
        dismissed = true;
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%) scale(0.95)';
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
    }
    if (closeBtn) closeBtn.addEventListener('click', dismissToast);
    container.appendChild(toast);
    setTimeout(dismissToast, duration);
};

// Global Custom Confirmation Modal Helper
window.confirmModal = function({ title, message, confirmText = 'Confirm', cancelText = 'Cancel', isDestructive = false, onConfirm }) {
    const modal = document.getElementById('customConfirmModal');
    if (!modal) {
        if (window.confirm(message)) {
            if (onConfirm) onConfirm();
        }
        return;
    }
    const lastActiveConfirmTrigger = document.activeElement;
    const titleEl = document.getElementById('confirmModalTitle');
    const msgEl = document.getElementById('confirmModalMessage');
    const confirmBtn = document.getElementById('confirmModalConfirmBtn');
    const cancelBtn = document.getElementById('confirmModalCancelBtn');
    const backdrop = document.getElementById('confirmModalBackdrop');
    const icon = document.getElementById('confirmModalIcon');
    const iconBg = document.getElementById('confirmModalIconBg');

    if (titleEl) titleEl.textContent = title || 'Confirm Action';
    if (msgEl) msgEl.textContent = message || 'Are you sure you want to proceed?';
    if (confirmBtn) {
        confirmBtn.textContent = confirmText;
        if (isDestructive) {
            confirmBtn.className = 'w-full sm:w-auto px-5 py-2 text-sm font-bold text-white bg-red-600 hover:bg-red-700 rounded-xl transition-all shadow-sm cursor-pointer text-center';
        } else {
            confirmBtn.className = 'w-full sm:w-auto px-5 py-2 text-sm font-bold text-white bg-navy hover:bg-teal-700 rounded-xl transition-all shadow-sm cursor-pointer text-center';
        }
    }
    if (cancelBtn) cancelBtn.textContent = cancelText;

    if (icon && iconBg) {
        if (isDestructive) {
            icon.className = 'fas fa-trash-alt text-red-500';
            iconBg.className = 'w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center flex-shrink-0 text-lg sm:text-xl';
        } else {
            icon.className = 'fas fa-question-circle text-gold';
            iconBg.className = 'w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-amber-50 border border-gold/40 flex items-center justify-center flex-shrink-0 text-lg sm:text-xl';
        }
    }

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    if (confirmBtn) setTimeout(() => confirmBtn.focus(), 60);

    function closeModal() {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        if (confirmBtn) confirmBtn.removeEventListener('click', handleConfirm);
        if (cancelBtn) cancelBtn.removeEventListener('click', closeModal);
        if (backdrop) backdrop.removeEventListener('click', closeModal);
        if (lastActiveConfirmTrigger && typeof lastActiveConfirmTrigger.focus === 'function') {
            lastActiveConfirmTrigger.focus();
        }
    }

    function handleConfirm() {
        closeModal();
        if (typeof onConfirm === 'function') onConfirm();
    }

    if (confirmBtn) confirmBtn.addEventListener('click', handleConfirm, { once: true });
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal, { once: true });
    if (backdrop) backdrop.addEventListener('click', closeModal, { once: true });
};

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // Session Expiration & Inactivity Auto-Logout Configuration
    // -------------------------------------------------------------
    const SESSION_MAX_DURATION_MS = 60 * 60 * 1000; // 60 minutes absolute session validity
    const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000;   // 30 minutes idle inactivity auto-logout

    function clearSessionState() {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('userId');
        localStorage.removeItem('userName');
        localStorage.removeItem('login_time');
        localStorage.removeItem('last_activity');
    }

    // Automated test helper for visual inspection across roles
    const devUrlParams = new URLSearchParams(window.location.search);
    if (devUrlParams.get('test_role')) {
        localStorage.setItem('token', 'dev_test_token_active');
        localStorage.setItem('role', devUrlParams.get('test_role'));
        localStorage.setItem('userName', devUrlParams.get('test_role') === 'admin' ? 'Admin Salsabeel' : 'Test Student');
        localStorage.setItem('login_time', Date.now().toString());
        localStorage.setItem('last_activity', Date.now().toString());
    } else if (devUrlParams.has('test_logout')) {
        clearSessionState();
    }

    // Authoritative in-memory authentication state & popup timer
    window.__authStatus = {
        state: 'pending', // 'pending' | 'verifying' | 'resolved' | 'unavailable' | 'offline'
        isAuthenticated: false,
        hasToken: Boolean(localStorage.getItem('token')),
        user: null
    };

    window.__promoPopupTimer = null;

    window.__authReady = (async function syncBackendAuthStatus() {
        const storedToken = localStorage.getItem('token');
        if (!storedToken) {
            window.__authStatus = {
                state: 'resolved',
                isAuthenticated: false,
                hasToken: false,
                user: null
            };
            return window.__authStatus;
        }

        if (storedToken === 'dev_test_token_active') {
            window.__authStatus = {
                state: 'resolved',
                isAuthenticated: true,
                hasToken: true,
                user: {
                    role: localStorage.getItem('role') || 'student',
                    name: localStorage.getItem('userName') || 'Test User'
                }
            };
            return window.__authStatus;
        }

        window.__authStatus.state = 'verifying';
        try {
            const res = await fetch('/api/auth/status', {
                headers: { 'Authorization': `Bearer ${storedToken}` }
            });

            if (res.status === 200) {
                const data = await res.json();
                window.__authStatus = {
                    state: 'resolved',
                    isAuthenticated: true,
                    hasToken: true,
                    user: data.user
                };
            } else if (res.status === 401) {
                // Token confirmed invalid or expired -> clear stale storage
                clearSessionState();
                window.__authStatus = {
                    state: 'resolved',
                    isAuthenticated: false,
                    hasToken: false,
                    user: null
                };
            } else {
                // HTTP 500, 502, 503 or other server error -> DO NOT CLEAR TOKEN!
                // Suppress automatic promotional popups
                window.__authStatus = {
                    state: 'unavailable',
                    isAuthenticated: false,
                    hasToken: true,
                    user: null
                };
            }
        } catch (netErr) {
            // Network / connectivity failure -> DO NOT CLEAR TOKEN!
            // Suppress automatic promotional popups
            window.__authStatus = {
                state: 'offline',
                isAuthenticated: false,
                hasToken: true,
                user: null
            };
        }
        return window.__authStatus;
    })();

    // Promotional Popup Gatekeeper
    async function canTriggerPromotionalGiftPopup() {
        if (window.location.pathname.startsWith('/admin')) return false;
        if (window.__authReady) {
            await window.__authReady;
        }
        if (window.__authStatus && window.__authStatus.isAuthenticated) return false;
        if (window.__authStatus && (window.__authStatus.state === 'unavailable' || window.__authStatus.state === 'offline') && window.__authStatus.hasToken) {
            return false;
        }
        const role = localStorage.getItem('role');
        if (role === 'student' || role === 'admin') return false;
        if (localStorage.getItem('token')) return false;

        return Boolean(window.__authStatus && window.__authStatus.state === 'resolved' && !window.__authStatus.isAuthenticated && !window.__authStatus.hasToken);
    }
    window.canTriggerPromotionalGiftPopup = canTriggerPromotionalGiftPopup;

    // Verify session validity upon page load
    let token = localStorage.getItem('token');
    const userRole = localStorage.getItem('role');
    const userId = localStorage.getItem('userId');
    const now = Date.now();

    if (token) {
        const loginTime = parseInt(localStorage.getItem('login_time') || '0', 10);
        const lastActivity = parseInt(localStorage.getItem('last_activity') || '0', 10);

        if (loginTime > 0 && (now - loginTime > SESSION_MAX_DURATION_MS)) {
            clearSessionState();
            token = null;
            setTimeout(() => {
                showToast('Your session has expired. Please sign in again.', 'warning', 4500);
            }, 300);
        } else if (lastActivity > 0 && (now - lastActivity > INACTIVITY_TIMEOUT_MS)) {
            clearSessionState();
            token = null;
            setTimeout(() => {
                showToast('You were signed out due to 30 minutes of inactivity.', 'warning', 4500);
            }, 300);
        } else {
            // Refresh activity timestamp on load
            localStorage.setItem('last_activity', now.toString());
        }
    }

    // Rolling user activity listener to prevent abrupt timeout while active
    if (token) {
        let throttleTimer = null;
        const recordUserActivity = () => {
            if (throttleTimer) return;
            throttleTimer = setTimeout(() => {
                localStorage.setItem('last_activity', Date.now().toString());
                throttleTimer = null;
            }, 5000); // Throttle activity updates to once every 5 seconds
        };

        ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(evt => {
            window.addEventListener(evt, recordUserActivity, { passive: true });
        });

        // Periodic inactivity watchdog (checks every 60 seconds)
        setInterval(() => {
            const currentToken = localStorage.getItem('token');
            if (!currentToken) return;

            const curNow = Date.now();
            const curLoginTime = parseInt(localStorage.getItem('login_time') || '0', 10);
            const curLastAct = parseInt(localStorage.getItem('last_activity') || '0', 10);

            if (curLoginTime > 0 && (curNow - curLoginTime > SESSION_MAX_DURATION_MS)) {
                clearSessionState();
                showToast('Session expired. Please sign in again.', 'warning');
                setTimeout(() => window.location.reload(), 1200);
            } else if (curLastAct > 0 && (curNow - curLastAct > INACTIVITY_TIMEOUT_MS)) {
                clearSessionState();
                showToast('Signed out due to inactivity.', 'warning');
                setTimeout(() => window.location.reload(), 1200);
            }
        }, 60000);
    }

    // -------------------------------------------------------------
    // Top Navbar & Auth State Controls
    // -------------------------------------------------------------
    // Auth Buttons across all navigation containers
    const loginBtns = [
        document.getElementById('topLoginBtn'),
        document.getElementById('mobileLoginBtn'),
        document.getElementById('mobileDrawerLoginBtn'),
        document.getElementById('sidebarLoginBtn'),
        document.getElementById('loginBtn')
    ].filter(Boolean);

    const logoutBtns = [
        document.getElementById('topLogoutBtn'),
        document.getElementById('mobileLogoutBtn'),
        document.getElementById('mobileDrawerLogoutBtn'),
        document.getElementById('sidebarLogoutBtn'),
        document.getElementById('logoutBtn')
    ].filter(Boolean);

    const adminBtns = [
        document.getElementById('topAdminBtn'),
        document.getElementById('mobileAdminBtn'),
        document.getElementById('mobileDrawerAdminBtn'),
        document.getElementById('sidebarAdminBtn'),
        document.getElementById('adminBtn')
    ].filter(Boolean);

    const deleteCourseBtns = document.querySelectorAll('.delete-course-btn');

    // 1. Deterministic Navigation Route Detection & Active State Sync
    function detectActiveNavSection(rawPath) {
        if (!rawPath) return null;
        const cleanPath = rawPath.split('?')[0].split('#')[0].replace(/\/+$/, '') || '/';
        if (cleanPath === '/' || cleanPath === '/index.html') {
            return 'home';
        }
        if (cleanPath === '/courses' || 
            cleanPath.startsWith('/courses/') || 
            cleanPath.startsWith('/viewer/') || 
            cleanPath.startsWith('/course/')) {
            return 'courses';
        }
        if (cleanPath === '/about' || cleanPath.startsWith('/about/')) {
            return 'about';
        }
        if (cleanPath === '/admissions' || cleanPath.startsWith('/admissions/')) {
            return 'admissions';
        }
        if (cleanPath === '/updates' || cleanPath.startsWith('/updates/')) {
            return 'updates';
        }
        if (cleanPath === '/admin' || cleanPath.startsWith('/admin/')) {
            return 'admin';
        }
        return null;
    }

    function syncActiveNavState() {
        const activeSection = detectActiveNavSection(window.location.pathname);

        // Synchronize Desktop Navigation
        document.querySelectorAll('.top-nav-link').forEach(link => {
            const navKey = link.getAttribute('data-nav');
            if (activeSection && navKey === activeSection) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            } else if (navKey) {
                link.classList.remove('active');
                link.removeAttribute('aria-current');
            }
        });

        // Synchronize Mobile Drawer Navigation
        document.querySelectorAll('.mobile-nav-link').forEach(link => {
            const navKey = link.getAttribute('data-nav');
            if (activeSection && navKey === activeSection) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            } else if (navKey) {
                link.classList.remove('active');
                link.removeAttribute('aria-current');
            }
        });

        // Synchronize Admin Dashboard Button
        const topAdminBtn = document.getElementById('topAdminBtn');
        if (topAdminBtn) {
            if (activeSection === 'admin') {
                topAdminBtn.classList.add('ring-2', 'ring-brand-gold', 'ring-offset-1');
                topAdminBtn.setAttribute('aria-current', 'page');
            } else {
                topAdminBtn.classList.remove('ring-2', 'ring-brand-gold', 'ring-offset-1');
                topAdminBtn.removeAttribute('aria-current');
            }
        }
    }

    // Run active navigation sync
    syncActiveNavState();
    window.addEventListener('popstate', syncActiveNavState);

    // 2. Mobile Slide-in Drawer Controls & Accessibility
    const mobileDrawerOpenBtn = document.getElementById('mobileDrawerOpenBtn');
    const mobileDrawerCloseBtn = document.getElementById('mobileDrawerCloseBtn');
    const mobileDrawerBackdrop = document.getElementById('mobileDrawerBackdrop');
    const mobileDrawer = document.getElementById('mobileDrawer');

    function openMobileDrawer() {
        if (mobileDrawer) mobileDrawer.classList.remove('-translate-x-full');
        if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.remove('hidden');
        if (mobileDrawerOpenBtn) mobileDrawerOpenBtn.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
        if (mobileDrawerCloseBtn) {
            setTimeout(() => mobileDrawerCloseBtn.focus(), 100);
        }
    }

    function closeMobileDrawer(returnFocus = false) {
        if (mobileDrawer) mobileDrawer.classList.add('-translate-x-full');
        if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.add('hidden');
        if (mobileDrawerOpenBtn) mobileDrawerOpenBtn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
        if (returnFocus && mobileDrawerOpenBtn) {
            mobileDrawerOpenBtn.focus();
        }
    }

    if (mobileDrawerOpenBtn) mobileDrawerOpenBtn.addEventListener('click', openMobileDrawer);
    if (mobileDrawerCloseBtn) {
        mobileDrawerCloseBtn.addEventListener('click', () => closeMobileDrawer(true));
    }
    if (mobileDrawerBackdrop) {
        mobileDrawerBackdrop.addEventListener('click', () => closeMobileDrawer(true));
    }

    // Auto-close mobile drawer when any navigation link is clicked
    document.querySelectorAll('.mobile-nav-link').forEach(link => {
        link.addEventListener('click', () => {
            closeMobileDrawer(false);
        });
    });

    // Keyboard accessibility: Escape key closes drawer and modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (mobileDrawer && !mobileDrawer.classList.contains('-translate-x-full')) {
                closeMobileDrawer(true);
            } else if (authModal && !authModal.classList.contains('hidden')) {
                closeModal();
            } else if (memberGiftModal && !memberGiftModal.classList.contains('hidden')) {
                closeMemberGiftModal();
            } else if (forgotModal && !forgotModal.classList.contains('hidden')) {
                closeForgotModal();
            }
        }
    });

    // Global Unicode Initial Extractor (supports English, Tamil conjuncts, Arabic, and Unicode scripts)
    window.getUnicodeInitial = function(name) {
        if (!name || !String(name).trim()) return '?';
        const clean = String(name).trim();
        if (typeof Intl !== 'undefined' && Intl.Segmenter) {
            try {
                const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' });
                const iterator = segmenter.segment(clean)[Symbol.iterator]();
                const first = iterator.next().value;
                if (first && first.segment) {
                    const seg = first.segment;
                    return /^[a-zA-Z]$/.test(seg) ? seg.toUpperCase() : seg;
                }
            } catch (err) {
                console.warn('Intl.Segmenter fallback:', err);
            }
        }
        const match = clean.match(/^([\p{L}\p{N}][\p{M}]*)/u);
        if (match) {
            const seg = match[1];
            return /^[a-zA-Z]$/.test(seg) ? seg.toUpperCase() : seg;
        }
        return clean.charAt(0).toUpperCase();
    };

    // 3. Synchronize Auth State Across Elements
    const userProfilePill = document.getElementById('userProfilePill');
    const userMonogramAvatar = document.getElementById('userMonogramAvatar');
    const adminOnlyEls = document.querySelectorAll('.admin-only');

    if (token) {
        loginBtns.forEach(btn => btn.classList.add('hidden'));
        logoutBtns.forEach(btn => btn.classList.remove('hidden'));

        if (userProfilePill && userMonogramAvatar) {
            userProfilePill.classList.remove('hidden');
            userProfilePill.classList.add('flex');
            userMonogramAvatar.textContent = window.getUnicodeInitial(localStorage.getItem('userName') || userRole || 'S');
            if (localStorage.getItem('userName')) userMonogramAvatar.title = localStorage.getItem('userName');
        }

        if (userRole === 'admin') {
            adminBtns.forEach(btn => btn.classList.remove('hidden'));
            deleteCourseBtns.forEach(btn => btn.classList.remove('hidden'));
            adminOnlyEls.forEach(el => el.classList.remove('hidden'));
        } else {
            adminBtns.forEach(btn => btn.classList.add('hidden'));
            deleteCourseBtns.forEach(btn => btn.classList.add('hidden'));
            adminOnlyEls.forEach(el => el.classList.add('hidden'));
        }
    } else {
        loginBtns.forEach(btn => btn.classList.remove('hidden'));
        logoutBtns.forEach(btn => btn.classList.add('hidden'));
        adminBtns.forEach(btn => btn.classList.add('hidden'));
        deleteCourseBtns.forEach(btn => btn.classList.add('hidden'));
        adminOnlyEls.forEach(el => el.classList.add('hidden'));
        if (userProfilePill) userProfilePill.classList.add('hidden');
    }

    function handleLogout(e) {
        if (e) e.preventDefault();
        clearSessionState();
        window.__authStatus = {
            state: 'resolved',
            isAuthenticated: false,
            hasToken: false,
            user: null
        };
        if (window.__promoPopupTimer) {
            clearTimeout(window.__promoPopupTimer);
            window.__promoPopupTimer = null;
        }
        showToast('Signed out successfully.', 'info');
        setTimeout(() => window.location.reload(), 400);
    }

    logoutBtns.forEach(btn => btn.addEventListener('click', handleLogout));

    // -------------------------------------------------------------
    // Modal & Mode Toggle (Sign In vs Sign Up)
    // -------------------------------------------------------------
    const authModal = document.getElementById('authModal');
    const closeBtn = document.querySelector('.modal-close');
    const overlay = document.querySelector('.modal-overlay');
    const authForm = document.getElementById('authForm');
    const modalTitle = document.getElementById('modalTitle');
    const authSubmitBtn = document.getElementById('authSubmitBtn');
    const authTogglePrompt = document.getElementById('authTogglePrompt');
    const authToggleBtn = document.getElementById('authToggleBtn');
    const nameGroup = document.getElementById('nameGroup');
    const nameInput = document.getElementById('name');

    let isSignUp = false;
    let lastActiveModalTrigger = null;

    function openModal() {
        lastActiveModalTrigger = document.activeElement;
        closeMobileDrawer();
        if (authModal) {
            authModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            setTimeout(() => {
                const targetInput = isSignUp ? document.getElementById('name') : document.getElementById('email');
                if (targetInput) targetInput.focus();
            }, 60);
        }
    }

    function closeModal() {
        if (authModal) {
            authModal.classList.add('hidden');
            document.body.style.overflow = '';
            if (lastActiveModalTrigger && typeof lastActiveModalTrigger.focus === 'function') {
                lastActiveModalTrigger.focus();
            }
        }
    }

    function setAuthMode(signUpMode) {
        isSignUp = signUpMode;
        if (isSignUp) {
            if (modalTitle) modalTitle.textContent = 'Create an Account';
            if (authSubmitBtn) authSubmitBtn.textContent = 'Sign Up';
            if (authTogglePrompt) authTogglePrompt.textContent = 'Already have an account?';
            if (authToggleBtn) authToggleBtn.textContent = 'Log In';
            if (nameGroup) nameGroup.classList.remove('hidden');
            if (nameInput) nameInput.required = true;
        } else {
            if (modalTitle) modalTitle.textContent = 'Sign In to Salsabeel';
            if (authSubmitBtn) authSubmitBtn.textContent = 'Sign In';
            if (authTogglePrompt) authTogglePrompt.textContent = "Don't have an account?";
            if (authToggleBtn) authToggleBtn.textContent = 'Sign Up';
            if (nameGroup) nameGroup.classList.add('hidden');
            if (nameInput) {
                nameInput.required = false;
                nameInput.value = '';
            }
        }
    }

    loginBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal();
        });
    });

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (overlay) overlay.addEventListener('click', closeModal);
    if (authToggleBtn) {
        authToggleBtn.addEventListener('click', () => setAuthMode(!isSignUp));
    }

    // -------------------------------------------------------------
    // Auth Form Submission
    // -------------------------------------------------------------
    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const name = nameInput ? nameInput.value.trim() : '';

            if (!email || !password) return;

            // Password minimum 8 characters validation
            if (password.length < 8) {
                showToast('Password must be at least 8 characters long.', 'warning');
                return;
            }

            try {
                if (isSignUp) {
                    // Register first
                    const regRes = await fetch('/api/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, email, password })
                    });
                    const regData = await regRes.json();
                    if (!regRes.ok) {
                        showToast(regData.detail || 'Registration failed.', 'error');
                        return;
                    }
                }

                // Log in to get token
                const formBody = new URLSearchParams({ username: email, password });
                const tokenRes = await fetch('/api/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formBody
                });
                const tokenData = await tokenRes.json();

                if (!tokenRes.ok) {
                    showToast(tokenData.detail || 'Incorrect email or password.', 'error');
                    return;
                }

                localStorage.setItem('token', tokenData.access_token);
                localStorage.setItem('role', tokenData.role);
                localStorage.setItem('userId', tokenData.user_id);
                if (tokenData.name) {
                    localStorage.setItem('userName', tokenData.name);
                }
                const nowTimestamp = Date.now().toString();
                localStorage.setItem('login_time', nowTimestamp);
                localStorage.setItem('last_activity', nowTimestamp);

                // Immediate in-memory authentication state update and timer cancellation
                window.__authStatus = {
                    state: 'resolved',
                    isAuthenticated: true,
                    hasToken: true,
                    user: {
                        id: tokenData.user_id,
                        role: tokenData.role,
                        name: tokenData.name
                    }
                };
                if (window.__promoPopupTimer) {
                    clearTimeout(window.__promoPopupTimer);
                    window.__promoPopupTimer = null;
                }

                closeModal();
                showToast('Welcome to Salsabeel Academy!', 'success');
                setTimeout(() => window.location.reload(), 600);
            } catch (err) {
                console.error(err);
                showToast('Connection error. Please try again.', 'error');
            }
        });
    }

    // -------------------------------------------------------------
    // Member Gift Modal Logic (Rasmul Mushaf)
    // -------------------------------------------------------------
    const memberGiftModal = document.getElementById('memberGiftModal');
    const memberGiftNavBtn = document.getElementById('memberGiftNavBtn');
    const mobileDrawerGiftBtn = document.getElementById('mobileDrawerGiftBtn');
    const closeMemberGiftBtn = document.getElementById('closeMemberGiftBtn');
    const memberGiftBackdrop = document.getElementById('memberGiftBackdrop');
    const memberGiftAuthContent = document.getElementById('memberGiftContentAuthenticated');
    const memberGiftGuestContent = document.getElementById('memberGiftContentGuest');
    const giftSignInTriggerBtn = document.getElementById('giftSignInTriggerBtn');
    const copyGiftLinkBtn = document.getElementById('copyGiftLinkBtn');

    let lastActiveGiftTrigger = null;

    async function openMemberGiftModal() {
        lastActiveGiftTrigger = document.activeElement;
        closeMobileDrawer();
        if (window.__authReady) {
            await window.__authReady;
        }
        const currentToken = localStorage.getItem('token');
        const isAuth = Boolean(window.__authStatus && window.__authStatus.isAuthenticated);
        if (isAuth || (currentToken && (window.__authStatus?.state === 'unavailable' || window.__authStatus?.state === 'offline'))) {
            if (memberGiftAuthContent) memberGiftAuthContent.classList.remove('hidden');
            if (memberGiftGuestContent) memberGiftGuestContent.classList.add('hidden');
        } else {
            if (memberGiftAuthContent) memberGiftAuthContent.classList.add('hidden');
            if (memberGiftGuestContent) memberGiftGuestContent.classList.remove('hidden');
        }
        if (memberGiftModal) memberGiftModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
    window.openMemberGiftModal = openMemberGiftModal;

    function closeMemberGiftModal() {
        if (memberGiftModal) memberGiftModal.classList.add('hidden');
        document.body.style.overflow = '';
        sessionStorage.setItem('dismissed_visitor_gift_promo', 'true');
        if (lastActiveGiftTrigger && typeof lastActiveGiftTrigger.focus === 'function') {
            lastActiveGiftTrigger.focus();
        }
    }
    window.closeMemberGiftModal = closeMemberGiftModal;

    if (memberGiftNavBtn) memberGiftNavBtn.addEventListener('click', openMemberGiftModal);
    if (mobileDrawerGiftBtn) mobileDrawerGiftBtn.addEventListener('click', openMemberGiftModal);
    if (closeMemberGiftBtn) closeMemberGiftBtn.addEventListener('click', closeMemberGiftModal);
    if (memberGiftBackdrop) memberGiftBackdrop.addEventListener('click', closeMemberGiftModal);

    if (giftSignInTriggerBtn) {
        giftSignInTriggerBtn.addEventListener('click', () => {
            closeMemberGiftModal();
            openModal();
        });
    }

    if (copyGiftLinkBtn) {
        copyGiftLinkBtn.addEventListener('click', () => {
            const link = "https://classroom.google.com/c/NzkwNDI3MjAyMzc0?cjc=zyahrwyo";
            if (navigator.clipboard) {
                navigator.clipboard.writeText(link).then(() => {
                    showToast("Classroom link copied to clipboard!", "success");
                }).catch(() => {
                    showToast("Link: " + link, "info");
                });
            } else {
                showToast("Link: " + link, "info");
            }
        });
    }

    // Schedule visitor promo popup (strictly gated for confirmed unauthenticated visitors)
    window.scheduleVisitorPromotionalPopup = async function() {
        if (window.location.pathname.startsWith('/admin')) return;
        if (window.__promoPopupTimer) {
            clearTimeout(window.__promoPopupTimer);
            window.__promoPopupTimer = null;
        }

        const allowed = await canTriggerPromotionalGiftPopup();
        if (!allowed) return;

        if (sessionStorage.getItem('dismissed_visitor_gift_promo') === 'true') {
            return;
        }

        window.__promoPopupTimer = setTimeout(async () => {
            const recheck = await canTriggerPromotionalGiftPopup();
            if (recheck && !sessionStorage.getItem('dismissed_visitor_gift_promo')) {
                openMemberGiftModal();
                sessionStorage.setItem('dismissed_visitor_gift_promo', 'true');
            }
        }, 25000);
    };

    // Run visitor promotional scheduler
    scheduleVisitorPromotionalPopup();

    // -------------------------------------------------------------
    // Universal Password Visibility Toggle (.toggle-pwd-btn)
    // -------------------------------------------------------------
    document.addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('.toggle-pwd-btn');
        if (!toggleBtn) return;
        e.preventDefault();

        const targetId = toggleBtn.getAttribute('data-target');
        const input = targetId ? document.getElementById(targetId) : toggleBtn.closest('.relative')?.querySelector('input');
        if (!input) return;

        const icon = toggleBtn.querySelector('i');
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) {
                icon.className = 'fas fa-eye-slash text-emerald';
            }
        } else {
            input.type = 'password';
            if (icon) {
                icon.className = 'far fa-eye text-gray-400';
            }
        }
    });

    // -------------------------------------------------------------
    // Forgot Password Flow & Modal Controls
    // -------------------------------------------------------------
    const forgotModal = document.getElementById('forgotPasswordModal');
    const forgotOpenBtn = document.getElementById('forgotPasswordOpenBtn');
    const closeForgotBtn = document.getElementById('closeForgotModalBtn');
    const forgotOverlay = document.querySelector('.forgot-modal-overlay');
    const backToSignInBtn = document.getElementById('backToSignInBtn');
    const backToStep1Btn = document.getElementById('backToStep1Btn');
    const resendCodeBtn = document.getElementById('resendCodeBtn');

    const forgotStep1 = document.getElementById('forgotStep1');
    const forgotStep2 = document.getElementById('forgotStep2');
    const requestCodeForm = document.getElementById('requestCodeForm');
    const resetPasswordForm = document.getElementById('resetPasswordForm');
    const forgotEmailInput = document.getElementById('forgotEmail');
    const displayTargetEmail = document.getElementById('displayTargetEmail');

    let activeResetEmail = '';

    let lastActiveForgotTrigger = null;

    function openForgotModal() {
        lastActiveForgotTrigger = document.activeElement;
        closeModal();
        if (forgotStep1) forgotStep1.classList.remove('hidden');
        if (forgotStep2) forgotStep2.classList.add('hidden');
        if (forgotEmailInput) {
            const currentLoginEmail = document.getElementById('email')?.value.trim();
            if (currentLoginEmail) forgotEmailInput.value = currentLoginEmail;
            setTimeout(() => forgotEmailInput.focus(), 60);
        }
        if (forgotModal) {
            forgotModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeForgotModal() {
        if (forgotModal) {
            forgotModal.classList.add('hidden');
            document.body.style.overflow = '';
            if (lastActiveForgotTrigger && typeof lastActiveForgotTrigger.focus === 'function') {
                lastActiveForgotTrigger.focus();
            }
        }
    }

    if (forgotOpenBtn) forgotOpenBtn.addEventListener('click', openForgotModal);
    if (closeForgotBtn) closeForgotBtn.addEventListener('click', closeForgotModal);
    if (forgotOverlay) forgotOverlay.addEventListener('click', closeForgotModal);

    if (backToSignInBtn) {
        backToSignInBtn.addEventListener('click', () => {
            closeForgotModal();
            openModal();
        });
    }

    if (backToStep1Btn) {
        backToStep1Btn.addEventListener('click', () => {
            if (forgotStep2) forgotStep2.classList.add('hidden');
            if (forgotStep1) forgotStep1.classList.remove('hidden');
        });
    }

    // Step 1: Send Code
    if (requestCodeForm) {
        requestCodeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = forgotEmailInput.value.trim().toLowerCase();
            if (!email) return;

            const sendBtn = document.getElementById('sendCodeBtn');
            const originalText = sendBtn ? sendBtn.innerHTML : 'Send Code';
            if (sendBtn) {
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Sending Code...';
            }

            try {
                const res = await fetch('/api/auth/forgot-password/request', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await res.json();

                if (!res.ok) {
                    showToast(data.detail || 'Could not send verification code.', 'error');
                    return;
                }

                activeResetEmail = email;
                if (displayTargetEmail) displayTargetEmail.textContent = email;
                const toastType = data.status === 'warning' ? 'warning' : 'success';
                showToast(data.message || 'Verification code sent to your email!', toastType, 6000);

                // Switch to Step 2
                if (forgotStep1) forgotStep1.classList.add('hidden');
                if (forgotStep2) forgotStep2.classList.remove('hidden');
                const codeInput = document.getElementById('resetCode');
                if (codeInput) {
                    if (data.dev_code) {
                        codeInput.value = data.dev_code;
                    }
                    codeInput.focus();
                }
            } catch (err) {
                console.error(err);
                showToast('Network error while requesting code.', 'error');
            } finally {
                if (sendBtn) {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = originalText;
                }
            }
        });
    }

    // Resend Code
    if (resendCodeBtn) {
        resendCodeBtn.addEventListener('click', async () => {
            if (!activeResetEmail) return;
            try {
                showToast('Resending code...', 'info');
                const res = await fetch('/api/auth/forgot-password/request', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: activeResetEmail })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('A fresh 6-digit code has been sent!', 'success');
                } else {
                    showToast(data.detail || 'Failed to resend code.', 'error');
                }
            } catch (err) {
                showToast('Network error.', 'error');
            }
        });
    }

    // Step 2: Verify & Reset Password
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const code = document.getElementById('resetCode').value.trim();
            const new_password = document.getElementById('resetNewPassword').value;
            const confirm_password = document.getElementById('resetConfirmPassword').value;

            if (new_password.length < 8) {
                showToast('New password must be at least 8 characters long.', 'warning');
                return;
            }

            if (new_password !== confirm_password) {
                showToast('Passwords do not match.', 'warning');
                return;
            }

            const submitBtn = document.getElementById('resetSubmitBtn');
            const originalText = submitBtn ? submitBtn.innerHTML : 'Update Password';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Resetting Password...';
            }

            try {
                const res = await fetch('/api/auth/forgot-password/verify-and-reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: activeResetEmail,
                        code,
                        new_password,
                        confirm_password
                    })
                });
                const data = await res.json();

                if (!res.ok) {
                    showToast(data.detail || 'Could not reset password.', 'error');
                    return;
                }

                showToast(data.message || 'Password reset successfully!', 'success', 5000);
                closeForgotModal();

                // Open Sign In with the updated email prefilled
                const emailInput = document.getElementById('email');
                if (emailInput) emailInput.value = activeResetEmail;
                const pwdInput = document.getElementById('password');
                if (pwdInput) pwdInput.value = '';
                setAuthMode(false);
                openModal();
            } catch (err) {
                console.error(err);
                showToast('Network error while resetting password.', 'error');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }
        });
    }

    // -------------------------------------------------------------
    // Course Enrollment Tracking (Delegated)
    // -------------------------------------------------------------
    document.addEventListener('click', (e) => {
        const enrollBtn = e.target.closest('.enroll-btn');
        if (!enrollBtn) return;

        const courseId = enrollBtn.getAttribute('data-id');
        // If user is logged in, record enrollment in DB for admin tracking
        if (token && userId && courseId) {
            fetch('/api/enrollments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ user_id: parseInt(userId), course_id: parseInt(courseId) })
            }).catch(err => console.error('Enrollment tracking notice:', err));
        }
    });

    // -------------------------------------------------------------
    // Delete Course (Admin)
    // -------------------------------------------------------------
    document.querySelectorAll('.delete-course-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (!token) {
                showToast('Please log in as an administrator to delete courses.', 'warning');
                return;
            }
            const courseId = btn.getAttribute('data-id');

            confirmModal({
                title: 'Delete Course',
                message: 'Are you sure you want to permanently delete this course? This action cannot be undone.',
                confirmText: 'Delete Course',
                isDestructive: true,
                onConfirm: async () => {
                    btn.disabled = true;
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Deleting...';

                    try {
                        const res = await fetch(`/api/courses/${courseId}`, {
                            method: 'DELETE',
                            headers: { 'Authorization': `Bearer ${token}` }
                        });

                        if (res.ok) {
                            showToast('Course deleted successfully.', 'success');
                            setTimeout(() => window.location.reload(), 700);
                        } else {
                            showToast('Failed to delete course.', 'error');
                            btn.disabled = false;
                            btn.innerHTML = originalText;
                        }
                    } catch (err) {
                        console.error(err);
                        showToast('Network error.', 'error');
                        btn.disabled = false;
                        btn.innerHTML = originalText;
                    }
                }
            });
        });
    });

    // -------------------------------------------------------------
    // Add Course Form (Admin)
    // -------------------------------------------------------------
    const addCourseForm = document.getElementById('addCourseForm');
    if (addCourseForm) {
        addCourseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!token) {
                showToast('Please log in as an administrator to publish a course.', 'warning');
                return;
            }

            const imageInput = document.getElementById('image');
            const imageUrlInput = document.getElementById('image_url');
            const hasFile = imageInput && imageInput.files && imageInput.files.length > 0;
            const hasUrl = imageUrlInput && imageUrlInput.value.trim().length > 0;

            if (!hasFile && !hasUrl) {
                showToast('Please upload a cover image or use the AI Course Parser.', 'warning');
                return;
            }

            const submitBtn = addCourseForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Publishing...';
            }

            const formData = new FormData(addCourseForm);

            try {
                const res = await fetch('/api/courses', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData
                });

                if (res.ok) {
                    showToast('Course published successfully!', 'success');
                    setTimeout(() => {
                        window.location.href = '/courses';
                    }, 800);
                } else {
                    const err = await res.text();
                    showToast('Error publishing course: ' + err, 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('Network error.', 'error');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Publish Course';
                }
            }
        });
    }

    // -------------------------------------------------------------
    // Webflow-Inspired Sticky Four Pillars Storytelling & Progress Rail
    // -------------------------------------------------------------
    function initStickyPillars() {
        const rail = document.getElementById('pillarsRail');
        const cardsContainer = document.getElementById('pillarsCardsContainer');
        if (!rail || !cardsContainer) return;

        const steps = rail.querySelectorAll('.pillar-step');
        const cards = cardsContainer.querySelectorAll('.pillar-card');
        if (!steps.length || !cards.length) return;

        let currentActivePillar = '1';

        function setActivePillar(targetId) {
            if (currentActivePillar === targetId) return;
            currentActivePillar = targetId;

            steps.forEach(step => {
                const isActive = step.dataset.pillarTarget === targetId;
                step.classList.toggle('is-active', isActive);
                
                const num = step.querySelector('.pillar-step-num');
                const label = step.querySelector('.pillar-step-label');
                const indicator = step.querySelector('.pillar-step-indicator');

                if (isActive) {
                    if (num) {
                        num.className = 'pillar-step-num font-mono text-xs font-bold w-6 h-6 rounded-md bg-brand-deep text-brand-gold flex items-center justify-center transition-colors';
                    }
                    if (label) {
                        label.className = 'pillar-step-label text-sm text-brand-deep font-semibold transition-colors';
                    }
                    if (indicator) {
                        indicator.classList.remove('opacity-0');
                        indicator.classList.add('opacity-100');
                    }
                } else {
                    if (num) {
                        num.className = 'pillar-step-num font-mono text-xs font-semibold w-6 h-6 rounded-md bg-white border border-brand-hairline text-brand-muted flex items-center justify-center transition-colors';
                    }
                    if (label) {
                        label.className = 'pillar-step-label text-sm text-brand-muted font-normal transition-colors';
                    }
                    if (indicator) {
                        indicator.classList.remove('opacity-100');
                        indicator.classList.add('opacity-0');
                    }
                }
            });
        }

        // Click-to-scroll on rail steps with accessible focus preservation
        steps.forEach(step => {
            step.addEventListener('click', () => {
                const targetId = step.dataset.pillarTarget;
                const targetCard = document.getElementById(`pillar-card-${targetId}`);
                if (targetCard) {
                    targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setActivePillar(targetId);
                }
            });
        });

        // IntersectionObserver for understated, flicker-free tracking
        if ('IntersectionObserver' in window && window.innerWidth >= 1024) {
            const visiblePillars = new Map();
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    const id = entry.target.dataset.pillarId;
                    if (entry.isIntersecting) {
                        visiblePillars.set(id, entry.intersectionRatio);
                    } else {
                        visiblePillars.delete(id);
                    }
                });

                if (visiblePillars.size > 0) {
                    let bestId = null;
                    let maxRatio = -1;
                    visiblePillars.forEach((ratio, id) => {
                        if (ratio > maxRatio) {
                            maxRatio = ratio;
                            bestId = id;
                        }
                    });
                    if (bestId) {
                        setActivePillar(bestId);
                    }
                }
            }, {
                rootMargin: '-15% 0px -25% 0px',
                threshold: [0.15, 0.35, 0.55, 0.75]
            });

            cards.forEach(card => observer.observe(card));
        }
    }
    initStickyPillars();

    // -------------------------------------------------------------
    // Accessible, Zero-Jank FAQ Disclosure (Pure CSS Grid 220ms)
    // -------------------------------------------------------------
    function initFaqAccordion() {
        const accordion = document.getElementById('faqAccordion');
        if (!accordion) return;

        const items = accordion.querySelectorAll('.faq-item');
        items.forEach(item => {
            const btn = item.querySelector('.faq-toggle');
            const wrapper = item.querySelector('.faq-answer-wrapper');
            const icon = btn ? btn.querySelector('i') : null;
            if (!btn || !wrapper) return;

            btn.addEventListener('click', () => {
                const isOpen = wrapper.classList.contains('is-open');

                // Collapse all sibling items first for clean single-panel presentation
                items.forEach(sibling => {
                    if (sibling === item) return;
                    const sBtn = sibling.querySelector('.faq-toggle');
                    const sWrapper = sibling.querySelector('.faq-answer-wrapper');
                    const sIcon = sBtn ? sBtn.querySelector('i') : null;
                    if (sWrapper && sWrapper.classList.contains('is-open')) {
                        sWrapper.classList.remove('is-open');
                        if (sBtn) sBtn.setAttribute('aria-expanded', 'false');
                        if (sIcon) sIcon.classList.remove('rotate-180');
                        sWrapper.addEventListener('transitionend', function onEnd() {
                            if (!sWrapper.classList.contains('is-open')) {
                                sWrapper.setAttribute('hidden', '');
                            }
                            sWrapper.removeEventListener('transitionend', onEnd);
                        });
                    }
                });

                if (!isOpen) {
                    // Open: Remove hidden first, then trigger CSS Grid expansion on next tick
                    wrapper.removeAttribute('hidden');
                    requestAnimationFrame(() => {
                        wrapper.classList.add('is-open');
                        btn.setAttribute('aria-expanded', 'true');
                        if (icon) icon.classList.add('rotate-180');
                    });
                } else {
                    // Close: Animate shut via CSS Grid, then mark hidden on transitionend
                    wrapper.classList.remove('is-open');
                    btn.setAttribute('aria-expanded', 'false');
                    if (icon) icon.classList.remove('rotate-180');
                    wrapper.addEventListener('transitionend', function onEnd() {
                        if (!wrapper.classList.contains('is-open')) {
                            wrapper.setAttribute('hidden', '');
                        }
                        wrapper.removeEventListener('transitionend', onEnd);
                    });
                }
            });
        });
    }
    initFaqAccordion();

});
