import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from prepare_friction_features import normalize_features,scenario_score
from learn_route_preferences import equivalent_distance,fit_choice


def test_direction_and_missing_features():
    raw=pd.DataFrame({'canopy_mean':[0,80,np.nan],'traffic_index_0_100':[90,10,50],'length':[100,200,100]})
    out=normalize_features(raw)
    assert out.canopy_deficit_01.tolist()[:2]==pytest.approx([1,.2])
    assert out.traffic_burden_01.tolist()==pytest.approx([.9,.1,.5])
    assert not out.environment_features_complete.iloc[2]
    assert np.isnan(scenario_score(out,1,1).iloc[2])
    assert out.distance_km.iloc[0]==pytest.approx(.1)


def test_equivalent_cost_additive_nonnegative():
    a=equivalent_distance(100,60,.2)
    b=equivalent_distance([40,60],[20,40],.2).sum()
    assert a==pytest.approx(b)
    assert a>=0
    with pytest.raises(ValueError):equivalent_distance(10,11,.2)


def test_fitted_choice_sign_and_monotonicity():
    x=np.array([[20,10],[-20,-10],[10,-5],[-10,5]],dtype=float)
    beta=fit_choice(x,np.array([0,1,0,1]))
    assert beta[0]>0 and beta[1]>=0
    assert expit(-x[0]@beta)<expit(-x[1]@beta)
