document.getElementById('profile_picture-clear_id').addEventListener('click', function () {
    const profilePictureLink = this.previousElementSibling;
    profilePictureLink.innerText = '';
    profilePictureLink.href = '';
});