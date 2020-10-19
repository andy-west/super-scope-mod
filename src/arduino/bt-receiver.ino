//#include <SoftwareSerial.h>
#include <NeoSWSerial.h>

const int COMPOSITE_SYNC_PIN = 2;
const int VERTICAL_SYNC_PIN = 3;

const int BLUETOOTH_RX_PIN = 4;
const int BLUETOOTH_TX_PIN = 5;

const int TRIGGER_PIN = 8;
const int CURSOR_PIN = 9;
const int TURBO_PIN = 10;
const int PAUSE_PIN = 11;
const int EXTERNAL_LATCH_PIN = 12;  // Raster gate

const byte BT_MESSAGE_TRIGGER_PRESSED = 231;
const byte BT_MESSAGE_TRIGGER_RELEASED = 232;
const byte BT_MESSAGE_CURSOR_PRESSED = 233;
const byte BT_MESSAGE_CURSOR_RELEASED = 234;
const byte BT_MESSAGE_TURBO_ENABLED = 235;
const byte BT_MESSAGE_TURBO_DISABLED = 236;
const byte BT_MESSAGE_PAUSE_PRESSED = 237;
const byte BT_MESSAGE_PAUSE_RELEASED = 238;
const byte BT_MESSAGE_TV_NOT_VISIBLE = 239;
const byte BT_MESSAGE_AIM_X = 240;
const byte BT_MESSAGE_AIM_Y = 241;

const byte BT_MESSAGE_NONE = 0;
byte lastBluetoothMessage = BT_MESSAGE_NONE;

bool isTriggerPressed = false;
bool isCursorPressed = false;
bool isTurboEnabled = false;
bool isPausePressed = false;
bool isTvVisible = false;

const int minAimLine = 10;
const int maxAimLine = 240;
const int minAimMicroseconds = 5;
const int maxAimMicroseconds = 55;

int aimLine = (maxAimLine - minAimLine + 1) / 2 + minAimLine;
int aimMicroseconds = (maxAimMicroseconds - minAimMicroseconds + 1) / 2 + minAimMicroseconds;

volatile int currentLine = 0;

//SoftwareSerial bluetoothSerial(BLUETOOTH_RX_PIN, BLUETOOTH_TX_PIN);
NeoSWSerial bluetoothSerial(BLUETOOTH_RX_PIN, BLUETOOTH_TX_PIN);

void setup() {
  bluetoothSerial.begin(9600);
  Serial.begin(9600);

  pinMode(COMPOSITE_SYNC_PIN, INPUT);
  pinMode(VERTICAL_SYNC_PIN, INPUT);

  pinMode(TRIGGER_PIN, OUTPUT);
  pinMode(CURSOR_PIN, OUTPUT);
  pinMode(TURBO_PIN, OUTPUT);
  pinMode(PAUSE_PIN, OUTPUT);
  pinMode(EXTERNAL_LATCH_PIN, OUTPUT);

  digitalWrite(TRIGGER_PIN, HIGH);
  digitalWrite(CURSOR_PIN, HIGH);
  digitalWrite(TURBO_PIN, HIGH);
  digitalWrite(PAUSE_PIN, HIGH);
  digitalWrite(EXTERNAL_LATCH_PIN, HIGH);

  attachInterrupt(digitalPinToInterrupt(COMPOSITE_SYNC_PIN), handleCompositeSync, RISING);
  attachInterrupt(digitalPinToInterrupt(VERTICAL_SYNC_PIN), handleVerticalSync, RISING);

  Serial.println("Super Scope BT receiver started.");
}

void loop() {
  if (bluetoothSerial.available() > 0) {
    int inputByte = bluetoothSerial.read();

    switch (inputByte) {
      case BT_MESSAGE_TRIGGER_PRESSED:
        digitalWrite(TRIGGER_PIN, LOW);
        Serial.println("Trigger pressed.");
        break;
      case BT_MESSAGE_TRIGGER_RELEASED:
        digitalWrite(TRIGGER_PIN, HIGH);
        Serial.println("Trigger released.");
        break;
      case BT_MESSAGE_CURSOR_PRESSED:
        digitalWrite(CURSOR_PIN, LOW);
        Serial.println("Cursor pressed.");
        break;
      case BT_MESSAGE_CURSOR_RELEASED:
        digitalWrite(CURSOR_PIN, HIGH);
        Serial.println("Cursor released.");
        break;
      case BT_MESSAGE_TURBO_ENABLED:
        digitalWrite(TURBO_PIN, LOW);
        Serial.println("Turbo enabled.");
        break;
      case BT_MESSAGE_TURBO_DISABLED:
        digitalWrite(TURBO_PIN, HIGH);
        Serial.println("Turbo disabled.");
        break;
      case BT_MESSAGE_PAUSE_PRESSED:
        digitalWrite(PAUSE_PIN, LOW);
        Serial.println("Pause pressed.");
        break;
      case BT_MESSAGE_PAUSE_RELEASED:
        digitalWrite(PAUSE_PIN, HIGH);
        Serial.println("Pause pressed.");
        break;
      case BT_MESSAGE_TV_NOT_VISIBLE:
        isTvVisible = false;
        break;
      case BT_MESSAGE_AIM_X:
      case BT_MESSAGE_AIM_Y:
        isTvVisible = true;
        break;
    }

    if (inputByte > 230) {
      lastBluetoothMessage = inputByte;
    }
    else {
      switch (lastBluetoothMessage) {
        case BT_MESSAGE_AIM_X:
          aimMicroseconds = inputByte + minAimMicroseconds;
          break;
        case BT_MESSAGE_AIM_Y:
          aimLine = inputByte + minAimLine;
          break;
      }
    }
  }
}

void handleCompositeSync() {
  currentLine++;
  
  if (isTvVisible && currentLine == aimLine) {
    delayMicroseconds(aimMicroseconds);
    digitalWrite(EXTERNAL_LATCH_PIN, LOW);
    delayMicroseconds(5);
    digitalWrite(EXTERNAL_LATCH_PIN, HIGH);
  }
}

void handleVerticalSync() {
  currentLine = 0;
}
