void setup() {

  Serial.begin(115200);


}

void loop() {
    byte battery_status[] = {0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBB};

    for (int i = 0; i < sizeof(battery_status); i++) {
        Serial.write(battery_status[i]);  
        delay(0); 
    }
    delay(10);  // <-- Add delay between messages

    byte afe1_status[] = {0xAA, 0x00, 0x00, 0x07, 0x82, 0x08, 0x32, 0x19, 0xDC, 0x00, 0xF4, 0x01, 0xB0, 0x04, 0xBB};

    for (int i = 0; i < sizeof(afe1_status); i++) {
        Serial.write(afe1_status[i]);  // Send the byte at index 'i'
        delay(0); 
    }
    delay(10);


    byte motor_velocity[] = {0xAA, 0x00, 0x00, 0x00, 0x24, 0x05, 0x01, 0x02, 0x03, 0x04, 0x05, 0xBB};

    for (int i = 0; i < sizeof(motor_velocity); i++) {
        Serial.write(motor_velocity[i]);  
        delay(0); 
    }
    delay(10);  // <-- Add delay between messages

    byte pd_status[] = {0xAA, 0x00, 0x00, 0x00, 0x02, 0x06, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0xBB};

    for (int i = 0; i < sizeof(pd_status); i++) {
        Serial.write(pd_status[i]);  
        delay(0); 
    }
    delay(10);  // <-- Add delay between messages

    byte battery_vt[] = {0xAA, 0x00, 0x00, 0x00, 0x0F, 0x08, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0xBB};

    for (int i = 0; i < sizeof(battery_vt); i++) {
        Serial.write(battery_vt[i]);  
        delay(0); 
    }
    delay(10);  // <-- Add delay between messages
}