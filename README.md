# NFQWS HA - Home Assistant Integration

🌐 **Itegration for managing NFQWS service on Keenetic/OpenWRT routers via SSH.**

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.9%2B-blue.svg)](https://www.home-assistant.io)

## Features

- ⚡ **Full NFQWS2 Support** – Compatible with the latest script paths
- 🔄 **Legacy Compatibility** – Toggle between NFQWS v1 and v2 with a single checkbox.
- 📊 **Monitor NFQWS service status** - Real-time status monitoring
- 🌐 **Dual platform support** - Keenetic/Netcraze and OpenWRT compatibility
- 🎯 **Configurable monitoring** - Adjust update intervals to your needs
- 🌍 **Multi-language support** - English and Russian interfaces

## Supported Platforms

### Fully Tested & Supported
- **Keenetic routers** with Entware

### Experimental Support
- **OpenWRT devices** - *Theoretical support, needs community testing*

> ⚠️ **OpenWRT Note:** OpenWRT support is implemented based on the official NFQWS documentation but has not been tested due to lack of suitable hardware. If you have an OpenWRT device with NFQWS installed, please test and provide feedback!

## 🛠️ Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click on **"Integrations"**
3. Click **"+"** and select **"Custom repositories"**
4. Add this repository URL: `https://github.com/IdadonI/nfqws-ha`
5. Install **"NFQWS HA"** integration
6. Restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy the `custom_components/nfqws` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add integration via **Settings → Devices & Services → Add Integration → "NFQWS HA"**

## 🎮 Entities and Controls 

### Sensors
| Entity | Description |
|--------|-------------|
| **NFQWS Status** | Current service status (requires monitoring) |
| **NFQWS Version** | Installed NFQWS version |

### Buttons
| Entity | Description |
|--------|-------------|
| **NFQWS Start** | Start the NFQWS service |
| **NFQWS Stop** | Stop the NFQWS service |
| **NFQWS Restart** | Restart the NFQWS service |

---
*Disclaimer: This integration is not affiliated with Keenetic or the NFQWS developers. Use it at your own risk.*