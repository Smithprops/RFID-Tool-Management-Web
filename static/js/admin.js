document.addEventListener("DOMContentLoaded", function () {
    let tabs = document.querySelectorAll(".nav-tabs .nav-link");
    let contentPanes = document.querySelectorAll(".tab-pane");

    tabs.forEach(tab => {
        tab.addEventListener("click", function (event) {
            event.preventDefault();
            let activeTab = document.querySelector(".nav-tabs .nav-link.active");
            let activePane = document.querySelector(".tab-pane.show.active");

            if (activeTab) activeTab.classList.remove("active");
            if (activePane) activePane.classList.remove("show", "active");

            this.classList.add("active");
            let targetPane = document.querySelector(this.getAttribute("href"));
            if (targetPane) targetPane.classList.add("show", "active");
        });
    });
});
