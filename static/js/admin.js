document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("registerAdminForm").onsubmit = async function (event) {
        event.preventDefault();

        let username = document.getElementById("adminUsername").value;
        let password = document.getElementById("adminPassword").value;

        let response = await fetch("/register_admin", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username, password })
        });

        let result = await response.json();
        alert(result.message);
        loadAdmins();
    };

    async function loadAdmins() {
        let response = await fetch("/get_admins");
        let admins = await response.json();
        let adminList = document.getElementById("adminList");
        adminList.innerHTML = "";

        admins.forEach(admin => {
            let listItem = document.createElement("li");
            listItem.className = "list-group-item";
            listItem.textContent = `${admin.username}`;
            adminList.appendChild(listItem);
        });
    }

    loadAdmins();
});
