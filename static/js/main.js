// Salsabeel Academy - Main Frontend Script
document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // Auth State
    // -------------------------------------------------------------
    const token = localStorage.getItem('token');
    const userRole = localStorage.getItem('role');
    const userId = localStorage.getItem('userId');

    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const adminBtn = document.getElementById('adminBtn');
    const deleteCourseBtns = document.querySelectorAll('.delete-course-btn');

    if (token) {
        if (loginBtn) loginBtn.classList.add('hidden');
        if (logoutBtn) logoutBtn.classList.remove('hidden');
        if (userRole === 'admin') {
            if (adminBtn) adminBtn.classList.remove('hidden');
            deleteCourseBtns.forEach(btn => btn.classList.remove('hidden'));
        }
    } else {
        if (loginBtn) loginBtn.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
        if (adminBtn) adminBtn.classList.add('hidden');
        deleteCourseBtns.forEach(btn => btn.classList.add('hidden'));
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            localStorage.removeItem('userId');
            window.location.reload();
        });
    }

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
    // Course Enrollment Tracking
    // -------------------------------------------------------------
    document.querySelectorAll('.enroll-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const courseId = btn.getAttribute('data-id');

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
    });

    // -------------------------------------------------------------
    // Delete Course (Admin)
    // -------------------------------------------------------------
    document.querySelectorAll('.delete-course-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const courseId = btn.getAttribute('data-id');
            if (!confirm('Are you sure you want to permanently delete this course?')) return;

            try {
                const res = await fetch(`/api/courses/${courseId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (res.ok) {
                    alert('Course deleted.');
                    window.location.reload();
                } else {
                    alert('Failed to delete course.');
                }
            } catch (err) {
                console.error(err);
                alert('Network error.');
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

            const imageInput = document.getElementById('image');
            const imageUrlInput = document.getElementById('image_url');
            const hasFile = imageInput && imageInput.files && imageInput.files.length > 0;
            const hasUrl = imageUrlInput && imageUrlInput.value.trim().length > 0;

            if (!hasFile && !hasUrl) {
                alert('Please upload a cover image or use the AI Course Parser.');
                return;
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
            }
        });
    }
});
