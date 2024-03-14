function selectCurrentHouseID(houseId, storeHouseId, detailsCurrentHouse, csrf_token) {
    // AJAX request to store the selected house id
    fetch(storeHouseId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({house_id: houseId})
    })
        .then(response => {
            if (response.ok) {
                // Redirect to the house details page
                window.location.href = detailsCurrentHouse.replace("0", houseId);
            } else {
                console.error('Failed to store selected house id');
            }
        })
        .catch(error => console.error('Error:', error));
}
