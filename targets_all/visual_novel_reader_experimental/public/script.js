document.addEventListener('DOMContentLoaded', () => {
    const dialogueEl = document.getElementById('dialogue');
    const nextBtn = document.getElementById('btn-next');
    const continueBtn = document.getElementById('btn-continue');
    const restartBtn = document.getElementById('btn-restart');

    let sentences = [];
    let currentIndex = 0;
    const storageKey = 'vn_progress';

    function showSentence(index) {
        if (index >= 0 && index < sentences.length) {
            dialogueEl.textContent = sentences[index];
            currentIndex = index;
            nextBtn.style.display = (index >= sentences.length - 1) ? 'none' : 'inline-block';
        }
    }

    function saveProgress() {
        localStorage.setItem(storageKey, currentIndex);
    }

    function loadProgress() {
        const savedIndex = parseInt(localStorage.getItem(storageKey), 10);
        if (!isNaN(savedIndex) && savedIndex > 0 && savedIndex < sentences.length) {
            continueBtn.style.display = 'inline-block';
            continueBtn.dataset.targetIndex = savedIndex;
        } else {
            continueBtn.style.display = 'none';
        }
    }

    fetch('/story.txt')
        .then(response => response.text())
        .then(text => {
            sentences = text.replace(/\n/g, ' ').split(/(?<=[.?!])\s+/).map(s => s.trim()).filter(s => s.length > 0);
            showSentence(0);
            loadProgress();
        });

    nextBtn.addEventListener('click', () => {
        if (currentIndex < sentences.length - 1) {
            showSentence(currentIndex + 1);
            saveProgress();
        }
    });

    continueBtn.addEventListener('click', () => {
        const targetIndex = parseInt(continueBtn.dataset.targetIndex, 10);
        showSentence(targetIndex);
        saveProgress();
        continueBtn.style.display = 'none';
    });

    restartBtn.addEventListener('click', () => {
        localStorage.removeItem(storageKey);
        showSentence(0);
        continueBtn.style.display = 'none';
    });
});