document.addEventListener('DOMContentLoaded', function () {
    const apartmentCheckboxes = document.querySelectorAll('[name="based_on_apartment"]');
    const peopleCheckboxes = document.querySelectorAll('[name="based_on_total_people"]');
    const saveButton = document.querySelector('button.btn[type="submit"]');
    const fixedTaxCheckbox = document.getElementById('id_fixed_monthly_taxes');
    const calcOptionsWrapper = document.getElementById('calc-options-wrapper');

    const checkboxMap = {};
    const allUniqueExpenseValues = new Set();

    // 1. Collect all unique expense values
    apartmentCheckboxes.forEach(cb => allUniqueExpenseValues.add(cb.value));
    peopleCheckboxes.forEach(cb => allUniqueExpenseValues.add(cb.value));

    // 2. Populate checkboxMap
    allUniqueExpenseValues.forEach(value => {
        checkboxMap[value] = {
            apartment: document.querySelector(`[name="based_on_apartment"][value="${value}"]`),
            people: document.querySelector(`[name="based_on_total_people"][value="${value}"]`)
        };
    });

    function updateSaveButtonState() {
        if (fixedTaxCheckbox && fixedTaxCheckbox.checked) {
            saveButton.disabled = false;
            return;
        }

        if (allUniqueExpenseValues.size === 0) {
            saveButton.disabled = false;
            return;
        }

        const allOptionsConfigured = Array.from(allUniqueExpenseValues).every(value => {
            const config = checkboxMap[value];
            const isApartmentSelected = config.apartment && config.apartment.checked;
            const isPeopleSelected = config.people && config.people.checked;

            return isApartmentSelected || isPeopleSelected;
        });

        saveButton.disabled = !allOptionsConfigured;
    }

    function updateCheckboxPairDisabledStates() {
        allUniqueExpenseValues.forEach(value => {
            const config = checkboxMap[value];

            if (config.apartment && config.people) {
                config.apartment.disabled = false;
                config.people.disabled = false;

                if (config.apartment.checked) {
                    config.people.disabled = true;
                } else if (config.people.checked) {
                    config.apartment.disabled = true;
                }
            } else if (config.apartment) {
                config.apartment.disabled = false;
            } else if (config.people) {
                config.people.disabled = false;
            }
        });
    }

    function toggleCalcOptions() {
        if (!fixedTaxCheckbox || !calcOptionsWrapper) return;

        if (fixedTaxCheckbox.checked) {
            calcOptionsWrapper.style.display = 'none';
        } else {
            calcOptionsWrapper.style.display = 'block';
        }

        updateSaveButtonState();
    }

    function handleCheckboxChange() {
        updateCheckboxPairDisabledStates();
        updateSaveButtonState();
    }

    // Add listeners to calculation checkboxes
    allUniqueExpenseValues.forEach(value => {
        const config = checkboxMap[value];
        if (config.apartment) config.apartment.addEventListener('change', handleCheckboxChange);
        if (config.people) config.people.addEventListener('change', handleCheckboxChange);
    });

    if (fixedTaxCheckbox) {
        fixedTaxCheckbox.addEventListener('change', toggleCalcOptions);
    }

    // Initialize states on page load
    updateCheckboxPairDisabledStates();
    toggleCalcOptions();
});