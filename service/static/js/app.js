const PROMOTIONS_API = "/promotions";

const attributeSelect = document.getElementById("query-attribute");
const valueInput = document.getElementById("query-value");
const searchButton = document.getElementById("search-btn");
const clearButton = document.getElementById("clear-btn");
const resultsBody = document.getElementById("search-results");
const flashMessage = document.getElementById("flash-message");


function showMessage(message) {
    flashMessage.textContent = message;
}


function renderPromotions(promotions) {
    resultsBody.replaceChildren();

    if (promotions.length === 0) {
        showMessage("No matching Promotions were found.");
        return;
    }

    promotions.forEach((promotion) => {
        const row = document.createElement("tr");

        const values = [
            promotion.id,
            promotion.name,
            promotion.promotion_type,
            promotion.value,
            promotion.product_id ?? "Store-wide",
            promotion.start_date,
            promotion.end_date,
            promotion.active,
        ];

        values.forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });

        resultsBody.appendChild(row);
    });

    showMessage(`${promotions.length} Promotion(s) found.`);
}


async function loadPromotions(queryString = "") {
    try {
        const response = await fetch(`${PROMOTIONS_API}${queryString}`);

        if (!response.ok) {
            throw new Error("Unable to load Promotions.");
        }

        const promotions = await response.json();
        renderPromotions(promotions);
    } catch (error) {
        resultsBody.replaceChildren();
        showMessage(error.message);
    }
}


async function searchPromotions() {
    const attribute = attributeSelect.value;
    const value = valueInput.value.trim();

    if (!value) {
        showMessage("Please enter a search value.");
        return;
    }

    const params = new URLSearchParams();
    params.set(attribute, value);

    await loadPromotions(`?${params.toString()}`);
}


async function clearSearch() {
    valueInput.value = "";
    attributeSelect.selectedIndex = 0;
    await loadPromotions();
}


searchButton.addEventListener("click", searchPromotions);
clearButton.addEventListener("click", clearSearch);
