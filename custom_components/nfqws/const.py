"""Constants for the NFQWS HA integration."""

DOMAIN = "nfqws"
DEFAULT_NAME = "NFQWS HA"

CONF_SSH_PORT = "ssh_port"
DEFAULT_SSH_PORT = 222

CONF_WEB_PORT = "web_port"
DEFAULT_WEB_PORT = 90

CONF_STATUS_MONITORING = "status_monitoring"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30

CONF_OPENWRT_MODE = "openwrt_mode"

# Commands for different platforms
CMD_STATUS_KEENETIC = "/opt/etc/init.d/S51nfqws status"
CMD_START_KEENETIC = "/opt/etc/init.d/S51nfqws start"
CMD_STOP_KEENETIC = "/opt/etc/init.d/S51nfqws stop"
CMD_RESTART_KEENETIC = "/opt/etc/init.d/S51nfqws restart"

CMD_STATUS_OPENWRT = "service nfqws-keenetic status"
CMD_START_OPENWRT = "service nfqws-keenetic start"
CMD_STOP_OPENWRT = "service nfqws-keenetic stop"
CMD_RESTART_OPENWRT = "service nfqws-keenetic restart"