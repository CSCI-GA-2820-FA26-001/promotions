const promotionsTableBody = document.getElementById("promotion-list");
const detailsPanel = document.getElementById("promotion-details");
const lookupStatus = document.getElementById("lookup-status");

const detailFields = {
    id: "promotion-id",
    name: "promotion-name",
    promotion_type: "promotion-type",
    value: "promotion-value",
    start_date: "promotion-start-date",
    end_date: "promotion-end-date",
    created_at: "promotion-created-at",
    updated_at: "promotion-updated-at",
};


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
            const viewButton = document.createElement("button");
            viewButton.type = "button";
            viewButton.className = "view-details-btn";
            viewButton.dataset.promotionId = promotion.id;
            viewButton.textContent = "View details";
            actionCell.appendChild(viewButton);
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


function setDetailText(elementId, value) {
    document.getElementById(elementId).textContent = value ?? "—";
}


function clearDetails() {
    Object.values(detailFields).forEach((elementId) => setDetailText(elementId, ""));
    setDetailText("promotion-product-id", "");
    setDetailText("promotion-active", "");
}


function displayPromotion(promotion) {
    Object.entries(detailFields).forEach(([field, elementId]) => {
        setDetailText(elementId, promotion[field]);
    });
    setDetailText(
        "promotion-product-id",
        promotion.product_id === null ? "Store-wide" : promotion.product_id,
    );
    setDetailText("promotion-active", promotion.active ? "Active" : "Inactive");
}


async function loadPromotion(promotionId) {
    detailsPanel.hidden = false;
    clearDetails();

    if (!/^[1-9]\d*$/.test(String(promotionId))) {
        lookupStatus.textContent = "Enter a valid Promotion ID.";
        return;
    }

    lookupStatus.textContent = "Loading Promotion details…";

    try {
        const response = await fetch(`/api/promotions/${encodeURIComponent(promotionId)}`, {
            headers: { Accept: "application/json" },
        });

        if (response.status === 404) {
            lookupStatus.textContent = `Promotion ${promotionId} was not found.`;
            return;
        }
        if (!response.ok) {
            lookupStatus.textContent = `Unable to load Promotion details (HTTP ${response.status}).`;
            return;
        }

        displayPromotion(await response.json());
        lookupStatus.textContent = `Promotion ${promotionId} loaded.`;
    } catch (error) {
        lookupStatus.textContent = "Unable to connect to the Promotions service.";
    }
}


promotionsTableBody.addEventListener("click", (event) => {
    const viewButton = event.target.closest(".view-details-btn");
    if (!viewButton) {
        return;
    }

    const promotionId = viewButton.dataset.promotionId;
    const url = new URL(window.location.href);
    url.searchParams.set("id", promotionId);
    window.history.replaceState({}, "", url);
    loadPromotion(promotionId);
});


const initialPromotionId = new URLSearchParams(window.location.search).get("id");
if (initialPromotionId) {
    loadPromotion(initialPromotionId);
}
