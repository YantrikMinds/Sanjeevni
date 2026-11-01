/* =====================================================================
 * SANJEEVNI NANO ROVER v2 - firmware (ESP32-S3-WROOM-1-N8R8)
 * Board in Arduino IDE: "ESP32S3 Dev Module", PSRAM: "OPI PSRAM", Flash 8MB,
 * USB CDC On Boot: Enabled.  Works with Arduino-ESP32 core 2.0.x and 3.x.
 * Optional library: "VL53L1X" by Pololu (ToF).  Without it, collision stop is off.
 *
 * What changed vs v1:
 *  - MJPEG stream moved to its own server on port 81 + its own task.
 *    (v1 streamed inside the single-threaded port-80 server, so /drive could not
 *     be answered while video was playing -> rover uncontrollable.)
 *  - Pins come from pinmap.h (generated from the same file as the PCB netlist).
 *  - Real telemetry: battery voltage (ADC divider), tilt (MPU6050), distance (VL53L1X).
 *  - Real safety: flip detection, obstacle stop, Wi-Fi/command watchdog.
 *  - Motors held asleep (nSLEEP low) when idle; IR LED forced off at boot.
 * ===================================================================== */
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include "pinmap.h"

#if __has_include(<VL53L1X.h>)
  #include <VL53L1X.h>
  #define HAVE_TOF 1
  VL53L1X tof;
#else
  #define HAVE_TOF 0
#endif

// ---- Wi-Fi access point. CHANGE THE PASSWORD before field use (min 8 chars) ----
const char* AP_SSID = "SANJEEVNI-NANO-01";
const char* AP_PASS = "change-me-1234";

WebServer server(80);        // control + telemetry
WebServer streamServer(81);  // video only

// ---- motor PWM ----
const int PWM_FREQ = 20000, PWM_RES = 8;
const int MOTOR_PINS[4] = { PIN_MOTOR_L_FWD, PIN_MOTOR_L_REV, PIN_MOTOR_R_FWD, PIN_MOTOR_R_REV };

static void pwmInit() {
  for (int i = 0; i < 4; i++) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcAttachChannel(MOTOR_PINS[i], PWM_FREQ, PWM_RES, i);
#else
    ledcSetup(i, PWM_FREQ, PWM_RES);
    ledcAttachPin(MOTOR_PINS[i], i);
#endif
  }
}
static void pwmWrite(int i, int duty) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(MOTOR_PINS[i], duty);
#else
  ledcWrite(i, duty);
#endif
}

// ---- shared state ----
volatile int   currentSpeed   = 180;      // 0-255
volatile float tiltDeg        = 0.0f;
volatile float obstacleCm     = -1.0f;    // -1 = no reading
volatile bool  flipped        = false;
volatile bool  movingForward  = false;
volatile bool  irOn           = false;
volatile unsigned long lastCommandMs = 0;
const unsigned long FAILSAFE_MS = 2500;   // stop if no command for this long
const float STOP_DIST_CM = 6.0f;          // forward stop distance
const float FLIP_TILT_DEG = 65.0f;

// ---- motors ----
void stopMotors() {
  for (int i = 0; i < 4; i++) pwmWrite(i, 0);
  movingForward = false;
}
static void motorPair(int a, int b, int speed) {
  speed = constrain(speed, -255, 255);
  pwmWrite(a, speed > 0 ? speed : 0);
  pwmWrite(b, speed < 0 ? -speed : 0);
}
void drive(int left, int right) {
  lastCommandMs = millis();
  if (flipped) { stopMotors(); return; }
  digitalWrite(PIN_MOTOR_NSLEEP, HIGH);                       // wake DRV8833
  if (left > 0 && right > 0 && obstacleCm >= 0 && obstacleCm < STOP_DIST_CM) { stopMotors(); return; }
  motorPair(0, 1, left);
  motorPair(2, 3, right);
  movingForward = (left > 0 && right > 0);
}

// ---- battery ----
float batteryVolts() {
  uint32_t mv = 0;
  for (int i = 0; i < 16; i++) mv += analogReadMilliVolts(PIN_VBAT_ADC);
  return (mv / 16.0f) * 2.0f / 1000.0f;          // 100k/100k divider (R15/R16)
}
int batteryPercent(float v) {                    // rough LiPo curve
  static const float tv[] = {3.30,3.50,3.60,3.70,3.80,3.90,4.00,4.10,4.20};
  static const int   tp[] = {0,5,15,30,50,65,80,92,100};
  if (v <= tv[0]) return 0;
  for (int i = 1; i < 9; i++) if (v <= tv[i]) return tp[i-1] + (int)((v - tv[i-1]) / (tv[i] - tv[i-1]) * (tp[i] - tp[i-1]));
  return 100;
}

// ---- sensors (only this task touches the I2C bus) ----
static bool imuOk = false;
static bool imuInit() {
  Wire.beginTransmission(0x68); Wire.write(0x6B); Wire.write(0x00);   // wake MPU6050
  return Wire.endTransmission() == 0;
}
static bool imuTilt(float &deg) {
  Wire.beginTransmission(0x68); Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(0x68, 6) != 6) return false;
  int16_t ax = (Wire.read() << 8) | Wire.read();
  int16_t ay = (Wire.read() << 8) | Wire.read();
  int16_t az = (Wire.read() << 8) | Wire.read();
  float x = ax / 16384.0f, y = ay / 16384.0f, z = az / 16384.0f;     // +-2 g range
  deg = atan2f(sqrtf(x * x + y * y), z) * 180.0f / PI;               // angle from vertical
  return true;
}
void sensorTask(void*) {
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000);
  imuOk = imuInit();
#if HAVE_TOF
  tof.setTimeout(100);
  bool tofOk = tof.init();
  if (tofOk) { tof.setDistanceMode(VL53L1X::Short); tof.setMeasurementTimingBudget(33000); tof.startContinuous(50); }
#endif
  for (;;) {
    float d;
    if (imuOk && imuTilt(d)) { tiltDeg = d; flipped = (d > FLIP_TILT_DEG); if (flipped) stopMotors(); }
#if HAVE_TOF
    if (tofOk && tof.dataReady()) {
      uint16_t mm = tof.read(false);
      obstacleCm = tof.timeoutOccurred() ? -1.0f : mm / 10.0f;
      if (movingForward && obstacleCm >= 0 && obstacleCm < STOP_DIST_CM) stopMotors();
    }
#endif
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

// ---- camera ----
bool initCamera() {
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_4;  c.ledc_timer = LEDC_TIMER_2;
  c.pin_d0 = Y2_GPIO_NUM; c.pin_d1 = Y3_GPIO_NUM; c.pin_d2 = Y4_GPIO_NUM; c.pin_d3 = Y5_GPIO_NUM;
  c.pin_d4 = Y6_GPIO_NUM; c.pin_d5 = Y7_GPIO_NUM; c.pin_d6 = Y8_GPIO_NUM; c.pin_d7 = Y9_GPIO_NUM;
  c.pin_xclk = XCLK_GPIO_NUM; c.pin_pclk = PCLK_GPIO_NUM; c.pin_vsync = VSYNC_GPIO_NUM; c.pin_href = HREF_GPIO_NUM;
  c.pin_sccb_sda = SIOD_GPIO_NUM; c.pin_sccb_scl = SIOC_GPIO_NUM;
  c.pin_pwdn = PWDN_GPIO_NUM; c.pin_reset = RESET_GPIO_NUM;
  c.xclk_freq_hz = 20000000;
  c.pixel_format = PIXFORMAT_JPEG;
  if (psramFound()) {
    c.frame_size = FRAMESIZE_VGA; c.jpeg_quality = 12; c.fb_count = 2;
    c.fb_location = CAMERA_FB_IN_PSRAM; c.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    c.frame_size = FRAMESIZE_QVGA; c.jpeg_quality = 15; c.fb_count = 1; c.fb_location = CAMERA_FB_IN_DRAM;
  }
  if (esp_camera_init(&c) != ESP_OK) { Serial.println("[CAMERA] init failed - check FPC pin map"); return false; }
  sensor_t* s = esp_camera_sensor_get();
  s->set_vflip(s, 1); s->set_hmirror(s, 1);   // set to 0 if your image is upside down
  return true;
}

// ---- video server (port 81) ----
#define PART_BOUNDARY "123456789000000000000987654321"
void handleStream() {
  WiFiClient client = streamServer.client();
  client.print("HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace;boundary=" PART_BOUNDARY
               "\r\nAccess-Control-Allow-Origin: *\r\nCache-Control: no-cache\r\n\r\n");
  while (client.connected()) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) { delay(10); continue; }
    client.print("\r\n--" PART_BOUNDARY "\r\n");
    client.printf("Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", (unsigned)fb->len);
    size_t len = fb->len;
    size_t sent = client.write(fb->buf, len);
    esp_camera_fb_return(fb);
    if (sent == 0) break;                          // client went away
  }
}
void streamTask(void*) {
  streamServer.on("/stream.mjpg", HTTP_GET, handleStream);
  streamServer.begin();
  for (;;) { streamServer.handleClient(); vTaskDelay(pdMS_TO_TICKS(2)); }
}

// ---- control server (port 80) ----
static void cors() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
}
void handleDrive() {
  cors();
  String cmd = server.hasArg("cmd") ? server.arg("cmd") : "stop";
  int spd = server.hasArg("spd") ? constrain(server.arg("spd").toInt(), 0, 255) : currentSpeed;
  if      (cmd == "forward" || cmd == "w") drive(spd, spd);
  else if (cmd == "reverse" || cmd == "s") drive(-spd, -spd);
  else if (cmd == "left"    || cmd == "a") drive(-spd, spd);
  else if (cmd == "right"   || cmd == "d") drive(spd, -spd);
  else { stopMotors(); lastCommandMs = millis(); }
  bool wantFwd = (cmd == "forward" || cmd == "w");
  bool blocked = flipped || (wantFwd && !movingForward);      // flipped, or obstacle too close
  server.send(200, "application/json", String("{\"status\":\"ok\",\"cmd\":\"") + cmd + "\",\"blocked\":" + (blocked ? "true" : "false") + "}");
}
void handleTelemetry() {
  cors();
  float v = batteryVolts();
  String j = "{\"device\":\"SANJEEVNI-NANO-01\"";
  j += ",\"battery_v\":" + String(v, 2);
  j += ",\"battery_pct\":" + String(batteryPercent(v));
  j += ",\"tilt_deg\":" + String(tiltDeg, 1);
  j += ",\"flipped\":" + String(flipped ? "true" : "false");
  j += ",\"clearance_m\":" + (obstacleCm >= 0 ? String(obstacleCm / 100.0f, 2) : String("null"));
  j += ",\"motor_fault\":" + String(digitalRead(PIN_MOTOR_NFAULT) == LOW ? "true" : "false");
  j += ",\"torch\":" + String(irOn ? "true" : "false");
  j += ",\"rssi_clients\":" + String(WiFi.softAPgetStationNum()) + "}";
  server.send(200, "application/json", j);
}
void handleTorch() {
  cors();
  irOn = server.hasArg("on") ? (server.arg("on") == "1") : !irOn;
  digitalWrite(PIN_IR_LED, irOn ? HIGH : LOW);
  server.send(200, "application/json", String("{\"torch\":") + (irOn ? "true" : "false") + "}");
}

// ---- setup / loop ----
void setup() {
  pinMode(PIN_IR_LED, OUTPUT);   digitalWrite(PIN_IR_LED, LOW);     // IR off at boot
  pinMode(PIN_STAT_LED, OUTPUT); digitalWrite(PIN_STAT_LED, HIGH);
  pinMode(PIN_MOTOR_NSLEEP, OUTPUT); digitalWrite(PIN_MOTOR_NSLEEP, LOW);
  pinMode(PIN_MOTOR_NFAULT, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_VBAT_ADC, ADC_11db);
  Serial.begin(115200);
  pwmInit();
  stopMotors();

  bool cam = initCamera();
  WiFi.mode(WIFI_AP);
  WiFi.setTxPower(WIFI_POWER_15dBm);          // lower peak current than 20 dBm; raise if range is short
  WiFi.softAP(AP_SSID, AP_PASS, 1, 0, 2);     // max 2 clients
  Serial.printf("[AP] %s  IP %s  camera:%s\n", AP_SSID, WiFi.softAPIP().toString().c_str(), cam ? "ok" : "FAIL");

  server.on("/drive", HTTP_GET, handleDrive);
  server.on("/telemetry", HTTP_GET, handleTelemetry);
  server.on("/torch", HTTP_GET, handleTorch);
  server.begin();

  xTaskCreatePinnedToCore(sensorTask, "sensors", 4096, nullptr, 2, nullptr, 0);
  if (cam) xTaskCreatePinnedToCore(streamTask, "stream", 8192, nullptr, 1, nullptr, 0);
  digitalWrite(PIN_STAT_LED, cam ? LOW : HIGH);   // LED stays on if camera failed
  lastCommandMs = millis();
}

void loop() {
  server.handleClient();
  if (millis() - lastCommandMs > FAILSAFE_MS) {   // watchdog
    stopMotors();
    digitalWrite(PIN_MOTOR_NSLEEP, LOW);          // sleep driver when idle
  }
  delay(1);
}
