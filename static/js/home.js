document.addEventListener('DOMContentLoaded', () => {
    // Hero section animations
    const heroElements = document.querySelectorAll('.animate-fade-in-up, .animate-fade-in-scale');
    heroElements.forEach(el => {
      if (el.classList.contains('animate-fade-in-up') || el.classList.contains('animate-fade-in-scale')) {
        el.style.opacity = '1';
        el.style.transform = el.classList.contains('animate-fade-in-up') ? 'translateY(0)' : 'scale(1)';
      }
    });
    
    // Scroll animations for sections
    const sections = document.querySelectorAll('.scroll-section');
    const sectionElements = document.querySelectorAll('.section-element');
    let currentSection = 0;
    let animating = false;
    
    const checkScroll = () => {
      if (animating) return;
      
      sections.forEach((section, index) => {
        const sectionTop = section.getBoundingClientRect().top;
        const sectionHeight = section.getBoundingClientRect().height;
        const triggerPoint = window.innerHeight * 0.7;
        
        if (sectionTop < triggerPoint && sectionTop > -sectionHeight * 0.5) {
          if (index >= currentSection) {
            animating = true;
            currentSection = index;
            
            // Animate the section container first
            section.classList.add('animate-section');
            
            // Then animate the elements inside with delays
            const elements = section.querySelectorAll('.section-element');
            elements.forEach(el => {
              const delay = el.dataset.delay || 0;
              setTimeout(() => {
                el.classList.add('animate');
              }, delay);
            });
            
            // Allow next animation after a short delay
            setTimeout(() => {
              animating = false;
            }, 500);
          }
        }
      });
    };
    
    // Initial check on load
    checkScroll();
    
    // Check on scroll
    window.addEventListener('scroll', checkScroll);
    
    // Check on resize
    window.addEventListener('resize', checkScroll);
  });