# pi_player

## Intro

pi_player is an application that extends the use of camilladsp to a fully functional preamp/streamer, controlled via IR remote control and/or rotary encoder.

## Features 
* Supports any remote control
	* Key mapping defined in config file
* Inputs
	* User-defined inputs (e.g TV, streamer, analog)
	* Direct input selection
	* Scroll through inputs
	* 3 modes per input -- direct, EQ and EQ alt.
	* EQ can be turned on or off (direct)
* Volume Control
	* Coarse (3.0dB) or fine (0.5dB) steps.
	* Volume dim (20dB)
	* Events throttling to control adjustment speed
	* Via remote control or rotary encoder
	* Volume level displayed on screen during adjustment
* Squeezelite
	* Play, pause, stop, prev track, next track.
	* Multiple display options, such as album art image or track info (album, artist, title, bitrate)
	* Continuously updates display with up-to-date information

# Installation

## Prerequisites
### Initial RPi installation
> Credits to @mdsimon2 on providing detailed instructions in this this [ASR thread](https://www.audiosciencereview.com/forum/index.php?threads/rpi4-camilladsp-tutorial.29656/)
1. Using `Raspberry Pi Imager`, install `Ubuntu Server 23.10 (64-bit)` on an SD card. RPi 4 recommended.
2. Install SD card, power up RPi and start a terminal.
3. Update RPi and install packages
```
sudo apt update
sudo apt full-upgrade
sudo apt install -- alsa-utils linux-modules-extra-raspi python3 python3-pip python3-venv python3-dev unzip ir-keytable
```

### CamillaDSP
1. Download:
```
mkdir ~/camilladsp ~/camilladsp/coeffs ~/camilladsp/configs
wget https://github.com/HEnquist/camilladsp/releases/download/v2.0.3/camilladsp-linux-aarch64.tar.gz -P ~/camilladsp/
sudo tar -xvf ~/camilladsp/camilladsp-linux-aarch64.tar.gz -C /usr/local/bin/
```

2. Create and configure CamillaDSP config files (out of scope for these instructions)
3. Download CamillaGUI:
```
mkdir ~/venv
python3 -m venv ~/venv
~/venv/bin/pip install --upgrade pip
~/venv/bin/pip install -- aiohttp git+https://github.com/HEnquist/pycamilladsp.git git+https://github.com/HEnquist/pycamilladsp-plot.git
 
wget https://github.com/HEnquist/camillagui-backend/releases/download/v2.1.0/camillagui.zip -P ~/camilladsp/
unzip ~/camilladsp/camillagui.zip -d ~/camilladsp/camillagui
rm ~/camilladsp/camillagui.zip 
```
4. Test CamillaGUI. Expected output:
```
$ ~/venv/bin/python ~/camilladsp/camillagui/main.py
======== Running on http://0.0.0.0:5005 ========
(Press CTRL+C to quit)
```

#### Create services
1. `sudo nano /lib/systemd/system/camilladsp.service`
```
[Unit]
After=syslog.target
StartLimitIntervalSec=10
StartLimitBurst=10

[Service]
Type=simple
User=<username>
WorkingDirectory=~
ExecStart=camilladsp -s camilladsp/statefile.yml -w -g-40 -o camilladsp/camilladsp.log -p 1234
Restart=always
RestartSec=1
StandardOutput=journal
StandardError=journal
SyslogIdentifier=camilladsp
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=10

[Install]
WantedBy=multi-user.target
```
2. `sudo nano /lib/systemd/system/camillagui.service`
```
[Unit]
Description=CamillaDSP Backend and GUI
After=multi-user.target

[Service]
Type=idle
User=<username>
WorkingDirectory=~
ExecStart=/home/<username>/venv/bin/python camilladsp/camillagui/main.py

[Install]
WantedBy=multi-user.target
```
3. Enable and run services:
```
sudo systemctl enable -- camilladsp camillagui
sudo service camillagui start
sudo service camilladsp start
```

### Squeezelite
1. Install: `sudo apt install squeezelite`
2. Modify config: `sudo nano /etc/default/squeezelite`
```
SL_SOUNDCARD="hw:Loopback,1"
SB_EXTRA_ARGS="-W -C 30 -r 44100-44100 -R hLE:::28 -U PCM"
```
3. Configure loopback: `echo snd-aloop | sudo tee /etc/modules-load.d/snd-aloop.conf`
4. Restart: `sudo service squeezelite restart`


### Pigpio
1. Download:
```
cd ~/src
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
rm master.zip
cd pigpio-master
```
2. Modify Makefile to install in venv. Replace `if which python3; then python3 ...` with `if which python3; then /home/<username>/venv/bin/python3 ...`
3. Build and install:
```
make
sudo make install
```
Run: `sudo pigpiod`
<!-- TODO: add instructions to do this on startup -->

## pi_player
### Setup IR reciever
1. Configure device with `sudo nano /boot/firmware/config.txt`

```
# Add to end of file. GPIO should match the output pin of the IR receiver
dtoverlay=gpio-ir,gpio_pin=22
```

2. Reboot `sudo reboot`

### Download
1. Clone the repo and install dependencies
```
mkdir ~/src
git clone https://github.com/itsikhefez/pi_player.git ~/src/pi_player
~/venv/bin/pip install -- Pillow luma.oled luma.lcd evdev pysqueezebox
```
2. Copy and customize `config.yaml`
```
cp config.yaml config.main.yaml
```

3. Run:
```
~/venv/bin/python ~/src/pi_player/main.py --log INFO --config-path ~/src/pi_player/config.main.yaml
```

## Troubleshooting

### RuntimeError: No access to /dev/mem.  Try running as root!
<!-- TODO: add instructions to do this on startup -->
```
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
```

### FileNotFoundError: [Errno 2] No such file or directory: '/dev/input/event0'
IR device not setup properly.
* `cat /proc/bus/input/devices` to view devices
* `lsmod | grep gpio` output should include a row for `gpio_ir_recv` e.g
```
raspberrypi_gpiomem    12288  0
gpio_ir_recv           12288  0
```

### Remote not receiving events
* Ensure the correct protocol is enabled.
* Run `ir-keytable -c -p all -t` to test which protocol the remote is using.
* Run `sudo ir-keytable -p <protocol>` to enable correct protocol on next boot.
<!-- TODO: add instructions to do this on startup -->
