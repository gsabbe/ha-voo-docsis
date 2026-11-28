# VOO Technicolor DOCSIS Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/v/release/gsabbe/ha-voo-docsis)](https://github.com/gsabbe/ha-voo-docsis/releases)
[![License](https://img.shields.io/github/license/gsabbe/ha-voo-docsis)](LICENSE)

Home Assistant integration for monitoring **DOCSIS cable modem metrics** from Technicolor routers provided by the ISP **VOO** in Belgium (e.g., Technicolor CGA4233VOO).

## Features
- 🔌 **UI Configuration & Options Flow**: Configure modem IP, username, masked password, and polling interval directly in Home Assistant — with automatic reauthentication prompts if your modem password changes.
- 🔒 **Secure Authentication**: Implements the 2-stage PBKDF2 HMAC-SHA256 authentication required by Technicolor VOO gateways.
- 📊 **DOCSIS Signal Metrics**:
  - Cable Modem Status (`CMStatus`)
  - Active Upstream Channels count & per-channel power levels (`dBmV`)
  - Active Downstream Channels count, per-channel power levels (`dBmV`), and SNR levels (`dB`)
  - DOCSIS 3.1 OFDM Downstream Power (`dBmV`) & SNR (`dB`)
  - Corrected & Uncorrectable Error Codewords counters
- ⚡ **Hardware Diagnostics**: CPU Usage (`%`), Memory Free (`MB`), Firmware Version, Model Name, and System Uptime.

---

## Installation

### Method 1: Home Assistant Marketplace / HACS (Recommended)

Click the button below to open this repository directly in your Home Assistant **Marketplace** (Home Assistant `2026.11+`, or **HACS** on earlier releases), then select **Install**:

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=gsabbe&repository=ha-voo-docsis&category=integration)

Or search for it from Home Assistant:

- **Home Assistant `2026.11+` (Marketplace)**:
  1. Go to **Settings** -> **Marketplace**.
  2. Search for **VOO Technicolor DOCSIS Monitor** and open its page.
  3. Select **Install**, then confirm **Install** (no GitHub account required).
  4. When prompted, complete the setup dialog (or restart Home Assistant first if a repair under **Settings** -> **System** -> **Repairs** requests it).

- **Home Assistant `2024.11` – `2026.10` (HACS)**:
  1. Open **HACS** in Home Assistant.
  2. Search for **VOO Technicolor DOCSIS Monitor**, open it, and select **Download**.
  3. Restart Home Assistant.

<details>
<summary><b>Fallback: Add as a custom repository</b> (if catalog sync hasn't propagated yet or when installing a fork)</summary>

**In Home Assistant Marketplace (`2026.11+`):**
1. Go to **Settings** -> **Marketplace**.
2. In the upper-right corner, select **Add from link** (connect your GitHub account via device sign-in if prompted).
3. Under **GitHub link**, enter `https://github.com/gsabbe/ha-voo-docsis` and select **Add**.
4. Open **VOO Technicolor DOCSIS Monitor** from the list and select **Install**.

**In standalone HACS:**
1. Open **HACS**, select the three-dots menu (`⋮`) in the top-right corner, and choose **Custom repositories**.
2. Enter `https://github.com/gsabbe/ha-voo-docsis` and select category **Integration**.
3. Select **Add**, then find **VOO Technicolor DOCSIS Monitor**, select **Download**, and restart Home Assistant.

</details>

### Method 2: Manual Installation
1. Download the latest release from [GitHub Releases](https://github.com/gsabbe/ha-voo-docsis/releases).
2. Copy the `custom_components/voo_docsis` directory into your Home Assistant `<config_dir>/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

If the setup dialog did not open automatically after installation, click the button below:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=voo_docsis)

Or add it manually:
1. In Home Assistant, go to **Settings** -> **Devices & services**.
2. Select **Add integration** and search for **VOO Technicolor DOCSIS Monitor**.
3. Fill in the configuration dialog:
   - **Modem IP address or Hostname**: `192.168.100.1` (or your modem's IP address)
   - **Username**: `voo` (or your modem login)
   - **Password**: Your modem web interface password
   - **Update Interval (seconds)**: `60` (adjustable anytime via **Configure** on the integration entry)
4. Select **Submit**.

---

## Technical Details

### Reverse-Engineered Technicolor API
- **Stage 1 (Salt Request)**: `POST /api/v1/session/login` with `username: "voo"` and `password: "seeksalthash"`.
- **PBKDF2 Calculation**:
  - `hashed1 = PBKDF2_HMAC_SHA256(password, salt, 1000, 16).hex()`
  - `final_password = PBKDF2_HMAC_SHA256(hashed1, saltwebui, 1000, 16).hex()`
- **Stage 2 (Session Login)**: `POST /api/v1/session/login` with `username: "voo"` and `password: final_password`.
- **Data Requests**: Passes `X-CSRF-TOKEN` header and `PHPSESSID` session cookies for `/api/v1/session/menu`, `/api/v1/modem`, and `/api/v1/system`.

---

## License
[MIT License](LICENSE)
