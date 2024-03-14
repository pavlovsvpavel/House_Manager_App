function redirectToHouseBillDetails(houseBillId, detailsCurrentHouse) {
    window.location.href = detailsCurrentHouse.replace("0", houseBillId);
}

function redirectToClientDetails(clientId, detailsCurrentClient) {
    window.location.href = detailsCurrentClient.replace("0", clientId);
}

function redirectToClientBillDetails(clientBillId, detailsCurrentClientBill) {
    window.location.href = detailsCurrentClientBill.replace("0", clientBillId);
}

function redirectToHouseClients(houseId, currentHouseClients) {
    window.location.href = currentHouseClients.replace("0", houseId);
}