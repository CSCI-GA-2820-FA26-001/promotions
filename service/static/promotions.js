const PROMOTIONS_API = "/api/promotions";


function renderPromotions(promotions) {
    const tbody = document.getElementById("promotion-list");

    tbody.replaceChildren();

    const fields = [
        "id",
        "name",
        "promotion_type",
        "value",
        "product_id",
        "start_date",
        "end_date",
        "active",
    ];

    promotions.forEach((promotion) => {
        const row = document.createElement("tr");
        row.setAttribute("data-testid", "promotion-row");

        fields.forEach((field) => {
            const cell = document.createElement("td");

            cell.textContent = String(promotion[field] ?? "—");
            cell.setAttribute(
                "data-testid",
                `promotion-${field}`,
            );

            row.appendChild(cell);
        });

        const actionCell = document.createElement("td");
        const deleteButton = document.createElement("button");

        deleteButton.type = "button";
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";
        deleteButton.setAttribute(
            "data-testid",
            "delete-promotion"
        );
        deleteButton.dataset.promotionId = promotion.id;

        deleteButton.addEventListener(
            "click",
            deletePromotion
        );

        actionCell.appendChild(deleteButton);
        row.appendChild(actionCell);

        tbody.appendChild(row);
    });
}


async function loadPromotions(queryString = "") {
    const tbody = document.getElementById("promotion-list");
    const listMessage = document.getElementById("list-message");
    const queryMessage = document.getElementById("flash-message");
    const isQuery = queryString !== "";

    if (isQuery) {
        queryMessage.textContent = "Searching Promotions...";
    } else {
        listMessage.textContent = "Loading promotions...";
    }

    tbody.replaceChildren();

    try {
        const response = await fetch(
            `${PROMOTIONS_API}${queryString}`,
            {
                headers: { Accept: "application/json" },
            },
        );

        if (!response.ok) {
            throw new Error("Unable to load Promotions.");
        }

        const promotions = await response.json();

        if (!Array.isArray(promotions)) {
            throw new Error("Invalid API response");
        }

        if (promotions.length === 0) {
            if (isQuery) {
                queryMessage.textContent =
                    "No matching Promotions were found.";
                listMessage.textContent = "";
            } else {
                listMessage.textContent =
                    "No promotions available.";

                if (queryMessage) {
                    queryMessage.textContent = "";
                }
            }

            return;
        }

        renderPromotions(promotions);

        if (isQuery) {
            queryMessage.textContent =
                `${promotions.length} Promotion(s) found.`;
            listMessage.textContent = "";
        } else {
            listMessage.textContent = "";

            if (queryMessage) {
                queryMessage.textContent = "";
            }
        }

    } catch (error) {
        tbody.replaceChildren();

        if (isQuery) {
            queryMessage.textContent = error.message;
        } else {
            listMessage.textContent =
                "Unable to load promotions.";
            listMessage.setAttribute(
                "data-testid",
                "list-error",
            );
        }
    }
}


async function createPromotion(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const message =
        document.getElementById("create-message");
    const submitButton =
        form.querySelector('button[type="submit"]');

    message.textContent = "";
    message.dataset.state = "";

    const invalidField = form.querySelector(":invalid");

    if (invalidField) {
        message.textContent =
            `Please enter a valid ${
                invalidField.name.replaceAll("_", " ")
            }.`;
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
        active: form.elements.namedItem("active").checked,
    };

    submitButton.disabled = true;

    try {
        const response = await fetch(PROMOTIONS_API, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify(promotion),
        });

        const result =
            await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                result.message ||
                "Could not create promotion.",
            );
        }

        form.reset();

        await loadPromotions();

        message.textContent =
            "Promotion created successfully!";
        message.dataset.state = "success";

    } catch (error) {
        message.textContent = error.message;
        message.dataset.state = "error";
    } finally {
        submitButton.disabled = false;
    }
}


async function deletePromotion(event) {
    const button = event.currentTarget;
    const promotionId = button.dataset.promotionId;
    const message = document.getElementById("delete-message");

    message.textContent = "";
    message.dataset.state = "";

    const confirmed = window.confirm(
        "Are you sure you want to delete this Promotion?"
    );

    if (!confirmed) {
        return;
    }

    button.disabled = true;

    try {
        const response = await fetch(
            `${PROMOTIONS_API}/${promotionId}`,
            {
                method: "DELETE",
                headers: {
                    Accept: "application/json",
                },
            },
        );

        if (!response.ok) {
            throw new Error("Unable to delete Promotion.");
        }

        await loadPromotions();

        message.textContent =
            "Promotion deleted successfully!";
        message.dataset.state = "success";

    } catch (error) {
        message.textContent =
            "Unable to delete Promotion.";
        message.dataset.state = "error";
        button.disabled = false;
    }
}


async function searchPromotions() {
    const attributeSelect =
        document.getElementById("query-attribute");
    const valueInput =
        document.getElementById("query-value");
    const queryMessage =
        document.getElementById("flash-message");

    const attribute = attributeSelect.value;
    const value = valueInput.value.trim();

    if (!value) {
        queryMessage.textContent =
            "Please enter a search value.";
        return;
    }

    const params = new URLSearchParams();
    params.set(attribute, value);

    await loadPromotions(`?${params.toString()}`);
}


async function clearSearch() {
    const attributeSelect =
        document.getElementById("query-attribute");
    const valueInput =
        document.getElementById("query-value");
    const queryMessage =
        document.getElementById("flash-message");

    valueInput.value = "";
    attributeSelect.selectedIndex = 0;

    await loadPromotions();

    queryMessage.textContent = "";
}


document.addEventListener("DOMContentLoaded", () => {
    const form =
        document.getElementById("create-promotion-form");
    const searchButton =
        document.getElementById("search-btn");
    const clearButton =
        document.getElementById("clear-btn");

    if (form) {
        form.addEventListener(
            "submit",
            createPromotion,
        );
    }

    if (searchButton) {
        searchButton.addEventListener(
            "click",
            searchPromotions,
        );
    }

    if (clearButton) {
        clearButton.addEventListener(
            "click",
            clearSearch,
        );
    }

    loadPromotions();
});
