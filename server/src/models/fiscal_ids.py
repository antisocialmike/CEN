import re
from datetime import date
from typing import Optional

CURP_DICTIONARY = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
CURP_STATES = frozenset(
    "AS BC BS CC CL CM CS CH DF DG GT GR HG JC MC MN MS NT NL OC PL QT QR "
    "SP SL SR TC TS TL VZ YN ZS NE".split()
)

RFC_PATTERN = re.compile(r"^[A-ZÑ&]{4}([0-9]{6})[A-Z0-9]{2}[0-9A]$")
CURP_PATTERN = re.compile(
    r"^[A-Z][AEIOUX][A-Z]{2}([0-9]{6})[HMX]([A-Z]{2})"
    r"[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9][0-9]$"
)
NSS_PATTERN = re.compile(r"^[0-9]{11}$")


def normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"[\s-]", "", value).upper()
    return cleaned or None


def _is_birth_date(yymmdd: str) -> bool:
    year, month, day = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:])
    for century in (1900, 2000):
        try:
            date(century + year, month, day)
            return True
        except ValueError:
            continue
    return False


def curp_check_digit(first_seventeen: str) -> int:
    total = sum(
        CURP_DICTIONARY.index(character) * (18 - position)
        for position, character in enumerate(first_seventeen)
    )
    return (10 - total % 10) % 10


def nss_check_digit(first_ten: str) -> int:
    total = 0
    for position, digit in enumerate(first_ten):
        product = int(digit) * (2 if position % 2 else 1)
        total += product // 10 + product % 10
    return (10 - total % 10) % 10


def validate_rfc(value: Optional[str]) -> Optional[str]:
    rfc = normalize(value)
    if rfc is None:
        return None
    match = RFC_PATTERN.match(rfc)
    if match is None:
        raise ValueError(
            "El RFC de una persona física lleva 13 caracteres: cuatro letras, "
            "la fecha de nacimiento y la homoclave"
        )
    if not _is_birth_date(match.group(1)):
        raise ValueError("La fecha de nacimiento del RFC no existe")
    return rfc


def validate_curp(value: Optional[str]) -> Optional[str]:
    curp = normalize(value)
    if curp is None:
        return None
    match = CURP_PATTERN.match(curp)
    if match is None or match.group(2) not in CURP_STATES:
        raise ValueError("La CURP no tiene el formato de 18 caracteres de RENAPO")
    if not _is_birth_date(match.group(1)):
        raise ValueError("La fecha de nacimiento de la CURP no existe")
    if curp_check_digit(curp[:17]) != int(curp[17]):
        raise ValueError("El dígito verificador de la CURP no corresponde")
    return curp


def validate_nss(value: Optional[str]) -> Optional[str]:
    nss = normalize(value)
    if nss is None:
        return None
    if NSS_PATTERN.match(nss) is None:
        raise ValueError("El NSS lleva 11 dígitos")
    if nss_check_digit(nss[:10]) != int(nss[10]):
        raise ValueError("El dígito verificador del NSS no corresponde")
    return nss


def birth_dates_match(rfc: Optional[str], curp: Optional[str]) -> bool:
    if rfc is None or curp is None:
        return True
    return rfc[4:10] == curp[4:10]
