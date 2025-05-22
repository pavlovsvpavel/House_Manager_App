document.addEventListener('DOMContentLoaded', function () {
    const apartmentCheckboxes = document.querySelectorAll('[name="based_on_apartment"]');
    const peopleCheckboxes = document.querySelectorAll('[name="based_on_total_people"]');
    const saveButton = document.querySelector('button.btn[type="submit"]');

    const checkboxMap = {};
    const allUniqueExpenseValues = new Set();

    // 1. Collect all unique expense values from both lists
    apartmentCheckboxes.forEach(cb => allUniqueExpenseValues.add(cb.value));
    peopleCheckboxes.forEach(cb => allUniqueExpenseValues.add(cb.value));

    // 2. Populate checkboxMap for each unique expense value
    allUniqueExpenseValues.forEach(value => {
        checkboxMap[value] = {
            apartment: document.querySelector(`[name="based_on_apartment"][value="${value}"]`),
            people: document.querySelector(`[name="based_on_total_people"][value="${value}"]`)
        };
    });

    // Function to update the enabled/disabled state of the Save button
    function updateSaveButtonState() {
        if (allUniqueExpenseValues.size === 0) {
            saveButton.disabled = false;
            return;
        }

        // Check if every unique expense option has a selection
        const allOptionsConfigured = Array.from(allUniqueExpenseValues).every(value => {
            const config = checkboxMap[value];
            const isApartmentSelected = config.apartment && config.apartment.checked;
            const isPeopleSelected = config.people && config.people.checked;

            return isApartmentSelected || isPeopleSelected;
        });

        saveButton.disabled = !allOptionsConfigured;
    }

    // Function to update disabled states of the paired checkboxes
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

    // Combined handler for checkbox changes
    function handleCheckboxChange() {
        updateCheckboxPairDisabledStates();
        updateSaveButtonState();
    }

    // Add event listeners to all relevant checkboxes
    allUniqueExpenseValues.forEach(value => {
        const config = checkboxMap[value];
        if (config.apartment) {
            config.apartment.addEventListener('change', handleCheckboxChange);
        }
        if (config.people) {
            config.people.addEventListener('change', handleCheckboxChange);
        }
    });

    // Initialize states on page load
    updateCheckboxPairDisabledStates();
    updateSaveButtonState();
});