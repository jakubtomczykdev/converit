document.addEventListener('DOMContentLoaded', () => {
    const videoUrlInput = document.getElementById('videoUrl');
    const convertBtn = document.getElementById('convertBtn');
    const loader = document.getElementById('loader');
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const thumbnail = document.getElementById('thumbnail');
    const videoTitle = document.getElementById('videoTitle');
    const qualitySelect = document.getElementById('qualitySelect');
    const downloadBtn = document.getElementById('downloadBtn');

    let currentVideoInfo = null;

    convertBtn.addEventListener('click', async () => {
        const url = videoUrlInput.value.trim();
        if (!url) {
            showError('Prosze podać link z YouTube');
            return;
        }

        resetUI();
        loader.classList.remove('hidden');

        try {
            const response = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
            const data = await response.json();

            if (data.error) {
                showError(data.error);
                return;
            }

            currentVideoInfo = data;
            displayResult(data);
        } catch (err) {
            showError('Wystąpił błąd podczas pobierania informacji');
        } finally {
            loader.classList.add('hidden');
        }
    });

    downloadBtn.addEventListener('click', () => {
        const url = videoUrlInput.value.trim();
        const itag = qualitySelect.value;
        window.location.href = `/api/download?url=${encodeURIComponent(url)}&itag=${itag}`;
    });

    function displayResult(data) {
        thumbnail.src = data.thumbnail;
        videoTitle.textContent = data.title;

        qualitySelect.innerHTML = '';
        data.formats.forEach(f => {
            const option = document.createElement('option');
            option.value = f.itag;
            let label = `${f.quality} (${f.container})`;
            if (f.height >= 1080) label += ' - Full HD';
            else if (f.height >= 720) label += ' - HD';
            option.textContent = label;
            qualitySelect.appendChild(option);
        });

        if (data.formats.length === 0) {
            const option = document.createElement('option');
            option.textContent = 'Brak dostępnych formatów MP4';
            qualitySelect.appendChild(option);
            downloadBtn.disabled = true;
        } else {
            downloadBtn.disabled = false;
        }

        result.classList.remove('hidden');
    }

    function showError(msg) {
        error.textContent = msg;
        error.classList.remove('hidden');
    }

    function resetUI() {
        result.classList.add('hidden');
        error.classList.add('hidden');
    }
});
