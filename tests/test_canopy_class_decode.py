import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pytest
from decode_canopy_classes import decode_classes


def test_verified_class_key_conversion_and_nodata():
    raw=np.ma.array([1,10,80,90,127],mask=[False,False,False,False,True])
    out=decode_classes(raw)
    np.testing.assert_allclose(out.compressed(),[0,14.5,84.5,95])
    assert out.mask[-1]


def test_unknown_class_not_interpreted_as_percent():
    with pytest.raises(ValueError):decode_classes(np.ma.array([37]))
