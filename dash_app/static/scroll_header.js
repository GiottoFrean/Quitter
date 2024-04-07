let prevScrollPos = window.pageYOffset;
let headerPos = 0;

window.addEventListener('scroll', () => {
  const currentScrollPos = window.pageYOffset;
  const headerBar = document.getElementById("fixed-header-bar");
  if (!headerBar) {
    return;
  }
  const headerHeight = headerBar.offsetHeight;

  if (currentScrollPos > prevScrollPos && currentScrollPos - headerPos > headerHeight) {
    // scrolling down, and scrolled past the header
        headerPos = Math.max(currentScrollPos-headerHeight,0);
    } else {
        headerPos = Math.min(currentScrollPos, headerPos);
    }
    const scrollProgress = Math.min((currentScrollPos - headerPos) / headerHeight, 1);
    headerBar.style.transform = `translateY(-${currentScrollPos - headerPos}px)`;
    prevScrollPos = currentScrollPos;
});