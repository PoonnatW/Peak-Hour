#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

// --- Pin Definitions ---
#define RST_PIN         22 
#define SS_1_PIN        5  
#define SS_2_PIN        4  

const int NR_OF_READERS = 2; 
byte ssPins[] = {SS_1_PIN, SS_2_PIN}; 

MFRC522 mfrc522[NR_OF_READERS];   

void setup() {
  Serial.begin(115200); 
  while (!Serial);      

  SPI.begin();          

  // Hard-reset all readers ONCE
  Serial.println(F("Waking up all RFID readers..."));
  pinMode(RST_PIN, OUTPUT);
  digitalWrite(RST_PIN, LOW);   
  delay(50);                    
  digitalWrite(RST_PIN, HIGH);  
  delay(50);                    

  // Initialize each reader
  for (uint8_t i = 0; i < NR_OF_READERS; i++) {
    mfrc522[i].PCD_Init(ssPins[i], 255); 
    
    // IMMEDIATELY turn the antenna OFF after initialization
    // This ensures no two fields are blasting at the same time
    mfrc522[i].PCD_AntennaOff();
    
    Serial.print(F("Cooking Station "));
    Serial.print(i + 1);
    Serial.println(F(" initialized and antenna muted."));
  }
  
  
  Serial.println(F("--- Game Ready! Waiting for ingredients... ---"));
}

void loop() {
  for (uint8_t i = 0; i < NR_OF_READERS; i++) {
    
    // 1. TURN ON the magnetic field for THIS station
    mfrc522[i].PCD_AntennaOn();
    
    // 2. WAIT for the field to stabilize and power the tag's microchip
    // 5 to 10 milliseconds is usually the sweet spot. 
    // If it misses reads, increase this slightly.
    delay(10); 
    
    // 3. CHECK if an ingredient is present
    if (mfrc522[i].PICC_IsNewCardPresent() && mfrc522[i].PICC_ReadCardSerial()) {

      String uidString = "";
      for (byte j = 0; j < mfrc522[i].uid.size; j++) {
        uidString += String(mfrc522[i].uid.uidByte[j] < 0x10 ? "0" : "");
        uidString += String(mfrc522[i].uid.uidByte[j], HEX);
      }
      
      uidString.toUpperCase();

      // NEW MACHINE-READABLE OUTPUT: "StationIndex,UID"
      Serial.print(i);
      Serial.print(",");
      Serial.println(uidString);

      // Put the tag back to sleep
      mfrc522[i].PICC_HaltA();
      mfrc522[i].PCD_StopCrypto1(); 
    }
    
    // 4. TURN OFF the magnetic field before moving to the next station
    mfrc522[i].PCD_AntennaOff();
  }
}