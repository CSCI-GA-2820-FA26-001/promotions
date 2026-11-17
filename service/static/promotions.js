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

            const actionCell = document.createElement("td");
            const actionButton = document.createElement("button");
            actionButton.type = "button";
            actionButton.className = "promotion-action-btn";
            actionButton.setAttribute("data-testid", "promotion-action");
            actionButton.dataset.promotionId = promotion.id;
            actionButton.dataset.action = promotion.active ? "deactivate" : "activate";
            actionButton.textContent = promotion.active ? "Deactivate" : "Activate";
            actionButton.setAttribute("aria-label", `${actionButton.textContent} ${promotion.name}`);
            actionCell.appendChild(actionButton);
            row.appendChild(actionCell);

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


async function performPromotionAction(button) {
    const promotionId = button.dataset.promotionId;
    const action = button.dataset.action;
    const actionMessage = document.getElementById("action-message");
    const actionVerb = action === "activate" ? "activate" : "deactivate";

    actionMessage.textContent = "";
    actionMessage.dataset.state = "";
    button.disabled = true;

    try {
        const response = await fetch(
            `/api/promotions/${encodeURIComponent(promotionId)}/${action}`,
            {
                method: "PUT",
                headers: { Accept: "application/json" },
            },
        );
        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(result.message || `Request failed (HTTP ${response.status}).`);
        }

        const expectedActive = action === "activate";
        if (result.active !== expectedActive) {
            throw new Error("The server did not confirm the requested Promotion state.");
        }

        const row = button.closest('[data-testid="promotion-row"]');
        row.querySelector('[data-testid="promotion-active"]').textContent = String(result.active);
        button.dataset.action = result.active ? "deactivate" : "activate";
        button.textContent = result.active ? "Deactivate" : "Activate";
        button.setAttribute("aria-label", `${button.textContent} ${result.name}`);

        const actionResult = action === "activate" ? "activated" : "deactivated";
        actionMessage.textContent = `Promotion ${promotionId} ${actionResult} successfully.`;
        actionMessage.dataset.state = "success";
    } catch (error) {
        actionMessage.textContent = `Unable to ${actionVerb} Promotion ${promotionId}: ${error.message}`;
        actionMessage.dataset.state = "error";
    } finally {
        button.disabled = false;
    }
}


document.getElementById("promotion-list").addEventListener("click", (event) => {
    const button = event.target.closest('[data-testid="promotion-action"]');
    if (button) {
        performPromotionAction(button);
    }
});


async function createPromotion(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const message = document.getElementById("create-message");
    const submitButton = form.querySelector('button[type="submit"]');

    message.textContent = "";
    message.dataset.state = "";

    const invalidField = form.querySelector(":invalid");

    if (invalidField) {
        message.textContent =
            `Please enter a valid ${invalidField.name.replaceAll("_", " ")}.`;
        message.dataset.state = "error";
        invalidField.focus();
        return;
    }

    const values = new FormData(form);

    const promotion = {
        name: values.get("name").trim(),
        promotion_type: values.get("promotion_type"),
        value: Number(values.get("value")),
        product_id: Number(values.get("product_id")),
        start_date: values.get("start_date"),
        end_date: values.get("end_date"),
        active: form.elements.namedItem("active").checked
    };

    submitButton.disabled = true;

   
    try {
        const response = await fetch("/api/promotions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json"
            },
            body: JSON.stringify(promotion)
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                result.message || "Could not create promotion."
            );
        }

        form.reset();

        await loadPromotions();

        message.textContent = "Promotion created successfully!";
        message.dataset.state = "success";

    } catch (error) {
        message.textContent = error.message;
        message.dataset.state = "error";
    } finally {
        submitButton.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("create-promotion-form");

    if (form) {
        form.addEventListener("submit", createPromotion);
    }
});
