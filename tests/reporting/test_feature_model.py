from rigor.reporting.cucumber import Cucumber
import yaml
import related
import os
import json


ROOT_DIR = os.path.join(os.path.dirname(__file__), "files")


def get_cuke(filename):
    fp = open(os.path.join(ROOT_DIR, filename))
    original = json.dumps(json.loads(fp.read()), indent=4, sort_keys=True)
    return related.from_json(original, Cucumber), original


def test_roundtrip_feature_1_json():
    cuke, original = get_cuke("feature_1.json")
    assert len(cuke.features) == 1
    assert cuke.features[0].uri == "features/one_passing_one_failing.feature"
    assert len(cuke.features[0].tags) == 1
    assert cuke.features[0].tags[0].name == "@a"

    generated = related.to_json(cuke.features)
    assert original == generated
