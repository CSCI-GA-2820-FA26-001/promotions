async function loadPromotions() {
    const tbody = document.getElementById("promotion-list");
    const message = document.getElementById("list-message");

    message.textContent = "Loading promotions...";
    tbody.replaceChildren();

    try {
                const response = await fetch("/api/promotions", {
            headers: { Accept: "application/json" }
        });

        if (!response.ok) {
            throw new Error("Failed to load promotions");
        }

        const promotions = await response.json();

        if (!Array.isArray(promotions)) {
            throw new Error("Invalid API response");
        }

        if (promotions.length === 0) {
            message.textContent = "No promotions available.";
            return;
        }

        const fields = [
            "id", "name", "promotion_type", "value",
            "product_id", "start_date", "end_date", "active"
        ];

        promotions.forEach((promotion) => {
            const row = document.createElement("tr");
            row.setAttribute("data-testid", "promotion-row");

            fields.forEach((field) => {
                const cell = document.createElement("td");

                cell.textContent = String(promotion[field] ?? "—");
                cell.setAttribute("data-testid", `promotion-${field}`);

                row.appendChild(cell);
            });

            tbody.appendChild(row);
        });

        message.textContent = "";

    } catch (error) {
        tbody.replaceChildren();
        message.textContent = "Unable to load promotions.";
        message.setAttribute("data-testid", "list-error");
    }
}

document.addEventListener("DOMContentLoaded", loadPromotions);