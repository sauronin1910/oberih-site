/* Автоматичне перемикання полів форми Block залежно від обраного типу блоку */
(function () {
    "use strict";

    function toggleFieldContainer(container, show) {
        if (!container) return;
        if (show) {
            container.classList.remove("oberih-hidden-field");
        } else {
            container.classList.add("oberih-hidden-field");
        }
    }

    function updateBlockContainer(selectEl) {
        var val = selectEl.value;
        var root =
            selectEl.closest(".inline-related") ||
            selectEl.closest("tr.form-row") ||
            selectEl.closest("form");
        if (!root) return;

        var isText = val === "p" || val === "h2" || val === "notice";
        var isList = val === "list" || val === "steps";
        var isTable = val === "table";

        var textField = root.querySelector(".field-text");
        var itemsField = root.querySelector(".field-items_text");
        var tableCaptionField = root.querySelector(".field-table_caption");
        var tableTextField = root.querySelector(".field-table_text");

        toggleFieldContainer(textField, isText);
        toggleFieldContainer(itemsField, isList);
        toggleFieldContainer(tableCaptionField, isTable);
        toggleFieldContainer(tableTextField, isTable);
    }

    function initAllBlockSelects() {
        var selects = document.querySelectorAll(
            'select[name="block_type"], select[name$="-block_type"]'
        );
        selects.forEach(function (selectEl) {
            updateBlockContainer(selectEl);
            if (!selectEl.dataset.oberihBound) {
                selectEl.dataset.oberihBound = "1";
                selectEl.addEventListener("change", function () {
                    updateBlockContainer(selectEl);
                });
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initAllBlockSelects();
        document.addEventListener("formset:added", function () {
            initAllBlockSelects();
        });
        var observer = new MutationObserver(function () {
            initAllBlockSelects();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();

