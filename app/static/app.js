// Invoice form: dynamic line-item rows.
document.addEventListener("DOMContentLoaded", () => {
  const items = document.getElementById("items");
  const addBtn = document.getElementById("add-item");
  if (!items || !addBtn) return;

  const templateRow = items.querySelector(".item-row");

  addBtn.addEventListener("click", () => {
    const row = templateRow.cloneNode(true);
    row.querySelectorAll("input").forEach((input) => {
      if (input.name === "description") input.value = "";
      if (input.name === "quantity") input.value = "1";
      if (input.name === "unit_price") input.value = "0";
    });
    items.appendChild(row);
  });

  items.addEventListener("click", (event) => {
    if (!event.target.classList.contains("remove-item")) return;
    if (items.querySelectorAll(".item-row").length > 1) {
      event.target.closest(".item-row").remove();
    }
  });
});
