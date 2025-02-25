import pytest
from telemetry.decoder import DatagramDecoder

@pytest.fixture
def decoder():
    return DatagramDecoder(test=True)

@pytest.mark.parametrize("message, expected_outputs", [
    # Test case 1: Invalid message with incorrect payload
    (
        [0xAA, 0xFF, 0x00, 0x00, 0x00, 0x01, 0x06, 0xAA, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBB], 
        []
    ),
    # Test case 2: Valid message with specific payload
    (
        [0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBB], 
        [{'BMS_FAULT_OVERVOLTAGE': 1, 'BMS_FAULT_UNBALANCE': 0, 'BMS_FAULT_OVERTEMP_AMBIENT': 0, 'BMS_FAULT_COMMS_LOSS_AFE': 0,
        'BMS_FAULT_COMMS_LOSS_CURR_SENSE': 0, 'BMS_FAULT_OVERTEMP_CELL': 0, 'BMS_FAULT_OVERCURRENT': 0, 'BMS_FAULT_UNDERVOLTAGE': 0,
        'BMS_FAULT_KILLSWITCH': 1, 'BMS_FAULT_RELAY_CLOSE_FAILED': 0, 'BMS_FAULT_DISCONNECTED': 0, 'aux_batt_v': 257, 'afe_status': 1}]
    ),
    # Test case 3: Invalid message with wrong end byte
    (
        [0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xAA], 
        []
    ),
    # Test case 4: Valid message with zeroed payload
    (
        [0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xBB], 
        [{'BMS_FAULT_OVERVOLTAGE': 0, 'BMS_FAULT_UNBALANCE': 0, 'BMS_FAULT_OVERTEMP_AMBIENT': 0, 'BMS_FAULT_COMMS_LOSS_AFE': 0, 
        'BMS_FAULT_COMMS_LOSS_CURR_SENSE': 0, 'BMS_FAULT_OVERTEMP_CELL': 0, 'BMS_FAULT_OVERCURRENT': 0, 'BMS_FAULT_UNDERVOLTAGE': 0, 
        'BMS_FAULT_KILLSWITCH': 0, 'BMS_FAULT_RELAY_CLOSE_FAILED': 0, 'BMS_FAULT_DISCONNECTED': 0, 'aux_batt_v': 0, 'afe_status': 0}]
    ),
])
def test_decoder(decoder, message, expected_outputs):
    outputs = []
    
    for byte in message:
        data = decoder.read_test(byte)
        if data:
            outputs.append(data)
    
    assert outputs == expected_outputs, f"Test failed for message: {message}\nExpected: {expected_outputs}\nGot: {outputs}"