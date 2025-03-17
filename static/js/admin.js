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

    // Ensure all tabs are accessible based on role
    fetch('/api/user_role')
        .then(response => response.json())
        .then(data => {
            if (data.role !== "admin") {
                document.getElementById("tools-section")?.remove();
                document.getElementById("rooms-section")?.remove();
                document.getElementById("checked-out-section")?.remove();
                document.getElementById("add-users-section")?.remove();
            }
        })
        .catch(error => console.error('Error fetching user role:', error));

    // Live Search for Users
    document.getElementById("searchUsers").addEventListener("keyup", function () {
        let filter = this.value.toLowerCase();
        document.querySelectorAll("#users-section tbody tr").forEach(row => {
            let name = row.querySelector("td:nth-child(2)").textContent.toLowerCase();
            row.style.display = name.includes(filter) ? "" : "none";
        });
    });
});
