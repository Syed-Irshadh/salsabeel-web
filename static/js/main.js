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
            confirmBtn.className = 'px-5 py-2 text-sm font-bold text-white bg-red-600 hover:bg-red-700 rounded-xl transition-all shadow-sm cursor-pointer';
        } else {
            confirmBtn.className = 'px-5 py-2 text-sm font-bold text-white bg-navy hover:bg-teal-700 rounded-xl transition-all shadow-sm cursor-pointer';
        }
    }
    if (cancelBtn) cancelBtn.textContent = cancelText;

    if (icon && iconBg) {
        if (isDestructive) {
            icon.className = 'fas fa-trash-alt text-red-500';
            iconBg.className = 'w-12 h-12 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center flex-shrink-0 text-xl';
        } else {
            icon.className = 'fas fa-question-circle text-gold';
            iconBg.className = 'w-12 h-12 rounded-xl bg-amber-50 border border-gold/40 flex items-center justify-center flex-shrink-0 text-xl';
        }
    }

    modal.classList.remove('hidden');

    function closeModal() {
        modal.classList.add('hidden');
        if (confirmBtn) confirmBtn.removeEventListener('click', handleConfirm);
        if (cancelBtn) cancelBtn.removeEventListener('click', closeModal);
        if (backdrop) backdrop.removeEventListener('click', closeModal);
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

    // 1. Active Navigation Highlight
    const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
    document.querySelectorAll('.top-nav-link, .sidebar-link, .mobile-nav-link').forEach(link => {
        const href = (link.getAttribute('href') || '').replace(/\/$/, '') || '/';
        const page = link.getAttribute('data-page');
        if (href === currentPath || page === currentPath || 
            (currentPath.startsWith('/courses') && (href === '/courses' || page === '/courses')) || 
            (currentPath.startsWith('/about') && (href === '/about' || page === '/about'))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // 2. Mobile Slide-in Drawer Controls
    const mobileDrawerOpenBtn = document.getElementById('mobileDrawerOpenBtn');
    const mobileDrawerCloseBtn = document.getElementById('mobileDrawerCloseBtn');
    const mobileDrawerBackdrop = document.getElementById('mobileDrawerBackdrop');
    const mobileDrawer = document.getElementById('mobileDrawer');

    function openMobileDrawer() {
        if (mobileDrawer) mobileDrawer.classList.remove('-translate-x-full');
        if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileDrawer() {
        if (mobileDrawer) mobileDrawer.classList.add('-translate-x-full');
        if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.add('hidden');
        document.body.style.overflow = '';
    }

    if (mobileDrawerOpenBtn) mobileDrawerOpenBtn.addEventListener('click', openMobileDrawer);
    if (mobileDrawerCloseBtn) mobileDrawerCloseBtn.addEventListener('click', closeMobileDrawer);
    if (mobileDrawerBackdrop) mobileDrawerBackdrop.addEventListener('click', closeMobileDrawer);

    // 3. Synchronize Auth State Across Elements
    if (token) {
        loginBtns.forEach(btn => btn.classList.add('hidden'));
        logoutBtns.forEach(btn => btn.classList.remove('hidden'));

        if (userRole === 'admin') {
            adminBtns.forEach(btn => btn.classList.remove('hidden'));
            deleteCourseBtns.forEach(btn => btn.classList.remove('hidden'));
        } else {
            adminBtns.forEach(btn => btn.classList.add('hidden'));
            deleteCourseBtns.forEach(btn => btn.classList.add('hidden'));
        }
    } else {
        loginBtns.forEach(btn => btn.classList.remove('hidden'));
        logoutBtns.forEach(btn => btn.classList.add('hidden'));
        adminBtns.forEach(btn => btn.classList.add('hidden'));
        deleteCourseBtns.forEach(btn => btn.classList.add('hidden'));
    }

    function handleLogout(e) {
        if (e) e.preventDefault();
        clearSessionState();
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

    function openModal() {
        closeMobileDrawer();
        if (authModal) authModal.classList.remove('hidden');
    }

    function closeModal() {
        if (authModal) authModal.classList.add('hidden');
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

    function openForgotModal() {
        closeModal();
        if (forgotStep1) forgotStep1.classList.remove('hidden');
        if (forgotStep2) forgotStep2.classList.add('hidden');
        if (forgotEmailInput) {
            const currentLoginEmail = document.getElementById('email')?.value.trim();
            if (currentLoginEmail) forgotEmailInput.value = currentLoginEmail;
        }
        if (forgotModal) forgotModal.classList.remove('hidden');
    }

    function closeForgotModal() {
        if (forgotModal) forgotModal.classList.add('hidden');
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
    // Hardware-Accelerated Smooth Entrance Observer
    // -------------------------------------------------------------
    if ('IntersectionObserver' in window) {
        const observerOptions = {
            root: null,
            rootMargin: '0px 0px -40px 0px',
            threshold: 0.1
        };

        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('animate-enter');
                        entry.target.classList.remove('opacity-0', 'translate-y-4');
                    }, (index % 4) * 60);
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        document.querySelectorAll('.reveal-on-scroll, .shadcn-card').forEach(el => {
            if (!el.classList.contains('animate-enter')) {
                el.classList.add('transition-all', 'duration-500');
                revealObserver.observe(el);
            }
        });
    }
});
