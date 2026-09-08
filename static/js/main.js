// Salsabeel Academy - Main Frontend Script
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
                alert('Password must be at least 8 characters long.');
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
                        alert(regData.detail || 'Registration failed.');
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
                    alert(tokenData.detail || 'Incorrect email or password.');
                    return;
                }

                localStorage.setItem('token', tokenData.access_token);
                localStorage.setItem('role', tokenData.role);
                localStorage.setItem('userId', tokenData.user_id);
                if (tokenData.name) {
                    localStorage.setItem('userName', tokenData.name);
                }

                closeModal();
                window.location.reload();
            } catch (err) {
                console.error(err);
                alert('Connection error. Please try again.');
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
                alert('Please log in as an administrator to delete courses.');
                return;
            }
            const courseId = btn.getAttribute('data-id');
            if (!confirm('Are you sure you want to permanently delete this course?')) return;

            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Deleting...';

            try {
                const res = await fetch(`/api/courses/${courseId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (res.ok) {
                    alert('Course deleted successfully.');
                    window.location.reload();
                } else {
                    alert('Failed to delete course.');
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }
            } catch (err) {
                console.error(err);
                alert('Network error.');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
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
                alert('Please log in as an administrator to publish a course.');
                return;
            }

            const imageInput = document.getElementById('image');
            const imageUrlInput = document.getElementById('image_url');
            const hasFile = imageInput && imageInput.files && imageInput.files.length > 0;
            const hasUrl = imageUrlInput && imageUrlInput.value.trim().length > 0;

            if (!hasFile && !hasUrl) {
                alert('Please upload a cover image or use the AI Course Parser.');
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
                    alert('Course published successfully!');
                    window.location.href = '/courses';
                } else {
                    const err = await res.text();
                    alert('Error publishing course: ' + err);
                }
            } catch (err) {
                console.error(err);
                alert('Network error.');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Publish Course';
                }
            }
        });
    }
});
