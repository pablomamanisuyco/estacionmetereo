#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <time.h>

// ===== CONFIGURACIÓN WiFi =====
const char* ssid = "PABLOJEF";
const char* password = "alfawise2790Dote";

// ===== CONFIGURACIÓN HIVEMQ =====
const char* mqtt_server = "f97725ae76b641a3b27f3cfee11cc92a.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "Huamanga2";
const char* mqtt_password = "Huamanga12";

// ===== TÓPICO ÚNICO =====
const char* mqtt_topic = "estacion/datos";

// ===== CLIENTES =====
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ===== VARIABLES =====
unsigned long lastMsg = 0;
const long interval = 300000;  // Enviar datos cada 5 minutos (300000 ms)
char msg[512];

// ===== CONFIGURACIÓN DE HORA =====
// Ajusta a tu zona si lo necesitas. Aquí está en UTC-5 (Perú)
const long gmtOffset_sec = -5 * 3600;
const int daylightOffset_sec = 0;

void setup_wifi();
void reconnect();
void publishData();
String getTimestamp();

void setup() {
  Serial.begin(115200);
  delay(10);

  randomSeed((uint32_t)esp_random());

  // Para pruebas rápidas: no validar certificado TLS (INSEGURO para producción)
  espClient.setInsecure();

  // Inicializar WiFi
  setup_wifi();

  // Inicializar NTP
  configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org", "time.nist.gov");

  // Esperar breve por sincronización NTP
  time_t now = time(nullptr);
  int waitSec = 0;
  while (now < 1600000000 && waitSec < 10) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
    waitSec++;
  }
  Serial.println();
  if (now >= 1600000000) {
    Serial.println("Hora NTP sincronizada");
  } else {
    Serial.println("Advertencia: no se pudo sincronizar hora NTP (se usará hora del sistema)");
  }

  // Configurar servidor MQTT
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    publishData();
  }
}

void setup_wifi() {
  Serial.println();
  Serial.print("Conectando a WiFi: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi conectado");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Fallo al conectar WiFi");
  }
}

void reconnect() {
  int attempts = 0;
  while (!client.connected() && attempts < 5) {
    Serial.print("Intentando conectar MQTT...");
    String clientId = "ESP32_Estacion_";
    clientId += String((uint32_t)esp_random(), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("conectado");
      client.subscribe("estacion/comando");
    } else {
      Serial.print("fallo, rc=");
      Serial.print(client.state());
      Serial.println(" reintentando en 5s");
      delay(5000);
      attempts++;
    }
  }
}

String getTimestamp() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return String("1970-01-01T00:00:00");
  }
  char buf[32];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  return String(buf);
}

void publishData() {
  // Generar datos aleatorios simulando sensores
  float temperatura = 15.0 + (random(0, 100) / 10.0);    // 15.0 - 25.0
  float humedad = 30.0 + (random(0, 700) / 10.0);        // 30.0 - 100.0
  float presion = 1005.0 + (random(0, 200) / 10.0);      // ~1005 - 1025
  float velocidad_viento = random(0, 250) / 10.0;        // 0.0 - 25.0
  int lluvia = random(0, 101);                          // 0 - 100 %

  String ts = getTimestamp();

  // Construir un único JSON con todos los valores y timestamp
 snprintf(msg, sizeof(msg),
         "{\"timestamp\":\"%s\",\"temperatura\":%.2f,\"humedad\":%.1f,"
         "\"presion\":%.2f,\"viento\":%.1f,\"lluvia\":%d}",
         ts.c_str(), temperatura, humedad, presion, velocidad_viento, lluvia);


  // Publicar en un solo tópico
  client.publish(mqtt_topic, msg);

  // Mostrar en serie para depuración
  Serial.print("Publicando en ");
  Serial.print(mqtt_topic);
  Serial.print(": ");
  Serial.println(msg);
  Serial.println("---");
}
