from pydantic import BaseModel
from typing import Optional, List


class AccidentFormData(BaseModel):
    """Legacy simple PoC form – kept for backwards compatibility if needed."""
    reporter_name: str
    incident_date: str
    location: str
    description: str
    witnesses: Optional[str] = None


# === ZUS EWYP – models aligned with the JSON schema and frontend ===


class DokumentTozsamosci(BaseModel):
    rodzaj: Optional[str] = None
    seriaINumer: Optional[str] = None


class AdresZPanstwem(BaseModel):
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None
    nazwaPanstwa: Optional[str] = None


class AdresKrajowy(BaseModel):
    """Adres bez pola 'nazwaPanstwa' – używany dla adresów w Polsce."""
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None


class AdresZTelefonem(AdresKrajowy):
    numerTelefonu: Optional[str] = None


class DaneOsobyPoszkodowanej(BaseModel):
    pesel: Optional[str] = None
    dokumentTozsamosci: Optional[DokumentTozsamosci] = None
    imie: str
    nazwisko: str
    dataUrodzenia: Optional[str] = None  # ISO date string
    miejsceUrodzenia: Optional[str] = None
    numerTelefonu: Optional[str] = None


class DaneOsobyKtoraZawiadamia(BaseModel):
    jestPoszkodowanym: Optional[bool] = None
    pesel: Optional[str] = None
    dokumentTozsamosci: Optional[DokumentTozsamosci] = None
    imie: Optional[str] = None
    nazwisko: Optional[str] = None
    dataUrodzenia: Optional[str] = None
    numerTelefonu: Optional[str] = None


class AdresDoKorespondencji(BaseModel):
    sposobKorespondencji: Optional[str] = None
    ulica: Optional[str] = None
    numerDomu: Optional[str] = None
    numerLokalu: Optional[str] = None
    kodPocztowy: Optional[str] = None
    miejscowosc: Optional[str] = None
    nazwaPanstwa: Optional[str] = None


class InformacjaOWypadku(BaseModel):
    dataWypadku: str
    godzinaWypadku: Optional[str] = None
    miejsceWypadku: str
    planowanaGodzinaRozpoczeciaPracy: Optional[str] = None
    planowanaGodzinaZakonczeniaPracy: Optional[str] = None
    rodzajDoznanychUrazow: Optional[str] = None
    opisOkolicznosciMiejscaIPrzyczyn: str
    pierwszaPomocUdzielona: Optional[bool] = None
    placowkaUdzielajacaPierwszejPomocy: Optional[str] = None
    organProwadzacyPostepowanie: Optional[str] = None
    wypadekPodczasObslugiMaszynLubUrzadzen: Optional[bool] = None
    opisStanuMaszynyIUzytkowania: Optional[str] = None
    maszynaPosiadaAtestLubDeklaracjeZgodnosci: Optional[bool] = None
    maszynaWpisanaDoEwidencjiSrodkowTrwalych: Optional[bool] = None


class AdresSwiadka(AdresZPanstwem):
    """Adres świadka – schema allows 'nazwaPanstwa'."""


class DaneSwiadka(BaseModel):
    imie: Optional[str] = None
    nazwisko: Optional[str] = None
    adres: Optional[AdresSwiadka] = None


class Zalaczniki(BaseModel):
    kartaInformacyjnaLubZaswiadczeniePierwszejPomocy: Optional[bool] = None
    postanowienieProkuratury: Optional[bool] = None
    dokumentyDotyczaceZgonu: Optional[bool] = None
    dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby: Optional[bool] = None
    inneDokumentyOpis: Optional[str] = None


class DokumentyDoDostarczeniaPozniej(BaseModel):
    dataDo: Optional[str] = None
    listaDokumentow: Optional[List[str]] = None


class Oswiadczenie(BaseModel):
    dataZlozenia: Optional[str] = None
    podpis: Optional[str] = None


class ZawiadomienieOWypadku(BaseModel):
    """Główny model formularza ZUS EWYP, zgodny z podanym JSON Schema."""

    daneOsobyPoszkodowanej: DaneOsobyPoszkodowanej
    adresZamieszkaniaOsobyPoszkodowanej: AdresZPanstwem
    adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego: Optional[AdresKrajowy] = None
    adresDoKorespondencjiOsobyPoszkodowanej: Optional[AdresDoKorespondencji] = None
    adresMiejscaProwadzeniaPozarolniczejDzialalnosci: Optional[AdresZTelefonem] = None
    adresSprawowaniaOpiekiNadDzieckiemDoLat3: Optional[AdresZTelefonem] = None

    daneOsobyKtoraZawiadamia: Optional[DaneOsobyKtoraZawiadamia] = None
    adresZamieszkaniaOsobyKtoraZawiadamia: Optional[AdresZPanstwem] = None
    adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia: Optional[AdresKrajowy] = None
    adresDoKorespondencjiOsobyKtoraZawiadamia: Optional[AdresDoKorespondencji] = None

    informacjaOWypadku: InformacjaOWypadku

    daneSwiadkowWypadku: Optional[List[DaneSwiadka]] = None  # maxItems=3 implied by frontend

    zalaczniki: Optional[Zalaczniki] = None
    dokumentyDoDostarczeniaPozniej: Optional[DokumentyDoDostarczeniaPozniej] = None

    sposobOdbioruOdpowiedzi: Optional[str] = None
    oswiadczenie: Optional[Oswiadczenie] = None


class FormResponse(BaseModel):
    """Standard response for form submissions."""
    success: bool
    message: str
    data: Optional[dict] = None


class ScanResponse(BaseModel):
    """Response for scan/OCR operations."""
    success: bool
    message: str
    ocr_result: Optional[str] = None
    data: Optional[dict] = None


# === Wyjaśnienia poszkodowanego – model formularza ===


class WyjasnieniaPoszkodowanego(BaseModel):
    """
    Model formularza 'Wyjaśnienia poszkodowanego'.
    Używany przy zgłaszaniu wyjaśnień dotyczących wypadku.
    
    All fields are Optional to allow partial data from OCR/scan.
    Required field validation is handled by JSON schema in the endpoint.
    """
    # Dane osobowe
    imieNazwisko: Optional[str] = None
    dataUrodzenia: Optional[str] = None  # format: YYYY-MM-DD
    miejsceUrodzenia: Optional[str] = None
    adresZamieszkania: Optional[str] = None
    zatrudnienie: Optional[str] = None
    dokumentTozsamosci: Optional[str] = None

    # Informacje o wypadku
    dataWypadku: Optional[str] = None  # format: YYYY-MM-DD
    miejsceWypadku: Optional[str] = None
    godzinaWypadku: Optional[str] = None
    planowanaGodzinaRozpoczeciaPracy: Optional[str] = None
    planowanaGodzinaZakonczeniaPracy: Optional[str] = None

    # Okoliczności wypadku
    rodzajCzynnosciPrzedWypadkiem: Optional[str] = None
    opisOkolicznosciWypadku: Optional[str] = None

    # Maszyny i urządzenia
    czyWypadekPodczasObslugiMaszyn: Optional[bool] = None
    nazwaTypUrzadzenia: Optional[str] = None
    dataProdukcjiUrzadzenia: Optional[str] = None
    czyUrzadzenieSprawneIUzytkowanePrawidlowo: Optional[str] = None

    # Zabezpieczenia
    czyBylyZabezpieczenia: Optional[bool] = None
    rodzajZabezpieczen: Optional[str] = None
    czySrodkiWlasciweISprawne: Optional[bool] = None

    # Warunki pracy
    czyAsekuracja: Optional[bool] = None
    czyObowiazekPracyPrzezDwieOsoby: Optional[bool] = None

    # BHP
    czyPrzestrzeganoZasadBHP: Optional[bool] = None
    czyPosiadamPrzygotowanieZawodowe: Optional[bool] = None
    czyOdbylemSzkolenieBHP: Optional[bool] = None
    czyPosiadamOceneRyzykaZawodowego: Optional[bool] = None
    stosowaneSrodkiZmniejszajaceRyzyko: Optional[str] = None

    # Stan trzeźwości
    czyWStanieNietrzezwosci: Optional[bool] = None
    stanTrzezwosciBadany: Optional[str] = None  # enum: badany_przez_policje, badany_podczas_pierwszej_pomocy, nie_badany

    # Organy prowadzące czynności
    czyOrganyPodejmowalyCzynnosci: Optional[bool] = None
    organyISzczegoly: Optional[str] = None

    # Pierwsza pomoc i hospitalizacja
    pierwszaPomocData: Optional[str] = None
    nazwaPlacowkiZdrowia: Optional[str] = None
    okresIMiejsceHospitalizacji: Optional[str] = None
    rozpoznanyUraz: Optional[str] = None
    niezdolnoscDoPracy: Optional[str] = None

    # Zwolnienie lekarskie
    czyNaZwolnieniuWLacuWypadku: Optional[bool] = None

    # Podpisy
    dataPodpisania: Optional[str] = None  # format: YYYY-MM-DD
    podpisPoszkodowanego: Optional[str] = None
    podpisPrzyjmujacego: Optional[str] = None

