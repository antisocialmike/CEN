import pytest

from server.src.models.fiscal_ids import (
    birth_dates_match,
    curp_check_digit,
    normalize,
    nss_check_digit,
    validate_curp,
    validate_nss,
    validate_rfc,
)

CURP_ANA = "HEGG560427MVZRRL04"
RFC_ANA = "HEGG560427AB1"
NSS_VALIDO = "92988084494"


@pytest.mark.parametrize("curp", [CURP_ANA, "SABC560626MDFLRN01"])
def test_the_check_digit_of_published_curps(curp):
    assert curp_check_digit(curp[:17]) == int(curp[17])


def test_the_check_digit_of_a_published_nss():
    assert nss_check_digit(NSS_VALIDO[:10]) == 4


@pytest.mark.parametrize("raw, clean", [
    ("  hegg560427mvzrrl04 ", CURP_ANA),
    ("92-98-80-8449-4", NSS_VALIDO),
    ("", None),
    ("   ", None),
    (None, None),
])
def test_normalize_removes_spaces_and_dashes_and_uppercases(raw, clean):
    assert normalize(raw) == clean


def test_a_valid_curp_is_kept_normalized():
    assert validate_curp(" hegg560427mvzrrl04") == CURP_ANA


@pytest.mark.parametrize("curp, message", [
    ("HEGG560427MVZRRL05", "digito verificador"),
    ("HEGG560427MXXRRL04", "formato"),
    ("HEGG561327MVZRRL04", "fecha de nacimiento"),
    ("HEGG560427MVZRRL0", "formato"),
    ("BADD110313HCMLNS09", "digito verificador"),
])
def test_an_invalid_curp_says_why(curp, message):
    with pytest.raises(ValueError, match=message):
        validate_curp(curp)


def test_a_curp_of_someone_born_abroad():
    first = "PEPJ900101HNERRN0"
    curp = first + str(curp_check_digit(first))

    assert validate_curp(curp) == curp


@pytest.mark.parametrize("rfc", [RFC_ANA, "ÑUÑO800229XY9", "XAXX010101000"])
def test_valid_rfcs_of_individuals(rfc):
    assert validate_rfc(rfc) == rfc


@pytest.mark.parametrize("rfc, message", [
    ("HEG560427AB1", "13 caracteres"),
    ("GNO850101AB12", "13 caracteres"),
    ("HEGG560431AB1", "fecha de nacimiento"),
    ("HEGG560427ABZ", "13 caracteres"),
])
def test_an_invalid_rfc_says_why(rfc, message):
    with pytest.raises(ValueError, match=message):
        validate_rfc(rfc)


def test_a_valid_nss_is_kept_without_dashes():
    assert validate_nss("92-98-80-8449-4") == NSS_VALIDO


@pytest.mark.parametrize("nss, message", [
    ("92988084495", "digito verificador"),
    ("9298808449", "11 digitos"),
    ("9298808449A", "11 digitos"),
])
def test_an_invalid_nss_says_why(nss, message):
    with pytest.raises(ValueError, match=message):
        validate_nss(nss)


def test_empty_values_are_simply_missing():
    assert validate_rfc("") is None
    assert validate_curp(None) is None
    assert validate_nss("  ") is None


def test_rfc_and_curp_carry_the_same_birth_date():
    assert birth_dates_match(RFC_ANA, CURP_ANA)
    assert not birth_dates_match("HEGG560428AB1", CURP_ANA)
    assert birth_dates_match(None, CURP_ANA)
