# Używamy oficjalnego lekkiego obrazu Pythona
FROM python:3.11-slim

# Instalujemy FFmpeg globalnie w systemie (niezbędny dla yt-dlp do łączenia obrazu i dźwięku)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Ustawiamy katalog roboczy dla naszej aplikacji
WORKDIR /app

# Kopiujemy listę wymagań i instalujemy je
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę plików aplikacji (kod, folder public)
COPY . .

# Tworzymy folder na pliki tymczasowe
RUN mkdir -p tmp_downloads

# Informujemy, że aplikacja działa na porcie 3000
EXPOSE 3000

# Komenda startowa wykorzystująca produkcyjny serwer Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:3000", "--timeout", "120", "--workers", "2", "app:app"]
