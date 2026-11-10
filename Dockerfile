FROM python:3.12-slim

WORKDIR /app

# Tidak ada dependensi pihak ketiga: cukup salin project.
COPY . /app

# Perintah bawaan: jalankan tiga workflow contoh dalam mode demo
# dan tampilkan ringkasannya. Untuk mode live, teruskan
# OPENROUTER_API_KEY lewat environment container.
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "agentforge", "demo"]
