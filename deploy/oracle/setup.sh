#!/usr/bin/env bash
# One-off setup of a fresh Oracle Cloud Ubuntu 24.04 VM (Ampere A1, Always Free).
#   curl -fsSL https://raw.githubusercontent.com/albertoqv/el-regista/main/deploy/oracle/setup.sh | bash
set -euo pipefail

# Docker Engine + Compose plugin from Docker's own repository.
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
  docker-compose-plugin unattended-upgrades
sudo usermod -aG docker "$USER"

# Oracle's Ubuntu images reject everything but SSH in iptables, on top of the
# cloud's security list: open HTTP/HTTPS here too and keep it across reboots.
for port in 80 443; do
  sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport "$port" -j ACCEPT
done
sudo iptables -C INPUT -p udp --dport 443 -j ACCEPT 2>/dev/null \
  || sudo iptables -I INPUT 6 -p udp --dport 443 -j ACCEPT
sudo netfilter-persistent save

# Security updates on their own, rebooting at 05:00 if a kernel needs it.
echo 'Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "05:00";' \
  | sudo tee /etc/apt/apt.conf.d/51elregista >/dev/null

[ -d "$HOME/el-regista" ] || git clone https://github.com/albertoqv/el-regista.git "$HOME/el-regista"
cp -n "$HOME/el-regista/deploy/oracle/.env.example" "$HOME/el-regista/deploy/oracle/.env"
chmod 600 "$HOME/el-regista/deploy/oracle/.env"

echo
echo "Listo. Cierra la sesión SSH y vuelve a entrar (grupo docker), rellena"
echo "  ~/el-regista/deploy/oracle/.env"
echo "y lanza  ~/el-regista/deploy/oracle/deploy.sh"
