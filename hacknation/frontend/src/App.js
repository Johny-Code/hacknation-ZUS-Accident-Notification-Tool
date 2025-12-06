import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';

// Import translations
import plTranslations from './i18n/pl.json';
import enTranslations from './i18n/en.json';

const translations = {
  pl: plTranslations,
  en: enTranslations
};

// Simple i18n hook
const useTranslation = (lang = 'pl') => {
  const t = (key) => {
    const keys = key.split('.');
    let value = translations[lang];
    for (const k of keys) {
      value = value?.[k];
    }
    return value || key;
  };
  return { t };
};

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Home Page
function HomePage({ t }) {
  return (
    <div className="home-container">
      <h1 className="home-title">{t('app.title')}</h1>
      <p className="home-subtitle">{t('app.subtitle')}</p>
      
      <div className="button-grid">
        <Link to="/skan" className="nav-button">
          <span className="nav-button-icon">📄</span>
          <span className="nav-button-text">{t('navigation.skan')}</span>
        </Link>
        
        <Link to="/form" className="nav-button">
          <span className="nav-button-icon">📝</span>
          <span className="nav-button-text">{t('navigation.formularz')}</span>
        </Link>
        
        <Link to="/voice" className="nav-button">
          <span className="nav-button-icon">🎤</span>
          <span className="nav-button-text">{t('navigation.voicechat')}</span>
        </Link>
      </div>
    </div>
  );
}

// Scan Page
function SkanPage({ t }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [ocrResult, setOcrResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const getUserId = () => {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
      userId = crypto.randomUUID();
      localStorage.setItem('user_id', userId);
    }
    return userId;
  };

  const handleFile = async (selectedFile) => {
    if (selectedFile.type !== 'application/pdf') {
      setStatus({ type: 'error', message: t('skan.pdf_only') });
      return;
    }

    setFile(selectedFile);
    setOcrResult(null);
    setStatus({ type: 'loading', message: t('skan.uploading') });

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_URL}/skan`, {
        method: 'POST',
        headers: {
          'X-User-ID': getUserId(),
        },
        body: formData,
      });
      const data = await response.json();
      
      if (response.ok && data.success) {
        setStatus({ type: 'success', message: t('skan.success') });
        setOcrResult(data.ocr_result);
      } else {
        setStatus({ type: 'error', message: data.detail || t('skan.error') });
      }
    } catch (error) {
      setStatus({ type: 'error', message: t('skan.error') });
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFile(droppedFile);
  };

  return (
    <div className="page-container">
      <h1 className="page-title">{t('skan.title')}</h1>
      <p className="page-description">{t('skan.description')}</p>

      <div
        className={`dropzone ${dragOver ? 'dragover' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <div className="dropzone-icon">📄</div>
        <p className="dropzone-text">{t('skan.dropzone')}</p>
        <p className="dropzone-hint">{t('skan.pdf_hint')}</p>
        <input
          id="file-input"
          type="file"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          accept="application/pdf,.pdf"
        />
      </div>

      {file && (
        <div className="file-info">
          <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
        </div>
      )}

      {status && (
        <div className={`status-message status-${status.type === 'loading' ? 'success' : status.type}`}>
          {status.message}
        </div>
      )}

      {ocrResult && (
        <div className="ocr-result">
          <h3 className="ocr-result-title">{t('skan.ocr_result')}</h3>
          <div className="ocr-result-content">{ocrResult}</div>
        </div>
      )}
    </div>
  );
}

// Helper Component: AddressForm
const AddressForm = ({ data, path, updateField, t, title, description, includeCountry = false, includePhone = false, includeCorrespondenceMethod = false, fieldDescriptions = {} }) => {
  if (!data) return null;
  
  return (
    <div className="address-block" style={{ marginBottom: '20px' }}>
      {title && <h3 className="section-subtitle">{title}</h3>}
      {description && <p className="field-description" style={{ marginBottom: '15px', whiteSpace: 'pre-wrap' }}>{description}</p>}
      
      {includeCorrespondenceMethod && (
        <div className="form-group">
          <label className="form-label">{t('form.fields.sposob_korespondencji')}</label>
          <select
            className="form-input"
            value={data.sposobKorespondencji || ''}
            onChange={(e) => updateField([...path, 'sposobKorespondencji'], e.target.value)}
          >
            <option value="">{t('form.options.sposob_korespondencji.placeholder')}</option>
            <option value="adres">{t('form.options.sposob_korespondencji.adres')}</option>
            <option value="poste restante">{t('form.options.sposob_korespondencji.poste_restante')}</option>
            <option value="skrytka pocztowa">{t('form.options.sposob_korespondencji.skrytka_pocztowa')}</option>
            <option value="przegródka pocztowa">{t('form.options.sposob_korespondencji.przegrodka_pocztowa')}</option>
          </select>
          {fieldDescriptions.sposobKorespondencji && <p className="field-description">{fieldDescriptions.sposobKorespondencji}</p>}
        </div>
      )}

      <div className="form-group">
        <label className="form-label">{t('form.fields.ulica')}</label>
        <input
          type="text" className="form-input" value={data.ulica || ''}
          onChange={(e) => updateField([...path, 'ulica'], e.target.value)}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">{t('form.fields.numer_domu')}</label>
          <input
            type="text" className="form-input" value={data.numerDomu || ''}
            onChange={(e) => updateField([...path, 'numerDomu'], e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">{t('form.fields.numer_lokalu')}</label>
          <input
            type="text" className="form-input" value={data.numerLokalu || ''}
            onChange={(e) => updateField([...path, 'numerLokalu'], e.target.value)}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">{t('form.fields.kod_pocztowy')}</label>
          <input
            type="text" className="form-input" value={data.kodPocztowy || ''}
            onChange={(e) => updateField([...path, 'kodPocztowy'], e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">{t('form.fields.miejscowosc')}</label>
          <input
            type="text" className="form-input" value={data.miejscowosc || ''}
            onChange={(e) => updateField([...path, 'miejscowosc'], e.target.value)}
          />
        </div>
      </div>

      {includeCountry && (
        <div className="form-group">
          <label className="form-label">{t('form.fields.nazwa_panstwa')}</label>
          <input
            type="text" className="form-input" value={data.nazwaPanstwa || ''}
            onChange={(e) => updateField([...path, 'nazwaPanstwa'], e.target.value)}
          />
          {fieldDescriptions.nazwaPanstwa && <p className="field-description">{fieldDescriptions.nazwaPanstwa}</p>}
        </div>
      )}

      {includePhone && (
        <div className="form-group">
          <label className="form-label">{t('form.fields.numer_telefonu')}</label>
          <input
            type="text" className="form-input" value={data.numerTelefonu || ''}
            onChange={(e) => updateField([...path, 'numerTelefonu'], e.target.value)}
          />
        </div>
      )}
    </div>
  );
};

// Form Page - Zawiadomienie o wypadku (ZUS EWYP schema)
function FormPage({ t }) {
  const initialFormData = {
    daneOsobyPoszkodowanej: {
      pesel: '90010112345',
      dokumentTozsamosci: { rodzaj: 'Dowód osobisty', seriaINumer: 'ABC123456' },
      imie: 'Jan',
      nazwisko: 'Kowalski',
      dataUrodzenia: '1990-01-01',
      miejsceUrodzenia: 'Warszawa',
      numerTelefonu: '500123456',
    },
    adresZamieszkaniaOsobyPoszkodowanej: {
      ulica: 'ul. Marszałkowska', numerDomu: '10', numerLokalu: '5', kodPocztowy: '00-001', miejscowosc: 'Warszawa', nazwaPanstwa: 'Polska',
    },
    adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego: {
      ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '',
    },
    adresDoKorespondencjiOsobyPoszkodowanej: {
      sposobKorespondencji: 'adres', ulica: 'ul. Marszałkowska', numerDomu: '10', numerLokalu: '5', kodPocztowy: '00-001', miejscowosc: 'Warszawa', nazwaPanstwa: 'Polska',
    },
    adresMiejscaProwadzeniaPozarolniczejDzialalnosci: {
      ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', numerTelefonu: '',
    },
    adresSprawowaniaOpiekiNadDzieckiemDoLat3: {
      ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', numerTelefonu: '',
    },
    daneOsobyKtoraZawiadamia: {
      jestPoszkodowanym: true,
      pesel: '',
      dokumentTozsamosci: { rodzaj: '', seriaINumer: '' },
      imie: '',
      nazwisko: '',
      dataUrodzenia: '',
      numerTelefonu: '',
    },
    adresZamieszkaniaOsobyKtoraZawiadamia: {
      ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', nazwaPanstwa: '',
    },
    adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia: {
      ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '',
    },
    adresDoKorespondencjiOsobyKtoraZawiadamia: {
      sposobKorespondencji: '', ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', nazwaPanstwa: '',
    },
    informacjaOWypadku: {
      dataWypadku: '2025-12-05',
      godzinaWypadku: '09:30',
      miejsceWypadku: 'Magazyn firmy XYZ, ul. Przemysłowa 15, Warszawa',
      planowanaGodzinaRozpoczeciaPracy: '08:00',
      planowanaGodzinaZakonczeniaPracy: '16:00',
      rodzajDoznanychUrazow: 'Złamanie przedramienia prawego',
      opisOkolicznosciMiejscaIPrzyczyn: 'Podczas przenoszenia ciężkich paczek w magazynie, pracownik potknął się o niezabezpieczoną paletę i upadł na betonową posadzkę. W wyniku upadku doznał złamania przedramienia prawego. Miejsce wypadku było słabo oświetlone, a paleta nie była oznaczona.',
      pierwszaPomocUdzielona: true,
      placowkaUdzielajacaPierwszejPomocy: 'Szpitalny Oddział Ratunkowy, Szpital Bielański, Warszawa',
      organProwadzacyPostepowanie: '',
      wypadekPodczasObslugiMaszynLubUrzadzen: false,
      opisStanuMaszynyIUzytkowania: '',
      maszynaPosiadaAtestLubDeklaracjeZgodnosci: false,
      maszynaWpisanaDoEwidencjiSrodkowTrwalych: false,
    },
    daneSwiadkowWypadku: [
      { imie: 'Anna', nazwisko: 'Nowak', adres: { ulica: 'ul. Kwiatowa', numerDomu: '5', numerLokalu: '', kodPocztowy: '00-002', miejscowosc: 'Warszawa', nazwaPanstwa: 'Polska' } },
      { imie: '', nazwisko: '', adres: { ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', nazwaPanstwa: '' } },
      { imie: '', nazwisko: '', adres: { ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', nazwaPanstwa: '' } },
    ],
    zalaczniki: {
      kartaInformacyjnaLubZaswiadczeniePierwszejPomocy: true,
      postanowienieProkuratury: false,
      dokumentyDotyczaceZgonu: false,
      dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby: false,
      inneDokumentyOpis: '',
    },
    dokumentyDoDostarczeniaPozniej: {
      dataDo: '',
      listaDokumentow: ['', '', '', '', '', '', '', ''],
    },
    sposobOdbioruOdpowiedzi: 'poczta tradycyjna',
    oswiadczenie: {
      dataZlozenia: '2025-12-06',
      podpis: 'Jan Kowalski',
    },
  };

  const [formData, setFormData] = useState(initialFormData);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const updateField = (path, value) => {
    setFormData((prev) => {
      const updated = { ...prev };
      let current = updated;
      for (let i = 0; i < path.length - 1; i += 1) {
        const key = path[i];
        current[key] = Array.isArray(current[key]) ? [...current[key]] : { ...(current[key] || {}) };
        current = current[key];
      }
      current[path[path.length - 1]] = value;
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    try {
      const response = await fetch(`${API_URL}/form`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();

      if (data.success) {
        setStatus({ type: 'success', message: t('form.success') });
        setFormData(initialFormData);
      } else {
        setStatus({ type: 'error', message: t('form.error') });
      }
    } catch (error) {
      setStatus({ type: 'error', message: t('form.error') });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <h1 className="page-title">{t('form.title')}</h1>

      <div className="form-card">
        <form onSubmit={handleSubmit}>
          {/* 1. Dane osoby poszkodowanej */}
          <h2 className="section-title">{t('form.sections.daneOsobyPoszkodowanej')}</h2>

          <div className="form-group">
            <label className="form-label">{t('form.fields.imie')}</label>
            <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.imie} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'imie'], e.target.value)} required />
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.nazwisko')}</label>
            <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.nazwisko} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'nazwisko'], e.target.value)} required />
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.pesel')}</label>
            <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.pesel} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'pesel'], e.target.value)} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.dataUrodzenia')}</label>
              <input type="date" className="form-input" value={formData.daneOsobyPoszkodowanej.dataUrodzenia} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'dataUrodzenia'], e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.miejsceUrodzenia')}</label>
              <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.miejsceUrodzenia} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'miejsceUrodzenia'], e.target.value)} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.dokumentRodzaj')}</label>
              <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.dokumentTozsamosci.rodzaj} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'dokumentTozsamosci', 'rodzaj'], e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.dokumentSeriaNumer')}</label>
              <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.dokumentTozsamosci.seriaINumer} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'dokumentTozsamosci', 'seriaINumer'], e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.numer_telefonu')}</label>
            <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.numerTelefonu} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'numerTelefonu'], e.target.value)} />
            <p className="field-description" style={{ whiteSpace: 'pre-wrap' }}>{t('form.hints.numer_telefonu')}</p>
          </div>

          {/* Adresy osoby poszkodowanej */}
          <AddressForm 
            data={formData.adresZamieszkaniaOsobyPoszkodowanej} 
            path={['adresZamieszkaniaOsobyPoszkodowanej']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresZamieszkaniaOsobyPoszkodowanej')} 
            includeCountry={true}
            fieldDescriptions={{ nazwaPanstwa: t('form.hints.nazwa_panstwa') }}
          />
          
          <AddressForm 
            data={formData.adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego} 
            path={['adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresOstatniegoMiejsca')} 
            description={t('form.hints.adres_ostatniego_miejsca')}
          />
          
          <AddressForm 
            data={formData.adresDoKorespondencjiOsobyPoszkodowanej} 
            path={['adresDoKorespondencjiOsobyPoszkodowanej']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresDoKorespondencji')} 
            description={t('form.hints.adres_do_korespondencji')}
            includeCountry={true} 
            includeCorrespondenceMethod={true}
            fieldDescriptions={{ nazwaPanstwa: t('form.hints.nazwa_panstwa_twoj') }}
          />
          
          <AddressForm 
            data={formData.adresMiejscaProwadzeniaPozarolniczejDzialalnosci} 
            path={['adresMiejscaProwadzeniaPozarolniczejDzialalnosci']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresDzialalnosci')}
            description={t('form.hints.adres_dzialalnosci')}
            includePhone={true} 
          />
          
          <AddressForm 
            data={formData.adresSprawowaniaOpiekiNadDzieckiemDoLat3} 
            path={['adresSprawowaniaOpiekiNadDzieckiemDoLat3']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresOpieki')} 
            description={t('form.hints.adres_opieki')}
            includePhone={true} 
          />


          {/* 2. Dane osoby zawiadamiającej */}
          <h2 className="section-title">{t('form.sections.daneOsobyZawiadamiajacej')}</h2>
          <p className="field-description">{t('form.hints.dane_osoby_zawiadamiajacej')}</p>
          
          <div className="form-group">
            <label className="form-label">
              <input type="checkbox" checked={formData.daneOsobyKtoraZawiadamia.jestPoszkodowanym} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'jestPoszkodowanym'], e.target.checked)} />
              {' '}{t('form.fields.jest_poszkodowanym')}
            </label>
          </div>

          {!formData.daneOsobyKtoraZawiadamia.jestPoszkodowanym && (
            <>
               <div className="form-group">
                <label className="form-label">{t('form.fields.imie')}</label>
                <input type="text" className="form-input" value={formData.daneOsobyKtoraZawiadamia.imie} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'imie'], e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">{t('form.fields.nazwisko')}</label>
                <input type="text" className="form-input" value={formData.daneOsobyKtoraZawiadamia.nazwisko} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'nazwisko'], e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">{t('form.fields.pesel')}</label>
                <input type="text" className="form-input" value={formData.daneOsobyKtoraZawiadamia.pesel} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'pesel'], e.target.value)} />
              </div>
               <div className="form-group">
                  <label className="form-label">{t('form.fields.dataUrodzenia')}</label>
                  <input type="date" className="form-input" value={formData.daneOsobyKtoraZawiadamia.dataUrodzenia} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'dataUrodzenia'], e.target.value)} />
               </div>
                <div className="form-row">
                <div className="form-group">
                  <label className="form-label">{t('form.fields.dokumentRodzaj')}</label>
                  <input type="text" className="form-input" value={formData.daneOsobyKtoraZawiadamia.dokumentTozsamosci.rodzaj} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'dokumentTozsamosci', 'rodzaj'], e.target.value)} />
                  <p className="field-description">{t('form.hints.dokument_tozsamosci_brak_pesel')}</p>
                </div>
                <div className="form-group">
                  <label className="form-label">{t('form.fields.dokumentSeriaNumer')}</label>
                  <input type="text" className="form-input" value={formData.daneOsobyKtoraZawiadamia.dokumentTozsamosci.seriaINumer} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'dokumentTozsamosci', 'seriaINumer'], e.target.value)} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">{t('form.fields.numer_telefonu')}</label>
                <input type="text" className="form-input" value={formData.daneOsobyKtoraZawiadamia.numerTelefonu} onChange={(e) => updateField(['daneOsobyKtoraZawiadamia', 'numerTelefonu'], e.target.value)} />
                <p className="field-description" style={{ whiteSpace: 'pre-wrap' }}>{t('form.hints.numer_telefonu')}</p>
              </div>

              <AddressForm 
                data={formData.adresZamieszkaniaOsobyKtoraZawiadamia} 
                path={['adresZamieszkaniaOsobyKtoraZawiadamia']} 
                updateField={updateField} 
                t={t} 
                title={t('form.sections.adresZamieszkaniaOsobyZawiadamiajacej')} 
                description={t('form.hints.adres_zamieszkania_zawiadamiajacej')}
                includeCountry={true} 
                fieldDescriptions={{ nazwaPanstwa: t('form.hints.nazwa_panstwa_twoj') }}
              />

              <AddressForm 
                data={formData.adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia} 
                path={['adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia']} 
                updateField={updateField} 
                t={t} 
                title={t('form.sections.adresOstatniegoMiejsca')}
                description={t('form.hints.adres_ostatniego_miejsca_zawiadamiajacej')} 
              />

              <AddressForm 
                data={formData.adresDoKorespondencjiOsobyKtoraZawiadamia} 
                path={['adresDoKorespondencjiOsobyKtoraZawiadamia']} 
                updateField={updateField} 
                t={t} 
                title={t('form.sections.adresDoKorespondencji')} 
                description={t('form.hints.adres_do_korespondencji_zawiadamiajacej')}
                includeCountry={true} 
                includeCorrespondenceMethod={true} 
                fieldDescriptions={{ nazwaPanstwa: t('form.hints.nazwa_panstwa_twoj') }}
              />
            </>
          )}


          {/* 3. Informacja o wypadku */}
          <h2 className="section-title">{t('form.sections.informacjaOWypadku')}</h2>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.data_wypadku')}</label>
              <input type="date" className="form-input" value={formData.informacjaOWypadku.dataWypadku} onChange={(e) => updateField(['informacjaOWypadku', 'dataWypadku'], e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.godzina_wypadku')}</label>
              <input type="time" className="form-input" value={formData.informacjaOWypadku.godzinaWypadku} onChange={(e) => updateField(['informacjaOWypadku', 'godzinaWypadku'], e.target.value)} />
            </div>
          </div>
          
           <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.planowana_godzina_rozpoczecia')}</label>
              <input type="time" className="form-input" value={formData.informacjaOWypadku.planowanaGodzinaRozpoczeciaPracy} onChange={(e) => updateField(['informacjaOWypadku', 'planowanaGodzinaRozpoczeciaPracy'], e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.planowana_godzina_zakonczenia')}</label>
              <input type="time" className="form-input" value={formData.informacjaOWypadku.planowanaGodzinaZakonczeniaPracy} onChange={(e) => updateField(['informacjaOWypadku', 'planowanaGodzinaZakonczeniaPracy'], e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.miejsce_wypadku')}</label>
            <input type="text" className="form-input" value={formData.informacjaOWypadku.miejsceWypadku} onChange={(e) => updateField(['informacjaOWypadku', 'miejsceWypadku'], e.target.value)} required />
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.rodzaj_urazow')}</label>
            <input type="text" className="form-input" value={formData.informacjaOWypadku.rodzajDoznanychUrazow} onChange={(e) => updateField(['informacjaOWypadku', 'rodzajDoznanychUrazow'], e.target.value)} />
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.opis_okolicznosci')}</label>
            <textarea className="form-textarea" value={formData.informacjaOWypadku.opisOkolicznosciMiejscaIPrzyczyn} onChange={(e) => updateField(['informacjaOWypadku', 'opisOkolicznosciMiejscaIPrzyczyn'], e.target.value)} required />
          </div>

          <div className="form-group">
             <label className="form-label">
              <input type="checkbox" checked={formData.informacjaOWypadku.pierwszaPomocUdzielona} onChange={(e) => updateField(['informacjaOWypadku', 'pierwszaPomocUdzielona'], e.target.checked)} />
              {' '}{t('form.fields.pierwsza_pomoc')}
            </label>
          </div>
          
          {formData.informacjaOWypadku.pierwszaPomocUdzielona && (
             <div className="form-group">
                <label className="form-label">{t('form.fields.placowka_medyczna')}</label>
                <input type="text" className="form-input" value={formData.informacjaOWypadku.placowkaUdzielajacaPierwszejPomocy} onChange={(e) => updateField(['informacjaOWypadku', 'placowkaUdzielajacaPierwszejPomocy'], e.target.value)} />
            </div>
          )}

          <div className="form-group">
             <label className="form-label">{t('form.fields.organ_prowadzacy')}</label>
             <input type="text" className="form-input" value={formData.informacjaOWypadku.organProwadzacyPostepowanie} onChange={(e) => updateField(['informacjaOWypadku', 'organProwadzacyPostepowanie'], e.target.value)} />
          </div>

          <div className="form-group">
             <label className="form-label">
              <input type="checkbox" checked={formData.informacjaOWypadku.wypadekPodczasObslugiMaszynLubUrzadzen} onChange={(e) => updateField(['informacjaOWypadku', 'wypadekPodczasObslugiMaszynLubUrzadzen'], e.target.checked)} />
              {' '}{t('form.fields.maszyny_urzadzenia')}
            </label>
          </div>
          
          {formData.informacjaOWypadku.wypadekPodczasObslugiMaszynLubUrzadzen && (
            <>
               <div className="form-group">
                  <label className="form-label">{t('form.fields.opis_stanu_maszyny')}</label>
                  <textarea className="form-textarea" value={formData.informacjaOWypadku.opisStanuMaszynyIUzytkowania} onChange={(e) => updateField(['informacjaOWypadku', 'opisStanuMaszynyIUzytkowania'], e.target.value)} />
               </div>
               <div className="form-group">
                 <label className="form-label">
                  <input type="checkbox" checked={formData.informacjaOWypadku.maszynaPosiadaAtestLubDeklaracjeZgodnosci} onChange={(e) => updateField(['informacjaOWypadku', 'maszynaPosiadaAtestLubDeklaracjeZgodnosci'], e.target.checked)} />
                  {' '}{t('form.fields.atest')}
                </label>
               </div>
                <div className="form-group">
                 <label className="form-label">
                  <input type="checkbox" checked={formData.informacjaOWypadku.maszynaWpisanaDoEwidencjiSrodkowTrwalych} onChange={(e) => updateField(['informacjaOWypadku', 'maszynaWpisanaDoEwidencjiSrodkowTrwalych'], e.target.checked)} />
                  {' '}{t('form.fields.ewidencja')}
                </label>
               </div>
            </>
          )}

          {/* 4. Świadkowie wypadku */}
          <h2 className="section-title">{t('form.sections.daneSwiadkow')}</h2>
          {formData.daneSwiadkowWypadku.map((swiadek, index) => (
            <div key={index} className="witness-block" style={{ border: '1px solid #eee', padding: '10px', marginBottom: '15px' }}>
              <h3 className="section-subtitle">{t('form.fields.swiadek')} {index + 1}</h3>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">{t('form.fields.imie')}</label>
                  <input type="text" className="form-input" value={swiadek.imie} onChange={(e) => updateField(['daneSwiadkowWypadku', index, 'imie'], e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('form.fields.nazwisko')}</label>
                  <input type="text" className="form-input" value={swiadek.nazwisko} onChange={(e) => updateField(['daneSwiadkowWypadku', index, 'nazwisko'], e.target.value)} />
                </div>
              </div>
              <AddressForm data={swiadek.adres} path={['daneSwiadkowWypadku', index, 'adres']} updateField={updateField} t={t} includeCountry={true} />
            </div>
          ))}

          {/* 5. Załączniki */}
          <h2 className="section-title">{t('form.sections.zalaczniki')}</h2>
          <div className="form-group">
            <label className="form-label">
              <input type="checkbox" checked={formData.zalaczniki.kartaInformacyjnaLubZaswiadczeniePierwszejPomocy} onChange={(e) => updateField(['zalaczniki', 'kartaInformacyjnaLubZaswiadczeniePierwszejPomocy'], e.target.checked)} />
              {' '}{t('form.fields.karta_informacyjna')}
            </label>
          </div>
           <div className="form-group">
            <label className="form-label">
              <input type="checkbox" checked={formData.zalaczniki.postanowienieProkuratury} onChange={(e) => updateField(['zalaczniki', 'postanowienieProkuratury'], e.target.checked)} />
              {' '}{t('form.fields.postanowienie_prokuratury')}
            </label>
          </div>
           <div className="form-group">
            <label className="form-label">
              <input type="checkbox" checked={formData.zalaczniki.dokumentyDotyczaceZgonu} onChange={(e) => updateField(['zalaczniki', 'dokumentyDotyczaceZgonu'], e.target.checked)} />
              {' '}{t('form.fields.dokumenty_zgon')}
            </label>
          </div>
           <div className="form-group">
            <label className="form-label">
              <input type="checkbox" checked={formData.zalaczniki.dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby} onChange={(e) => updateField(['zalaczniki', 'dokumentyPotwierdzajacePrawoDoKartyWypadkuDlaInnejOsoby'], e.target.checked)} />
              {' '}{t('form.fields.dokumenty_karta_wypadku')}
            </label>
          </div>
           <div className="form-group">
              <label className="form-label">{t('form.fields.inne_dokumenty')}</label>
              <textarea className="form-textarea" value={formData.zalaczniki.inneDokumentyOpis} onChange={(e) => updateField(['zalaczniki', 'inneDokumentyOpis'], e.target.value)} />
           </div>

          {/* 6. Dokumenty później */}
          <h2 className="section-title">{t('form.sections.dokumentyPozniej')}</h2>
           <div className="form-group">
              <label className="form-label">{t('form.fields.data_do')}</label>
              <input type="date" className="form-input" value={formData.dokumentyDoDostarczeniaPozniej.dataDo} onChange={(e) => updateField(['dokumentyDoDostarczeniaPozniej', 'dataDo'], e.target.value)} />
           </div>
           <label className="form-label">{t('form.fields.lista_dokumentow')}</label>
           {formData.dokumentyDoDostarczeniaPozniej.listaDokumentow.map((doc, i) => (
              <div key={i} className="form-group">
                 <input type="text" className="form-input" placeholder={`${i + 1}.`} value={doc} onChange={(e) => updateField(['dokumentyDoDostarczeniaPozniej', 'listaDokumentow', i], e.target.value)} />
              </div>
           ))}

          {/* 7. Oświadczenie */}
          <h2 className="section-title">{t('form.sections.oswiadczenie')}</h2>
          <div className="form-row">
             <div className="form-group">
                <label className="form-label">{t('form.fields.data_zlozenia')}</label>
                <input type="date" className="form-input" value={formData.oswiadczenie.dataZlozenia} onChange={(e) => updateField(['oswiadczenie', 'dataZlozenia'], e.target.value)} />
             </div>
             <div className="form-group">
                <label className="form-label">{t('form.fields.podpis')}</label>
                <input type="text" className="form-input" value={formData.oswiadczenie.podpis} onChange={(e) => updateField(['oswiadczenie', 'podpis'], e.target.value)} />
             </div>
          </div>

           {/* 8. Sposób odbioru */}
           <div className="form-group">
              <label className="form-label">{t('form.sections.sposobOdbioru')}</label>
              <input type="text" className="form-input" value={formData.sposobOdbioruOdpowiedzi} onChange={(e) => updateField(['sposobOdbioruOdpowiedzi'], e.target.value)} />
           </div>


          <button type="submit" className="submit-button" disabled={loading}>
            {t('form.submit')}
          </button>
        </form>

        {status && (
          <div className={`status-message status-${status.type}`}>
            {status.message}
          </div>
        )}

        <div className="json-preview-card">
          <h3 className="section-subtitle">{t('form.preview_title')}</h3>
          <pre className="json-preview">
            {JSON.stringify(formData, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

// Voice Page (Placeholder)
function VoicePage({ t }) {
  return (
    <div className="page-container">
      <h1 className="page-title">{t('voice.title')}</h1>

      <div className="placeholder-card">
        <div className="placeholder-icon">🎤</div>
        <p className="placeholder-text">{t('voice.description')}</p>
      </div>
    </div>
  );
}

// Main App
function App() {
  const [lang] = useState('pl'); // Default to Polish
  const { t } = useTranslation(lang);
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className="app-container">
      {!isHome && (
        <nav className="nav-bar">
          <Link to="/" className="nav-home">← {t('navigation.home')}</Link>
        </nav>
      )}

      <Routes>
        <Route path="/" element={<HomePage t={t} />} />
        <Route path="/skan" element={<SkanPage t={t} />} />
        <Route path="/form" element={<FormPage t={t} />} />
        <Route path="/voice" element={<VoicePage t={t} />} />
      </Routes>
    </div>
  );
}

export default App;
