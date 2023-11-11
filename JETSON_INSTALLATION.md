# Jetson Nano

## Anmeldedaten

* User/Password: gruppe38/singularity
* Computername: stairway-jones
* Zugreifen via Micro USB SSH: ssh gruppe38@192.168.55.1
* Zugreifen via WLAN: Mobile Hotspot einrichten mit SSID=stairway-jones und Passwort=singularity, dann auf dem Nano sudo ip link set wlan0 up

## Zu Jetson Nano via Micro-USB verbinden

* https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-2gb-devkit#setup

## Mit einem WiFi verbinden

1. sudo nmcli r wifi on
1. sudo nmcli d wifi list
1. sudo nmcli d wifi connect my_wifi password <password>
1. sudo nmcli c add type wifi con-name <name> ifname wlan0 ssid <ssid>
1. sudo nmcli c modify <name> wifi-sec.key-mgmt wpa-psk wifi-sec.psk <password>

Falls wlan0 down: sudo ip link set wlan0 up
Falls Fehler, dass blockiert: sudo rfkill unblock wifi

Wichtig: WLAN Password darf nur hexadezimale Charakter enthalten.

## Raspberry PI Camera ausprobieren

* https://github.com/JetsonHacksNano/CSI-Camera
* https://www.youtube.com/watch?v=dHvb225Pw1s

## Python installieren

Python ist bereits standardmässig installiert auf dem Jetson Nano.

## OpenCV installieren

OpenCV ist bereits standardmässig installiert auf dem Jetson Nano (v4.1.1).

## TensorFlow installieren

* https://docs.nvidia.com/deeplearning/frameworks/install-tf-jetson-platform/index.html

## Sonstige Pakete installieren
``sudo apt install graphviz``

## Metrics

* sudo tegrastats

## Python PATH

* export PATH="${PATH}:/home/gruppe38/.local/bin"
* export PYTHONPATH="${PYTHONPATH}:/home/gruppe38/.local/bin"
* add to ~/.bashrc

## Normalen Benutzer Recht geben, Kamera neu zu starten

1. sudo visudo
1. gruppe38        ALL = NOPASSWD: /usr/sbin/service nvargus-daemon restart (ganz an den Schluss der Datei)
1. danach trotzdem mit sudo ausführen: sudo service nvargus-daemon restart

## Berechtigungen für UART erteilen

1. systemctl stop nvgetty
1. systemctl disable nvgetty
1. udevadm trigger
1. sudo usermod -a -G dialout gruppe38
1. sudo usermod -a -G dialout gruppe38
1. vim /etc/udev/rules.d/55-tegraserial.rules mit Inhalt: KERNEL=="ttyTHS*", MODE="0666"

## Performance

* GUI modus abstellen: sudo systemctl set-default multi-user.target (spart mehr als 200MB)

## Buildumgebung einrichten (Jetson Nano)

1. gitlab-runner installieren: https://docs.gitlab.com/runner/install/linux-repository.html
1. SSH keys verifizieren: https://docs.gitlab.com/ee/ci/ssh_keys/#verifying-the-ssh-host-keys
1. sudo groupadd stairway-jones
1. mkdir /usr/local/stairway-jones
1. chown -R gruppe38:stairway-jones /usr/local/stairway-jones
1. /etc/systemd/system/gitlab-runner.service anpassen auf gruppe38-user
1. sudo gitlab-runner uninstall
1. gitlab-runner install --working-directory /home/gruppe38 --user gruppe38
1. sudo systemctl daemon-reload
1. sudo systemctl restart gitlab-runner

## Triton service einrichten

1. sudo cp triton/triton.service /etc/systemd/system/triton.service
1. chmod u+x /usr/local/stairway-jones/triton/start_server.sh
1. sudo systemctl start triton
1. sudo systemctl enable triton
1. sudo visudo
1. gruppe38        ALL = NOPASSWD: /bin/systemctl restart triton.service
1. gruppe38        ALL = NOPASSWD: /bin/systemctl start triton.service
1. gruppe38        ALL = NOPASSWD: /bin/systemctl stop triton.service

## Stairway-Jones Roboter service einrichten

1. sudo cp stairway-jones.service /etc/systemd/system/stairway-jones.service
1. sudo systemctl start stairway-jones
1. sudo systemctl enable stairway-jones

## Audio Device ID herausfinden

1. aplay -l
1. Format ist hw:cardNr,0

### Lautstärke ändern

1. amixer -c 2 (2 = card nr von aplay-l)
1. amixer -c 2 set Speaker 100% 

## FAQ

### Was tun, wenn man segmentation faults in jedem python script bekommt?

Jetson Nano braucht eine spezifische numpy version: pip3 install -U numpy==1.16.1

### Ich kann imgaug nicht installieren, wegen Shapely, was tun?

Shapely nicht installieren:

* pip3 install six numpy scipy Pillow matplotlib scikit-image opencv-python imageio
* pip3 install --no-dependencies imgaug