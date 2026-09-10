import pytest
import pandas as pd
from tools.evaluate_detectors import custom_agg_ddos, custom_agg_recon, EvaluatorMetrics

def test_custom_agg_ddos():
    df = pd.DataFrame({
        'Label': ['BENIGN', 'DDoS', 'BENIGN', 'Other'],
        'Total Fwd Packets': [10, 20, 5, 2],
        'Total Backward Packets': [10, 20, 5, 2],
        'Source IP': ['1.1.1.1', '2.2.2.2', '1.1.1.1', '3.3.3.3']
    })

    result = custom_agg_ddos(df)

    assert result['Total_Flows'] == 4
    assert result['Attack_Flows'] == 1
    assert result['Benign_Flows'] == 2
    assert result['Other_Flows'] == 1
    assert result['Total_Packets'] == 74

def test_custom_agg_recon():
    df = pd.DataFrame({
        'Label': ['BENIGN', 'PortScan', 'PortScan', 'BENIGN'],
        'Destination Port': [80, 443, 8080, 80],
        'Destination IP': ['1.1.1.1', '2.2.2.2', '1.1.1.1', '3.3.3.3']
    })

    result = custom_agg_recon(df)

    assert result['Total_Flows'] == 4
    assert result['Attack_Flows'] == 2
    assert result['Benign_Flows'] == 2
    assert result['Other_Flows'] == 0
    assert result['Unique_Ports'] == 3

def test_evaluator_metrics():
    metrics = EvaluatorMetrics()

    # Truth=1, Pred=1 -> TP
    metrics.add_result(1, 1)
    # Truth=0, Pred=1 -> FP
    metrics.add_result(0, 1)
    # Truth=0, Pred=0 -> TN
    metrics.add_result(0, 0)
    # Truth=1, Pred=0 -> FN
    metrics.add_result(1, 0)

    assert metrics.tp == 1
    assert metrics.fp == 1
    assert metrics.tn == 1
    assert metrics.fn == 1
