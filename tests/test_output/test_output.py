import os
import sys

from data import input_data

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.utils import UnderEST


def test_UnderEST():
    result = UnderEST.getUnderstimated(input_data)
    assert len(result) == 1
    assert result[0]["stock_id"] == "6285"
    assert result[0]["SDESTPER"][4][2] == 11.651803743333465

    msg = UnderEST.NoticeUndersEST(result)
    assert "6285啟碁: 11.7" in msg
