document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contactForm');
    const formMessage = document.getElementById('formMessage');

    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const phone = document.getElementById('phone').value;
            const message = document.getElementById('message').value;

            try {
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, email, phone, message })
                });

                const result = await response.json();

                if (result.success) {
                    formMessage.textContent = 'Message sent successfully! We will contact you soon.';
                    formMessage.className = 'form-message success';
                    contactForm.reset();
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                formMessage.textContent = 'Error sending message. Please try again.';
                formMessage.className = 'form-message error';
            }

            setTimeout(() => {
                formMessage.textContent = '';
                formMessage.className = 'form-message';
            }, 5000);
        });
    }
});
