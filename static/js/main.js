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
    // Auth State & Navigation Controls
    // -------------------------------------------------------------
    const token = localStorage.getItem('token');
    const userRole = localStorage.getItem('role');
    const userId = localStorage.getItem('userId');

    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const adminBtn = document.getElementById('adminBtn');
    const mobileLoginBtns = document.querySelectorAll('.mobile-login-btn');
    const mobileLogoutBtns = document.querySelectorAll('.mobile-logout-btn');
    const mobileAdminBtns = document.querySelectorAll('.mobile-admin-btn');
    const deleteCourseBtns = document.querySelectorAll('.delete-course-btn');

    // Mobile Hamburger Menu
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuIcon = document.getElementById('mobileMenuIcon');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
            if (mobileMenuIcon) {
                if (mobileMenu.classList.contains('hidden')) {
                    mobileMenuIcon.classList.replace('fa-times', 'fa-bars');
                } else {
                    mobileMenuIcon.classList.replace('fa-bars', 'fa-times');
                }
            }
        });
    }

    if (token) {
        if (loginBtn) loginBtn.classList.add('hidden');
        mobileLoginBtns.forEach(btn => btn.classList.add('hidden'));

        if (logoutBtn) logoutBtn.classList.remove('hidden');
        mobileLogoutBtns.forEach(btn => btn.classList.remove('hidden'));

        if (userRole === 'admin') {
            if (adminBtn) adminBtn.classList.remove('hidden');
            mobileAdminBtns.forEach(btn => btn.classList.remove('hidden'));
            deleteCourseBtns.forEach(btn => btn.classList.remove('hidden'));
        }
    } else {
        if (loginBtn) loginBtn.classList.remove('hidden');
        mobileLoginBtns.forEach(btn => btn.classList.remove('hidden'));

        if (logoutBtn) logoutBtn.classList.add('hidden');
        mobileLogoutBtns.forEach(btn => btn.classList.add('hidden'));

        if (adminBtn) adminBtn.classList.add('hidden');
        mobileAdminBtns.forEach(btn => btn.classList.add('hidden'));

        deleteCourseBtns.forEach(btn => btn.classList.add('hidden'));
    }

    function handleLogout(e) {
        if (e) e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('userId');
        localStorage.removeItem('userName');
        window.location.reload();
    }

    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
    mobileLogoutBtns.forEach(btn => btn.addEventListener('click', handleLogout));

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

    if (loginBtn) loginBtn.addEventListener('click', (e) => { e.preventDefault(); openModal(); });
    mobileLoginBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (mobileMenu) mobileMenu.classList.add('hidden');
            if (mobileMenuIcon) mobileMenuIcon.classList.replace('fa-times', 'fa-bars');
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
});
