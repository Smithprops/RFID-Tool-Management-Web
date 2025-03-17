document.addEventListener("DOMContentLoaded", function () {
    let tabs = document.querySelectorAll(".nav-tabs .nav-link");

    tabs.forEach(tab => {
        tab.addEventListener("click", function (event) {
            event.preventDefault();

            // Remove active class from previous tab and tab content
            document.querySelector(".nav-tabs .nav-link.active")?.classList.remove("active");
            document.querySelector(".tab-pane.show.active")?.classList.remove("show", "active");

            // Activate clicked tab
            this.classList.add("active");

            // Get target tab-pane ID using data-bs-target
            let targetPane = document.querySelector(this.getAttribute("data-bs-target"));
            if (targetPane) targetPane.classList.add("show", "active");
        });
    });
});

