// ==========================
// Login Modal
// ==========================

const loginBtn = document.getElementById("loginBtn");
const loginModal = document.getElementById("loginModal");
const closeBtn = document.querySelector(".close");

// Open Login
loginBtn.addEventListener("click", function () {

    loginModal.style.display = "flex";

});

// Close Login
closeBtn.addEventListener("click", function () {

    loginModal.style.display = "none";

});

// Close when clicking outside
window.addEventListener("click", function (e) {

    if (e.target == loginModal) {

        loginModal.style.display = "none";

    }

});

// ==========================
// Login → Register
// ==========================

const loginCard = document.getElementById("loginCard");
const registerCard = document.getElementById("registerCard");

document.getElementById("showRegister").addEventListener("click", function(e){

    e.preventDefault();

    loginCard.style.display = "none";

    registerCard.style.display = "block";

});

// ==========================
// Register → Login
// ==========================

document.getElementById("showLogin").addEventListener("click", function(e){

    e.preventDefault();

    registerCard.style.display = "none";

    loginCard.style.display = "block";

});