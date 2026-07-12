document.addEventListener('DOMContentLoaded', () => {
    // Auth State Management
    const userRole = localStorage.getItem('userRole');
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const addCourseBtn = document.getElementById('addCourseBtn');
    
    if (userRole) {
        if(loginBtn) loginBtn.style.display = 'none';
        if(logoutBtn) logoutBtn.style.display = 'inline-block';
        if (userRole === 'admin' && addCourseBtn) {
            addCourseBtn.style.display = 'inline-block';
        }
        if (userRole === 'admin') {
            document.querySelectorAll('.delete-course-btn').forEach(btn => btn.style.display = 'inline-block');
        }
    } else {
        if(loginBtn) loginBtn.style.display = 'inline-block';
        if(logoutBtn) logoutBtn.style.display = 'none';
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('userRole');
            window.location.reload();
        });
    }

    // Modal Logic
    const authModal = document.getElementById('authModal');
    const closeBtn = document.querySelector('.modal-close');
    
    if(loginBtn) {
        loginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            authModal.classList.add('active');
        });
    }

    if(closeBtn) {
        closeBtn.addEventListener('click', () => {
            authModal.classList.remove('active');
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === authModal) {
            authModal.classList.remove('active');
        }
    });

    // Handle course enrollment mock
    const enrollBtns = document.querySelectorAll('.enroll-btn');
    enrollBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // 1. Check if user is logged in
            if (!localStorage.getItem('userRole')) {
                alert('Please sign up or log in to enroll in a course.');
                const authModal = document.getElementById('authModal');
                if(authModal) authModal.classList.add('active');
                return;
            }

            const courseId = e.target.getAttribute('data-id');
            const coursePrice = e.target.getAttribute('data-price');
            
            // 2. Show price confirmation
            const confirmEnroll = confirm(`Would you like to purchase and enroll in this course for ${coursePrice}?`);
            
            if (confirmEnroll) {
                const userId = localStorage.getItem('userId');
                fetch('/api/enrollments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId), course_id: parseInt(courseId) })
                }).then(() => {
                    alert('Payment successful! Unlocking course...');
                    window.location.href = `/viewer/${courseId}`;
                }).catch(err => {
                    console.error(err);
                    alert('Failed to enroll.');
                });
            }
        });
    });

    const deleteBtns = document.querySelectorAll('.delete-course-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const courseId = e.target.getAttribute('data-id');
            if (confirm("Are you sure you want to delete this course?")) {
                fetch(`/api/courses/${courseId}`, {
                    method: 'DELETE'
                }).then(res => {
                    if(res.ok) {
                        alert("Course deleted");
                        window.location.reload();
                    }
                });
            }
        });
    });
    
    // Auth form submit mock
    const authForm = document.getElementById('authForm');
    if (authForm) {
        authForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('email').value;
            
            fetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: emailInput })
            }).then(res => res.json()).then(data => {
                localStorage.setItem('userRole', data.role);
                localStorage.setItem('userId', data.user_id);
                alert(`Successfully logged in as ${data.role}!`);
                authModal.classList.remove('active');
                window.location.reload();
            }).catch(err => {
                console.error(err);
                alert("Login failed.");
            });
        });
    }

    // Admin Add Course mock
    const addCourseForm = document.getElementById('addCourseForm');
    if (addCourseForm) {
        addCourseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(addCourseForm);
            
            try {
                const response = await fetch('/api/courses', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    alert('Course added successfully!');
                    window.location.href = '/courses';
                } else {
                    alert('Error adding course');
                }
            } catch (error) {
                console.error(error);
                alert('Network error');
            }
        });
    }
});
