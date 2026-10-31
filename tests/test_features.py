import pandas as pd

from ml.train import build_features, build_surge_labels


def toy_sales(n=40):
    dates = pd.date_range("2019-01-01", periods=n, freq="D")
    return pd.DataFrame({"datum": dates.strftime("%m/%d/%Y"), "N02BE": range(n)})


def test_lag_features_only_use_past_values():
    X, y = build_features(toy_sales(), "N02BE")
    # With sales = day index, lag_k must equal today's value minus k
    assert (X["lag_1"] == y - 1).all()
    assert (X["lag_7"] == y - 7).all()
    # The rolling mean is shifted, so it never includes today's value
    assert (X["rolling_7_mean"] == y - 4).all()


def test_surge_labels_mark_top_quartile():
    labels = build_surge_labels(pd.Series(range(100)))
    assert labels.sum() == 25
