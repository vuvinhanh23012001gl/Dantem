from app.config import PatchCoreTrainConfig
def test_patchcore_train_config_defaults():
    config = PatchCoreTrainConfig()
    assert config.img_size > 0
    assert config.batch_size > 0
    assert config.n_list > 0
    assert config.n_probe > 0
