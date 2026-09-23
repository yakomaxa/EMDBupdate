<!-- Modal Overlay -->
<div id="modal" onclick="if(event.target === this) closeModal()">
  <div class="modal-body" onclick="event.stopPropagation()">
    <!-- Top Navigation Header: <  ×  > -->
    <div class="modal-nav-header">
      <button type="button" class="nav-btn prev-btn" onclick="prevImage(); event.stopPropagation();" title="Previous">&#10094;</button>
      <button type="button" class="close-btn" onclick="closeModal(); event.stopPropagation();" title="Close">&times;</button>
      <button type="button" class="nav-btn next-btn" onclick="nextImage(); event.stopPropagation();" title="Next">&#10095;</button>
    </div>

    <div class="modal-images">
      <div class="img-box">
        <h4>Primary Surface Render</h4>
        <a id="emdbMainLink" href="#" target="_blank">
          <img id="emdbMainImg" src="" alt="EMDB Release Image">
        </a>
      </div>
    </div>

    <div class="modal-details">
      <h3 id="modalAcc"></h3>
      <div class="modal-title" id="modalTitle"></div>
      <div class="modal-meta">
        <p><strong>Authors:</strong> <span id="modalAuthors"></span></p>
        <p><strong>Status:</strong> <span id="modalStatus" class="badge"></span> | <strong>Release Date:</strong> <span id="modalDate"></span></p>
      </div>
      <div class="modal-links">
        <a id="linkEMDB" href="#" target="_blank" class="btn">View Entry on EMDB</a>
        <a id="linkEMNavi" href="#" target="_blank" class="btn btn-secondary">View on EMNavi</a>
      </div>
    </div>

    <div id="modalIndex"></div>
  </div>
</div>

<script>
const entries = [
{{IMAGE_DATA}}
];

let currentIndex = 0;

function openModal(index) {
  currentIndex = index;
  updateModal();
  document.getElementById("modal").style.display = "flex";
  document.body.style.overflow = "hidden";
}

function updateModal() {
  const entry = entries[currentIndex];
  if (!entry) return;

  const accUpper = entry.id.toUpperCase();
  const accLower = entry.id.toLowerCase();
  const numId = accLower.replace("emd-", "").replace("emd_", "");

  document.getElementById("modalAcc").textContent = accUpper;
  document.getElementById("modalTitle").textContent = entry.title;
  document.getElementById("modalAuthors").textContent = entry.authors;
  document.getElementById("modalStatus").textContent = entry.status;
  document.getElementById("modalDate").textContent = entry.date;
  document.getElementById("modalIndex").textContent = `${currentIndex + 1} / ${entries.length}`;

  const mainImg = document.getElementById("emdbMainImg");
  mainImg.src = entry.img_url;
  mainImg.onerror = function() {
    this.src = "https://www.ebi.ac.uk/emdb/static/images/emdb_placeholder.png";
  };

  document.getElementById("emdbMainLink").href = entry.link;
  document.getElementById("linkEMDB").href = entry.link;
  document.getElementById("linkEMNavi").href = `https://pdbj.org/emnavi/quick.php?id=${numId}`;
}

function closeModal() {
  document.getElementById("modal").style.display = "none";
  document.body.style.overflow = "auto";
}

function nextImage() {
  currentIndex = (currentIndex + 1) % entries.length;
  updateModal();
}

function prevImage() {
  currentIndex = (currentIndex - 1 + entries.length) % entries.length;
  updateModal();
}

// Keyboard Controls
document.addEventListener("keydown", function(event) {
  if (document.getElementById("modal").style.display === "flex") {
    if (event.key === "ArrowRight") nextImage();
    if (event.key === "ArrowLeft") prevImage();
    if (event.key === "Escape") closeModal();
  }
});

// Touch / Swipe Controls for Mobile Devices
let touchStartX = 0;
let touchEndX = 0;

const modalBody = document.querySelector(".modal-body");

if (modalBody) {
  modalBody.addEventListener("touchstart", function (event) {
    touchStartX = event.changedTouches[0].screenX;
  }, { passive: true });

  modalBody.addEventListener("touchend", function (event) {
    touchEndX = event.changedTouches[0].screenX;
    handleSwipe();
  }, { passive: true });
}

function handleSwipe() {
  const swipeThreshold = 50;
  if (touchEndX < touchStartX - swipeThreshold) {
    nextImage();
  }
  if (touchEndX > touchStartX + swipeThreshold) {
    prevImage();
  }
}
</script>

