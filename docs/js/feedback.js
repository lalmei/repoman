// Custom JavaScript for the repoman documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add custom functionality here
    
    // Example: Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Example: Add copy button to code blocks
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.textContent = 'Copy';
        button.className = 'copy-button';
        button.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            padding: 0.25rem 0.5rem;
            background: var(--md-primary-fg-color);
            color: var(--md-primary-bg-color);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
        `;
        
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent).then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            });
        });
        
        const container = block.parentElement;
        container.style.position = 'relative';
        container.appendChild(button);
    });
});
