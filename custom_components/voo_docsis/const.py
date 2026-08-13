"""Constants for the VOO Technicolor DOCSIS integration."""

DOMAIN = "voo_docsis"
DEFAULT_NAME = "VOO Technicolor Modem"
DEFAULT_HOST = "192.168.100.1"
DEFAULT_USERNAME = "voo"
DEFAULT_SCAN_INTERVAL = 30

# Configuration keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Sensor Keys
SENSOR_CM_STATUS = "cm_status"
SENSOR_CPU_USAGE = "cpu_usage"
SENSOR_MEM_FREE = "mem_free"
SENSOR_MEM_TOTAL = "mem_total"
SENSOR_UPTIME = "uptime"
SENSOR_SOFTWARE_VERSION = "software_version"
SENSOR_MODEL_NAME = "model_name"
SENSOR_ACTIVE_US_CHANNELS = "active_upstream_channels"
SENSOR_ACTIVE_DS_CHANNELS = "active_downstream_channels"
SENSOR_TOTAL_CORRECTEDS = "total_correcteds"
SENSOR_TOTAL_UNCORRECTABLES = "total_uncorrectables"
SENSOR_OFDM_POWER = "ofdm_power_level"
SENSOR_OFDM_SNR = "ofdm_snr_level"
