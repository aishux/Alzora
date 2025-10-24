setTimeout(function() {
      document.querySelectorAll('#messages-container .alert').forEach(function(el) {
          el.style.opacity = '0';
          setTimeout(() => el.remove(), 500); // remove after fade-out
      });
  }, 3000);