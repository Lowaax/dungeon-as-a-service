import random

import pytest

from app.domain.heros import Guerrier, Heros, Mage, Voleur


def test_heros_est_abstrait():
    with pytest.raises(TypeError):
        Heros(6, 2, 2)


def test_exemples_du_sujet():
    assert Guerrier(6, 2, 2).calculer_degats() == (14, False)
    assert Guerrier(6, 2, 2).pv_max == 32
    assert Mage(2, 2, 6).calculer_degats() == (19, False)
    assert Mage(2, 2, 6).pv_max == 24
    assert Voleur(2, 6, 2).pv_max == 24


def test_armure_du_guerrier():
    assert Guerrier(6, 2, 2).subir_degats(3) == 2
    assert Guerrier(6, 2, 2).subir_degats(1) == 1  # minimum 1
    assert Mage(2, 2, 6).subir_degats(3) == 3


def test_critique_du_voleur():
    class FakeRng(random.Random):
        def __init__(self, value):
            super().__init__()
            self.value = value

        def random(self):
            return self.value

    assert Voleur(2, 6, 2, rng=FakeRng(0.1)).calculer_degats() == (28, True)
    assert Voleur(2, 6, 2, rng=FakeRng(0.9)).calculer_degats() == (14, False)
