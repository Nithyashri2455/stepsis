// Sepsis Prediction System

document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector("form");

    form.addEventListener("submit", function (event) {

        const inputs = document.querySelectorAll("input");

        let valid = true;

        inputs.forEach(input => {

            if (input.value.trim() === "") {

                valid = false;

                input.style.border = "2px solid red";

            }
            else {

                input.style.border = "1px solid #ccc";

            }

        });

        if (!valid) {

            event.preventDefault();

            alert("Please fill all the fields.");

        }

    });

});

// ===========================
// Current Date & Time
// ===========================

function updateDateTime() {

    const now = new Date();

    document.getElementById("currentDate").innerHTML =
        "📅 " + now.toLocaleDateString();

    document.getElementById("currentTime").innerHTML =
        "🕒 " + now.toLocaleTimeString();

}

updateDateTime();

setInterval(updateDateTime, 1000);