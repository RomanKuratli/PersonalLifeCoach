function setNavigationPill(linkId) {
    console.log("setNavigationPill called");
    let navLinks = document.querySelectorAll(".nav-link");
    console.log(navLinks);
    let linkCount = navLinks.length;
    for (let i=0; i < linkCount; i++) {
        let classList = navLinks[i].classList;
        if (navLinks[i].id == linkId) classList.add("active");
        else classList.remove("active");
    }
}