# KaryoKE website: server setup

For whoever runs the website on the Compute Canada (Alliance cloud) VM. This is done once by the
maintainer; people using the website never run any of this, they just open its link.

## Current setup on the lab VPS

- Public link: **http://198.168.184.43:8086** (no domain yet; the VPS opens ports 8080-8090).
- Code: `/data/public_html/KaryoKE-web` (main.py in `src/`, settings in `src/.env`), packages in its `.venv`.
  Owned by `root:www-data`: the site can read its code but not change it.
- Service: `/etc/systemd/system/karyoke-web.service` runs `python main.py` as `www-data`. With no
  `DEVELOPMENT=true` in `.env`, main.py starts gunicorn on the unix socket `/run/karyoke-web/karyoke-web.sock`.
- nginx: `/etc/nginx/sites-available/KaryoKE-web`, listens on 8086 and forwards to that socket;
  logs in `/data/logs/KaryoKE-web/`. Modelled on the mCODEBrowser site on the same VPS.
- nginx sends the files in `src/static/` (logo, style.css, input.js) itself, straight from disk; only the
  pages and karyoke runs go to gunicorn. See "Static files" under step 3.
- After code changes (see "Socket and www-data" below for why sudo):
  ```bash
  cd /data/public_html/KaryoKE-web
  sudo git pull
  sudo $(which uv) sync --frozen                 # only if pyproject.toml / uv.lock changed
  sudo chown -R root:www-data .
  sudo systemctl restart karyoke-web
  ```
- Later: once kildealab.com points to the VPS, add the domain and HTTPS (steps 5 and 6).

## Socket and www-data (switching the lab VPS over, 2026-11)

Before: gunicorn on `127.0.0.1:5001`, running as your own user, set in the systemd file.
After: `python main.py` decides by itself. `DEVELOPMENT=true` in `.env` (your own computer) gives the
test server on http://localhost:PORT; anything else (the VPS) gives gunicorn on a unix socket that only
nginx uses. The service runs as `www-data`, the same user as nginx, and the code belongs to `root`.

**1. On your own computer**, copy `main.py`, `app/config.py` and `.env.example` into your repo's `src/`
(`src/main.py`, `src/app/config.py`, `src/.env.example`). Add `DEVELOPMENT=true` to your own `src/.env`
and check `python main.py` still opens on http://localhost:5001. Commit and push.

**2. On the VPS**, stop the site and give the folder to root:www-data:

```bash
sudo systemctl stop karyoke-web
cd /data/public_html/KaryoKE-web
sudo chown -R root:www-data .                  # root owns it, the www-data group can read it
sudo chmod -R u+rwX,g+rX,g-w,o-w .             # www-data may read and run, not change
sudo git pull                                  # sudo from now on: the folder belongs to root
grep -i development src/.env                   # must print nothing, or DEVELOPMENT=false
sudo chmod 640 src/.env                        # .env readable by root and www-data only
git config --global --add safe.directory /data/public_html/KaryoKE-web   # git status etc. without sudo
```

**3. The run folder.** Old runs in `TEMP_FOLDER` belong to your user, and www-data could not clean them up.
Delete the folder; the site makes a new one as www-data on its first run:

```bash
grep TEMP_FOLDER src/.env                      # default /tmp/karyoke-web if nothing is printed
sudo rm -rf /tmp/karyoke-web                   # or the folder printed above
```

**4. Check www-data can run everything:**

```bash
cd /data/public_html/KaryoKE-web/src
sudo -u www-data ../.venv/bin/python -c "import fasthtml, gunicorn, uvicorn_worker; print('python ok')"
sudo -u www-data KaryoKE/executable/karyoke -v
```

Both must work. If the first says `Permission denied` with a path in your home folder, uv made `.venv`
with a Python from your home that www-data cannot open; rebuild it with the system Python:
`cd .. && sudo rm -rf .venv && sudo $(which uv) sync --frozen --python /usr/bin/python3`.

**5. The new service file** (replaces the old one):

```bash
sudo tee /etc/systemd/system/karyoke-web.service > /dev/null <<'EOF'
[Unit]
Description=KaryoKE website
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/data/public_html/KaryoKE-web/src
ExecStart=/data/public_html/KaryoKE-web/.venv/bin/python main.py
# Makes /run/karyoke-web, owned by www-data, for the socket
RuntimeDirectory=karyoke-web
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl restart karyoke-web
systemctl status karyoke-web                   # "active (running)"; q to quit
ls -l /run/karyoke-web/                        # karyoke-web.sock, owned by www-data
curl -sI --unix-socket /run/karyoke-web/karyoke-web.sock http://localhost/ | head -1   # HTTP/1.1 200 OK
```

If it is not running, `journalctl -u karyoke-web -n 30` shows why.

**6. Point nginx at the socket.** In `/etc/nginx/sites-available/KaryoKE-web`, change the `proxy_pass` line to:

```nginx
        proxy_pass http://unix:/run/karyoke-web/karyoke-web.sock;
```

```bash
sudo nginx -t                                  # "syntax is ok" and "test is successful"
sudo systemctl reload nginx
curl -sI http://localhost:8086 | head -1       # HTTP/1.1 200 OK
```

Then open http://198.168.184.43:8086, press Ctrl+Shift+R and draw karyograms once to check runs work.
Copy the new service and nginx files into the repo's `deploy/` folder too.

The steps below are the general recipe; the lab VPS differs where the list above says so.

Throughout, replace:

- `YOUR_USER` with your login name on the VM (`whoami` prints it)
- `/home/YOUR_USER/karyoke-web` with where the karyoke-web folder is (`cd` into it, then `pwd` prints it)
- `8086` with the port in your `.env`, if it differs

The VM is assumed to be Ubuntu or Debian (`cat /etc/os-release` shows which). On AlmaLinux/Rocky,
use `sudo dnf install` instead of `sudo apt install`, and the nginx file goes in `/etc/nginx/conf.d/`.

The finished setup:

```
visitor's browser ──https──> nginx (ports 80/443, public) ──> gunicorn (127.0.0.1:8086, VM only) ──> main.py ──> karyoke
```

## Step 0. Already done: karyoke built, uv installed, `uv run main.py` works

```bash
sudo apt install g++ libcairo2-dev pkg-config          # if not done yet, then build karyoke with make
cp karyoke /home/YOUR_USER/karyoke-web/KaryoKE/executable/karyoke
cd /home/YOUR_USER/karyoke-web
cp .env.example .env                                     # set PORT=8086 (and TEMP_FOLDER) in it
uv sync                                                  # installs the packages into .venv/
```

## Step 1. Run it with gunicorn (test by hand)

`uv run main.py` is the quick test server. For real use, **gunicorn** runs the site with two
workers and only listens on the VM itself (`127.0.0.1`), never directly on the internet:

```bash
cd /home/YOUR_USER/karyoke-web
.venv/bin/gunicorn -k uvicorn_worker.UvicornWorker --bind 127.0.0.1:8086 --workers 2 --timeout 330 main:app
```

In a second SSH window: `curl -I http://localhost:8086` should answer `HTTP/1.1 200 OK`.
Then stop gunicorn with Ctrl-C; step 2 starts it automatically from now on.

`--timeout 330` is a bit above `TIMEOUT_SECONDS` (300), so karyoke's own timeout message reaches the user first.

## Step 2. Keep it running: a systemd service

systemd starts the site when the VM boots and restarts it if it crashes, so no terminal has to stay
open. Everything here runs on the VM, in your SSH session.

First stop any `uv run main.py` or gunicorn you started by hand (Ctrl-C), so port 8086 is free, and
check gunicorn is installed:

```bash
cd /home/YOUR_USER/karyoke-web
ls .venv/bin/gunicorn                        # if "No such file": uv sync
```

Create the service file. Run this **from inside the karyoke-web folder**: it fills in your user
name (`whoami`) and the folder (`pwd`) by itself.

```bash
sudo tee /etc/systemd/system/karyoke-web.service > /dev/null <<EOF
[Unit]
Description=KaryoKE website
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/.venv/bin/gunicorn -k uvicorn_worker.UvicornWorker --bind 127.0.0.1:8086 --workers 2 --timeout 330 main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
cat /etc/systemd/system/karyoke-web.service  # check the paths are real, e.g. /home/samy/karyoke-web
```

If your `main.py` is inside a `src/` folder (your coworker's layout), add `--chdir $(pwd)/src` right after
`gunicorn` in the ExecStart line, and run the block from the folder that holds `pyproject.toml` and `.venv`.

Then, from any folder:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now karyoke-web      # start now and at every boot
systemctl status karyoke-web                 # should say "active (running)"; q to quit
curl -I http://localhost:8086                # HTTP/1.1 200 OK
```

The site now runs in the background; `uv run` is no longer needed. If it is not running,
`journalctl -u karyoke-web -n 30` shows why.

## Step 3. nginx: the public entrance

nginx listens on the normal web port (80, later 443 for HTTPS) and passes visitors to gunicorn.

```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/karyoke-web
```

Paste:

```nginx
server {
    listen 80;
    server_name karyoke.kildealab.com;     # the website's address

    location / {
        proxy_pass http://127.0.0.1:8086;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50m;          # same as MAX_INPUT_MB
        proxy_read_timeout 330s;
    }
}
```

Then turn it on, and turn off nginx's default welcome page:

```bash
sudo ln -s /etc/nginx/sites-available/karyoke-web /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t                                # must say "syntax is ok" and "test is successful"
sudo systemctl reload nginx
curl -I http://localhost                     # HTTP/1.1 200 OK, now through nginx
```

### Static files (logo, style.css, input.js)

nginx can send these straight from disk, which is faster and keeps the Python workers free for karyoke
runs. Add this inside the `server { ... }` block, above `location /`, with the real path to `static/`:

```nginx
    location ~ ^/(KaryoKE_logo\.svg|style\.css|input\.js)$ {
        root /data/public_html/KaryoKE-web/src/static;
        expires 1h;
    }
```

`sudo nginx -t && sudo systemctl reload nginx`, then `curl -I http://localhost:8086/style.css` should show
`Cache-Control: max-age=3600` (only nginx adds it). A new file in `static/` needs its name added to that line;
`python main.py` on your own computer still serves them without nginx.

## Step 4. Open the VM to the internet (Alliance cloud dashboard)

In the OpenStack dashboard of your cloud project (for example Arbutus):

1. **Floating IP**: Compute → Instances → your VM → *Associate Floating IP*. This is the VM's
   public address. Skip if it already has one (it is the address you SSH to).
2. **Security group**: Network → Security Groups → the VM's group (often `default`) →
   *Manage Rules* → *Add Rule*: **HTTP** (port 80) and **HTTPS** (port 443), remote `0.0.0.0/0`.
   Do not open 8086.
3. If the VM itself runs a firewall (`sudo ufw status` says active): `sudo ufw allow 'Nginx Full'`.

Test from your own computer: `http://<floating IP>` in a browser should show the KaryoKE page.
(nginx answers on the IP even before the name exists, because it is the only site on the VM.)

## Step 5. The name: karyoke.kildealab.com

Whoever manages the kildealab.com domain (where it was registered, or the lab's IT) adds one DNS record:

| Type | Name | Value |
|---|---|---|
| A | `karyoke` | the floating IP |

It takes from minutes to a few hours to work everywhere. `nslookup karyoke.kildealab.com` on your
computer shows the floating IP once it does; then `http://karyoke.kildealab.com` opens the site.

## Step 6. HTTPS (the padlock)

Only after step 5 works, on the VM:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d karyoke.kildealab.com
```

certbot asks for an email (for expiry warnings), gets a free Let's Encrypt certificate, adds HTTPS
to the nginx file and renews it automatically. The public link is now
**https://karyoke.kildealab.com**, ready for the lab site's Software page.

## Settings

In `.env` (see `.env.example`); `sudo systemctl restart karyoke-web` after a change:

| Setting | Default | Meaning |
|---|---|---|
| `DEVELOPMENT` | false | `true` on your own computer: `python main.py` gives the test server on PORT |
| `SOCKET_PATH` | `/run/karyoke-web/karyoke-web.sock` | Production only: where gunicorn listens for nginx |
| `WORKERS` | 2 | Production only: gunicorn worker processes |
| `TEMP_FOLDER` | `/tmp/karyoke-web` | Where each run gets its folder (must be writable by YOUR_USER) |
| `PORT` | 5001 | Development only: the test server's port |
| `KEEP_MINUTES` | 60 | How long a run's viewer and summary can be opened |
| `MAX_INPUT_MB` | 50 | Largest upload or paste (keep nginx's `client_max_body_size` the same) |
| `TIMEOUT_SECONDS` | 300 | A karyoke run taking longer is stopped |
| `MAX_JOBS` | 2 | karyoke runs at the same time, per gunicorn worker |
| `SECRET_KEY` | random | Not needed today (no logins) |

The karyoke executable is always `KaryoKE/executable/karyoke`.

## Updating later

- **karyoke**: rebuild and copy over `KaryoKE/executable/karyoke`. The next run uses it; no restart needed.
- **The website's Python files**: copy them over, then `sudo systemctl restart karyoke-web`.
