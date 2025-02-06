import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from decoder import DatagramDecoder

@pytest.fixture
def decoder():
    return DatagramDecoder()

@pytest.mark.parametrize("message, expected_outputs", [
    # Test case 1: Invalid message with incorrect payload
    (
        [0xAA, 0xFF, 0x00, 0x00, 0x00, 0x01, 0x06, 0xAA, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBB], 
        []
    ),
    # Test case 2: Valid message with specific payload
    (
        [0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xBB], 
        [{'fault': 257, 'fault_val': 257, 'aux_batt_v': 257, 'afe_status': 1}]
    ),
    # Test case 3: Invalid message with wrong end byte
    (
        [0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xAA], 
        []
    ),
    # Test case 4: Valid message with zeroed payload
    (
        [0xAA, 0x00, 0x00, 0x00, 0x01, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xBB], 
        [{'fault': 0, 'fault_val': 0, 'aux_batt_v': 0, 'afe_status': 0}]
    ),
])
def test_decoder(decoder, message, expected_outputs):
    outputs = []
    
    for byte in message:
        data = decoder.read_test(byte)
        if data:
            outputs.append(data)
    
    assert outputs == expected_outputs, f"Test failed for message: {message}\nExpected: {expected_outputs}\nGot: {outputs}"