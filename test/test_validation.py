# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 12:10:33 2025

Test cases for BEAT visualization tool

@author: Bence Many
"""

import pytest
from BEAT import file_handler as fh

@pytest.fixture
def load_data():
    test_file = r"test\ValidationFile\SOF-0002687.txt"
    file_path = fh.open_datafile(test_file)
    df_num, df_text = fh.read_preproc_data(file_path)
    return df_num, df_text

def test_file_open(load_data):
    # Load data
    df_num, df_text = load_data
    
    # Check if file is present
    assert df_num is not None, "FAIL: Dataframe could not be loaded"
    assert df_text is not None, "FAIL: Dataframe could not be loaded"
    print("PASS: Dataframe loaded successfully")
        
# def test_no_preproc(load_data):
#     df_num, df_text = load_data
#     assert df_num is not None
#     assert False
    
# def test_old_file():
#     test_file = r"test\ValidationFile\SOF-0002687.txt"
#     file_path = fh.open_datafile(test_file)
#     df_num, df_text = fh.read_preproc_data(file_path)
#     assert df_num is not None
#     assert False
    
def test_motor_pos_inflate(load_data):
    
    # Load data
    df_num, df_text = load_data
    time = 60

    # Confirm "Inflate" is activated (within t+1 sec)
    inf_values = df_num.loc[time:time+1, "Inflate"].values
    assert any(x > 0 for x in inf_values), f"FAIL: Inflate is not activated at {time} sec"
    print(f"PASS: Inflate is activated at {time} sec")
    
    # Confirm "MotorPos" reaches expected value (within t+60 sec)
    motor_values = df_num.loc[time:time+60, "MotorPos"].values
    expected_value = 131
    assert expected_value in motor_values, f"FAIL: MotorPos has not reached {expected_value}"
    print(f"PASS: MotorPos has reached {expected_value}")

def test_motor_pos_deflate(load_data):
    
    # Load data
    df_num, df_text = load_data
    time = 150

    # Confirm "Deflate" is activated (within t+1 sec)
    def_values = df_num.loc[time:time+1, "Deflate"].values
    assert any(x > 0 for x in def_values), f"FAIL: Deflate is not activated at {time} sec"
    print(f"PASS: Deflate is activated at {time} sec")
    
    # Confirm "MotorPos" reaches expected value (within t+60 sec)
    motor_values = df_num.loc[time:time+60, "MotorPos"].values
    expected_value = 0
    assert expected_value in motor_values, f"FAIL: MotorPos has not reached {expected_value}"
    print(f"PASS: MotorPos has reached {expected_value}")
    
def test_hall(load_data):
    # Load data
    df_num, df_text = load_data
    time_start = 80
    time_end = 160

    # Extract Hall sensor signals during inflation. Remove offset
    hall_a_inf = df_num.loc[time_start:time_start+30, "PW HallA"].values + 22
    hall_b_inf = df_num.loc[time_start:time_start+30, "PW HallB"].values + 23
    
    # Confirm Hall B is leading Hall A during inflation
    for i in range(1, len(hall_b_inf)):
        if hall_b_inf[i] < hall_b_inf[i-1]:     # Hall B activation point
            assert hall_a_inf[i] == 0, "FAIL: Hall B is not leading Hall A during inflation."
    print("PASS: Hall B is leading Hall A during inflation.")
            
    # Extract Hall sensor signals during deflation. Remove offset
    hall_a_defl = df_num.loc[time_end-10:time_end, "PW HallA"].values + 22
    hall_b_defl = df_num.loc[time_end-10:time_end, "PW HallB"].values + 23
    
    # Confirm Hall A is leading Hall B during inflation
    for i in range(1, len(hall_a_defl)):
        if hall_a_defl[i] < hall_a_defl[i-1]:     # Hall A activation point
            assert hall_b_defl[i] == 0, "FAIL: Hall A is not leading Hall B during deflation."
    print("PASS: Hall A is leading Hall B during deflation.")
    
def test_state(load_data):
    # Load data
    df_num, df_text = load_data
    time_start = 30
    time_end = 188

    # Confirm "State" follows the expected sequence
    expected_values = [10, 30, 40, 50, 80, 90, 100, 110, 30]
    state_values = df_num.loc[time_start:time_end, "State"].values
    
    # Iterate through the values and keep only the first occurrence of consecutive duplicates
    state_sequence = []
    for i in range(len(state_values)):
        if i == 0 or state_values[i] != state_values[i - 1]:
            state_sequence.append(state_values[i])
    
    assert state_sequence == expected_values, f"FAIL: State sequence is incorrect: {state_sequence}"
    print(f"PASS: State sequence is correct:  {state_sequence}")
    
def test_pressure(load_data):
    # Load data
    df_num, df_text = load_data
    time = 384

    # Confirm "Tip, fast" pressure matches the expected value
    variable = "Tip, fast"
    expected_tip_fast = 200
    tip_fast = df_num.loc[time, variable]
    assert expected_tip_fast == tip_fast, f"FAIL: {variable} is incorrect: {tip_fast}"
    print(f"PASS: {variable} is correct: {tip_fast}")
    
    # Confirm "Tip, slow" pressure matches the expected value
    variable = "Tip, slow"
    expected_tip_slow = 200
    tip_slow = df_num.loc[time, variable]
    assert expected_tip_slow == tip_slow, f"FAIL: {variable} is incorrect: {tip_slow}"
    print(f"PASS: {variable} is correct: {tip_slow}")
    
    # Confirm "Balloon, fast" pressure matches the expected value
    variable = "Balloon, fast"
    expected_balloon_fast = 199
    balloon_fast = df_num.loc[time, variable]
    assert expected_balloon_fast == balloon_fast, f"FAIL: {variable} is incorrect: {balloon_fast}"
    print(f"PASS: {variable} is correct: {balloon_fast}")
    
    # Confirm "Balloon, slow" pressure matches the expected value
    variable = "Balloon, slow"
    expected_balloon_slow = 199
    balloon_slow = df_num.loc[time, variable]
    assert expected_balloon_slow == balloon_slow, f"FAIL: {variable} is incorrect: {balloon_slow}"
    print(f"PASS: {variable} is correct: {balloon_slow}")

def test_syst_dias_stat(load_data):
    # Load data
    df_num, df_text = load_data
    time = 384

    # Confirm "Systolic" pressure matches the expected value
    variable = "Systolic"
    expected_systolic = 200
    systolic = df_num.loc[time, variable]
    assert expected_systolic == systolic, f"FAIL: {variable} is incorrect: {systolic}"
    print(f"PASS: {variable} is correct: {systolic}")
    
    # Confirm "Diastolic" pressure matches the expected value
    variable = "Diastolic"
    expected_diastolic = 200
    diastolic = df_num.loc[time, variable]
    assert expected_diastolic == diastolic, f"FAIL: {variable} is incorrect: {diastolic}"
    print(f"PASS: {variable} is correct: {diastolic}")
    
def test_syst_dias_dyn(load_data):
    # Load data
    df_num, df_text = load_data
    time = 457.5

    # Confirm "Systolic" pressure matches the expected value
    variable = "Systolic"
    expected_systolic = 66
    systolic = df_num.loc[time, variable]
    assert expected_systolic == systolic, f"FAIL: {variable} pressure is incorrect: {systolic}"
    print(f"PASS: {variable} pressure is correct: {systolic}")
    
    # Confirm "Diastolic" pressure matches the expected value
    variable = "Diastolic"
    expected_diastolic = 0
    diastolic = df_num.loc[time, "Diastolic"]
    assert expected_diastolic == diastolic, f"FAIL: {variable} pressure is incorrect: {diastolic}"
    print(f"PASS: {variable} pressure is correct: {diastolic}")
    
def test_mean_art_press(load_data):
    # Load data
    df_num, df_text = load_data
    time = 457.5

    # Confirm "MAP" pressure matches the expected value
    variable = "MAP"
    expected_value = [21, 22]
    value = df_num.loc[time, variable]
    assert value in expected_value, f"FAIL: {variable} is incorrect: {value}"
    print(f"PASS: {variable} is correct: {value}")
    
def test_pulse_bpm(load_data):
    # Load data
    df_num, df_text = load_data
    time = 457.5

    # Confirm "Pulse BPM" matches the expected value
    variable = "Pulse BPM"
    expected_value = 87
    value = df_num.loc[time, variable]
    assert value == expected_value, f"FAIL: {variable} is incorrect: {value}"
    print(f"PASS: {variable} is correct: {value}")

def test_battery(load_data):
    # Load data
    df_num, df_text = load_data
    time = 457.5

    # Confirm "BattSlow" matches the expected value
    variable = "BattSlow"
    expected_value = 86
    value = df_num.loc[time, variable]
    assert value == expected_value, f"FAIL: {variable} is incorrect: {value}"
    print(f"PASS: {variable} is correct: {value}")
    
    # Confirm "BattFast" matches the expected value
    variable = "BattFast"
    value = df_num.loc[time, variable]
    assert value == expected_value, f"FAIL: {variable} is incorrect: {value}"
    print(f"PASS: {variable} is correct: {value}")
    
def test_battery_percent(load_data):
    # Load data
    df_num, df_text = load_data
    time = 30

    # Confirm "BattPercent" matches the expected value
    variable = "BattPercent"
    expected_value = 100
    value = df_num.loc[time, variable]
    assert value == expected_value, f"FAIL: {variable} is incorrect: {value}"
    print(f"PASS: {variable} is correct: {value}")
    
def test_alarm(load_data):
    # Load data
    df_num, df_text = load_data
    time = 541

    # Confirm "Alarm" is activated (within t+1 sec)
    variable = "Alarm"
    values = df_text.loc[time:time+1, variable].values
    expected_value = "0x204"
    assert any(expected_value in str(value) for value in values), f"FAIL: {variable} is not activated at {time} sec"
    print(f"PASS: {variable} is activated at {time} sec")
    
def test_time_scale(load_data):
    # Load data
    df_num, df_text = load_data

    # Confirm the time scale matches the expected value
    expected_value = (600, 601)
    value = df_num.index.max()
    assert (value < max(expected_value)) and (value > min(expected_value)), f"FAIL: Time scale is incorrect: max = {value}"
    print(f"PASS: Time scale is correct: max = {value}")
    
    # Confirm the time scale matches the expected value
    value = df_text.index.max()
    assert (value < max(expected_value)) and (value > min(expected_value)), f"FAIL: Time scale is incorrect: max = {value}"
    print(f"PASS: Time scale is correct: max = {value}")

