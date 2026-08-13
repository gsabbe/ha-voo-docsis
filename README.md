# VOO Technicolor DOCSIS Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for monitoring **DOCSIS cable modem metrics** from Technicolor routers provided by the ISP **VOO** in Belgium (e.g., Technicolor CGA4233VOO).

## Features
- 🔌 **UI Configuration Flow**: Configure modem IP, username, and password directly in Home Assistant without editing configuration YAML.
- 🔒 **Secure Authentication**: Implements the 2-stage PBKDF2 HMAC-SHA256 authentication required by Technicolor VOO gateways.
- 📊 **DOCSIS Signal Metrics**:
  - Cable Modem Status (`CMStatus`)
  - Active Upstream Channels count & per-channel power levels (`dBmV`)
  - Active Downstream Channels count, per-channel power levels (`dBmV`), and SNR levels (`dB`)
  - DOCSIS 3.1 OFDM Downstream Power & SNR
  - Corrected & Uncorrectable Error Codewords counters
- ⚡ **Hardware Diagnostics**: CPU Usage (`%`), Memory Free (`MB`), Total Memory (`MB`), Firmware Version, Model Name, and System Uptime.

---

## Installation

### Method 1: HACS (Recommended)
1. Open **HACS** in Home Assistant.
2. Click the 3 dots in the top right corner and select **Custom repositories**.
3. Enter the repository URL: `https://github.com/gsabbe/ha-voo-docsis`
4. Select Category: **Integration**.
5. Click **Add**, then find **VOO Technicolor DOCSIS Monitor** and click **Download**.
6. Restart Home Assistant.

### Method 2: Manual Installation
1. Copy the `custom_components/voo_docsis` directory into your Home Assistant `<config_dir>/custom_components/`.
2. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **VOO Technicolor DOCSIS Monitor**.
3. Fill in the configuration dialog:
   - **Host / IP**: `192.168.100.1` (or your modem's IP address)
   - **Username**: `voo` (or modem login)
   - **Password**: Your modem web interface password
   - **Update Interval**: `30` (seconds)
4. Click **Submit**.

---

## Technical Details

### Reverse-Engineered Technicolor API
- **Stage 1 (Salt Request)**: `POST /api/v1/session/login` with `username: "voo"` and `password: "seeksalthash"`.
- **PBKDF2 Calculation**:
  - `hashed1 = PBKDF2_HMAC_SHA256(password, salt, 1000, 16).hex()`
  - `final_password = PBKDF2_HMAC_SHA256(hashed1, saltwebui, 1000, 16).hex()`
- **Stage 2 (Session Login)**: `POST /api/v1/session/login` with `username: "voo"` and `password: final_password`.
- **Data Requests**: Passes `X-CSRF-TOKEN` header and `PHPSESSID` session cookies for `/api/v1/modem` and `/api/v1/system`.

---

## License
[MIT License](LICENSE)
