# smartbizchat
Install Docker and Docker Compose:
sudo apt install docker.io -y
sudo apt install docker-compose -y

Install Python and pip:
sudo apt install python3 -y
sudo apt install python3-pip -y

Use a virtual environment:
sudo apt install python3-venv -y
python3 -m venv myenv
source myenv/bin/activate

Install and configure nginx:
sudo apt install nginx -y
cd /var/www/html
sudo mkdir chat-widget
sudo vim /etc/nginx/sites-available/chat-widget
sudo nginx -t
sudo systemctl reload nginx

Embed widget:
<!-- BizBooster Chat Widget Embed Code -->
<!-- Replace YOUR_API_KEY with the API key provided by BizBooster -->
<script>
(function() {
    const iframe = document.createElement('iframe');
    iframe.src = 'https://<vps_ip>';
    iframe.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 420px;
        height: 600px;
        border: none;
        z-index: 999999;
        background: transparent;
        pointer-events: auto;
    `;

    document.body.appendChild(iframe);
})();
</script>

Host flask backend:
pip install flask gunicorn
mkdir -p /var/www/flask-app
cd /var/www/flask-app
gunicorn --bind 0.0.0.0:5000 --timeout 900 app:app&
sudo vim /etc/nginx/sites-available/flask-backend
sudo ln -s /etc/nginx/sites-available/flask-backend /etc/nginx/sites-enabled/
sudo systemctl reload nginx

Restart gunicorn:
pkill -f gunicorn
gunicorn --bind 0.0.0.0:5000 --timeout 900 app:app&

Docker compose:
docker compose --profile cpu up

Docker:
docker ps
docker exec -it <container_name_or_id> bash
psql -U postgres

postgres:
docker exec -it postgres psql -U postgres
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);






