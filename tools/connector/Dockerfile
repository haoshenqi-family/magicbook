FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY builder.py halo_client.py magicbook_client.py mapping.py notify.py server.py ./
COPY templates/ templates/
COPY config/ config/
EXPOSE 9878
CMD ["gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:9878", "server:app"]
