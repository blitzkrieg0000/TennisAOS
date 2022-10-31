var detailModal = document.getElementById('detailModal');
detailModal.addEventListener('show.bs.modal', function (event) {
    // Button that triggered the modal
    var button = event.relatedTarget

    // Extract info from data-bs-* attributes
    var raw = button.getAttribute('data-bs-whatever')
    data = JSON.parse(raw)
    console.log(data)
    var modalTitle = detailModal.querySelector('.modal-title')
    modalTitle.textContent = 'Details: ' + data["process"]["id"]

    var court_score_description = detailModal.querySelector("#court_score_description")
    var court_score = detailModal.querySelector("#court_score")
    if (data["processResponse"]["score"] != null) {
        court_score.innerHTML = "Puan: " + data["processResponse"]["score"];
        court_score_description.value = data["processResponse"]["score"];
    } else {
        court_score.innerHTML = "Puan: 0";
        court_score_description.value = "Puan: 0";
    }

    var court_description = detailModal.querySelector("#court_description");
    court_description.value = data["processResponse"]["description"];

    var court_sourceName = detailModal.querySelector("#court_sourceName");
    court_sourceName.value = data["stream"]["name"];

    var court_sourceUrl = detailModal.querySelector("#court_topicName");
    court_sourceUrl.value = data["processResponse"]["kafkaTopicName"];

    var court_sourceUrl = detailModal.querySelector("#court_sourceUrl")
    court_sourceUrl.value = data["stream"]["source"]

    var court_isVideo = detailModal.querySelector("#court_isVideo")
    if (data["stream"]["is_video"]) {
        court_isVideo.value = "Videodan Alındı."
    } else {
        court_isVideo.value = "Kameradan Alındı."
    }

    var imgbase64 = "data:image/png;base64, " + data["processResponse"]["canvas"]

    var court_image_gallery = detailModal.querySelector("#court_image_gallery")

    court_image_gallery.setAttribute('data-src', imgbase64);

    var image = detailModal.querySelector("#court_image")
    image.style = "background-image:url('" + imgbase64 + "');"

});