import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';

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
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [ocrResult, setOcrResult] = useState(null);
  const [validationData, setValidationData] = useState(null);
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
    setValidationData(null);
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
        // Successful validation
        setStatus({ type: 'success', message: data.message });
        setOcrResult(data.ocr_result);
        setValidationData(data.data);
      } else if (response.ok && !data.success) {
        // Validation failed
        setStatus({ type: 'error', message: data.message });
        setOcrResult(data.ocr_result);
        setValidationData(data.data);
      } else {
        setStatus({ type: 'error', message: data.detail || t('skan.error') });
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setStatus({ type: 'error', message: t('skan.error') });
    }
  };

  const handleReloadScan = () => {
    setFile(null);
    setStatus(null);
    setOcrResult(null);
    setValidationData(null);
    document.getElementById('file-input').value = '';
  };

  const handleGoToForm = () => {
    if (validationData && validationData.formData) {
      // Navigate to form with pre-filled data
      navigate('/form', { state: { prefilledData: validationData.formData } });
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

      {/* Validation stage information */}
      {validationData && validationData.validationStage && (
        <div className="form-card validation-section">
          <h3>
            {validationData.validationStage === 'schema' && '📋 Wstępna walidacja'}
            {validationData.validationStage === 'llm' && '🔍 Walidacja merytoryczna'}
            {validationData.validationStage === 'completed' && '✅ Walidacja zakończona'}
          </h3>

          {/* Show field errors */}
          {validationData.fieldErrors && Object.keys(validationData.fieldErrors).length > 0 && (
            <div className="validation-errors-section">
              <h4 className="validation-errors-title">Błędy walidacji:</h4>
              <ul className="validation-errors-list">
                {Object.entries(validationData.fieldErrors).map(([field, error]) => (
                  <li key={field} className="validation-error-item">
                    <strong>{field}:</strong> {error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Show schema validation errors */}
          {validationData.errors && validationData.errors.length > 0 && (
            <div className="validation-errors-section">
              <h4 className="validation-warnings-title">Niekompletne pola:</h4>
              <ul className="validation-errors-list">
                {validationData.errors.map((error, index) => (
                  <li key={index} className="validation-warning-item">
                    <strong>{error.path.join(' → ')}:</strong> {error.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* User options */}
          {validationData.userOptions && validationData.userOptions.length > 0 && (
            <div className="validation-actions">
              {validationData.userOptions.includes('reload_scan') && (
                <button onClick={handleReloadScan} className="action-button-reload">
                  🔄 Załaduj skan ponownie
                </button>
              )}
              {validationData.userOptions.includes('fill_form') && (
                <button onClick={handleGoToForm} className="action-button-form">
                  📝 Przejdź do formularza
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Show OCR result for successful validation */}
      {ocrResult && validationData && validationData.valid && (
        <div className="ocr-result">
          <h3 className="ocr-result-title">{t('skan.ocr_result')}</h3>
          <pre className="json-preview" style={{ textAlign: 'left', overflow: 'auto', maxHeight: '500px' }}>
            {typeof ocrResult === 'string' ? ocrResult : JSON.stringify(ocrResult, null, 2)}
          </pre>
          
          {validationData.pdf_filename && (
            <div style={{ padding: '1.5rem' }}>
              <a
                href={`${API_URL}/form/download/${validationData.pdf_filename}`}
                download
                className="download-button"
              >
                📥 Pobierz wygenerowany PDF
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper Component: AddressForm
const AddressForm = ({
  data,
  path,
  updateField,
  t,
  title,
  description,
  includeCountry = false,
  includePhone = false,
  includeCorrespondenceMethod = false,
  fieldDescriptions = {},
  fieldErrors = {},
  requiredFields = [],
}) => {
  if (!data) return null;

  const baseKey = Array.isArray(path) ? path.join('.') : String(path ?? '');
  return (
    <div className="address-block" style={{ marginBottom: '20px' }}>
      {title && <h3 className="section-subtitle">{title}</h3>}
      {description && <p className="field-description" style={{ marginBottom: '15px', whiteSpace: 'pre-wrap' }}>{description}</p>}
      
      {includeCorrespondenceMethod && (
        <div className="form-group">
          <label className="form-label">{t('form.fields.sposob_korespondencji')}</label>
          <select
            className={`form-input ${
              fieldErrors[`${baseKey}.sposobKorespondencji`] ? 'form-input-error' : ''
            }`}
            value={data.sposobKorespondencji || ''}
            onChange={(e) => updateField([...path, 'sposobKorespondencji'], e.target.value)}
            required={requiredFields.includes('sposobKorespondencji')}
          >
            <option value="">{t('form.options.sposob_korespondencji.placeholder')}</option>
            <option value="adres">{t('form.options.sposob_korespondencji.adres')}</option>
            <option value="poste_restante">{t('form.options.sposob_korespondencji.poste_restante')}</option>
            <option value="skrytka_pocztowa">{t('form.options.sposob_korespondencji.skrytka_pocztowa')}</option>
            <option value="przegrodka_pocztowa">{t('form.options.sposob_korespondencji.przegrodka_pocztowa')}</option>
          </select>
          {fieldErrors[`${baseKey}.sposobKorespondencji`] && (
            <span className="field-error-text">
              {t('form.validation.sposob_korespondencji')}
            </span>
          )}
          {fieldDescriptions.sposobKorespondencji && <p className="field-description">{fieldDescriptions.sposobKorespondencji}</p>}
        </div>
      )}

      <div className="form-group">
        <label className="form-label">{t('form.fields.ulica')}</label>
        <input
          type="text"
          className={`form-input ${
            fieldErrors[`${baseKey}.ulica`] ? 'form-input-error' : ''
          }`}
          value={data.ulica || ''}
          onChange={(e) => updateField([...path, 'ulica'], e.target.value)}
          required={requiredFields.includes('ulica')}
        />
        {fieldErrors[`${baseKey}.ulica`] && (
          <span className="field-error-text">{fieldErrors[`${baseKey}.ulica`]}</span>
        )}
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">{t('form.fields.numer_domu')}</label>
          <input
            type="text"
            className={`form-input ${
              fieldErrors[`${baseKey}.numerDomu`] ? 'form-input-error' : ''
            }`}
            value={data.numerDomu || ''}
            onChange={(e) => updateField([...path, 'numerDomu'], e.target.value)}
            required={requiredFields.includes('numerDomu')}
          />
          {fieldErrors[`${baseKey}.numerDomu`] && (
            <span className="field-error-text">{fieldErrors[`${baseKey}.numerDomu`]}</span>
          )}
        </div>
        <div className="form-group">
          <label className="form-label">{t('form.fields.numer_lokalu')}</label>
          <input
            type="text"
            className={`form-input ${
              fieldErrors[`${baseKey}.numerLokalu`] ? 'form-input-error' : ''
            }`}
            value={data.numerLokalu || ''}
            onChange={(e) => updateField([...path, 'numerLokalu'], e.target.value)}
          />
          {fieldErrors[`${baseKey}.numerLokalu`] && (
            <span className="field-error-text">{fieldErrors[`${baseKey}.numerLokalu`]}</span>
          )}
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">{t('form.fields.kod_pocztowy')}</label>
          <input
            type="text"
            className={`form-input ${
              fieldErrors[`${baseKey}.kodPocztowy`] ? 'form-input-error' : ''
            }`}
            value={data.kodPocztowy || ''}
            onChange={(e) => updateField([...path, 'kodPocztowy'], e.target.value)}
            required={requiredFields.includes('kodPocztowy')}
          />
          {fieldErrors[`${baseKey}.kodPocztowy`] && (
            <span className="field-error-text">{fieldErrors[`${baseKey}.kodPocztowy`]}</span>
          )}
        </div>
        <div className="form-group">
          <label className="form-label">{t('form.fields.miejscowosc')}</label>
          <input
            type="text"
            className={`form-input ${
              fieldErrors[`${baseKey}.miejscowosc`] ? 'form-input-error' : ''
            }`}
            value={data.miejscowosc || ''}
            onChange={(e) => updateField([...path, 'miejscowosc'], e.target.value)}
            required={requiredFields.includes('miejscowosc')}
          />
          {fieldErrors[`${baseKey}.miejscowosc`] && (
            <span className="field-error-text">{fieldErrors[`${baseKey}.miejscowosc`]}</span>
          )}
        </div>
      </div>

      {includeCountry && (
        <div className="form-group">
          <label className="form-label">{t('form.fields.nazwa_panstwa')}</label>
          <input
            type="text"
            className={`form-input ${
              fieldErrors[`${baseKey}.nazwaPanstwa`] ? 'form-input-error' : ''
            }`}
            value={data.nazwaPanstwa || ''}
            onChange={(e) => updateField([...path, 'nazwaPanstwa'], e.target.value)}
            required={requiredFields.includes('nazwaPanstwa')}
          />
          {fieldErrors[`${baseKey}.nazwaPanstwa`] && (
            <span className="field-error-text">{fieldErrors[`${baseKey}.nazwaPanstwa`]}</span>
          )}
          {fieldDescriptions.nazwaPanstwa && <p className="field-description">{fieldDescriptions.nazwaPanstwa}</p>}
        </div>
      )}

      {includePhone && (
        <div className="form-group">
          <label className="form-label">{t('form.fields.numer_telefonu')}</label>
          <input
            type="text"
            className={`form-input ${
              fieldErrors[`${baseKey}.numerTelefonu`] ? 'form-input-error' : ''
            }`}
            value={data.numerTelefonu || ''}
            onChange={(e) => updateField([...path, 'numerTelefonu'], e.target.value)}
          />
          {fieldErrors[`${baseKey}.numerTelefonu`] && (
            <span className="field-error-text">{fieldErrors[`${baseKey}.numerTelefonu`]}</span>
          )}
        </div>
      )}
    </div>
  );
};

// Helper Component: Field Warning
const FieldWarning = ({ message }) => {
  if (!message) return null;
  return (
    <div className="field-warning">
      <span className="field-warning-icon">⚠️</span>
      <span className="field-warning-text">{message}</span>
    </div>
  );
};

// Form Page - Zawiadomienie o wypadku (ZUS EWYP schema)
function FormPage({ t }) {
  const navigate = useNavigate();
  const location = useLocation();
  
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
      organProwadzacyPostepowanie: 'Policja Polska',
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
    sposobOdbioruOdpowiedzi: '',
    oswiadczenie: {
      dataZlozenia: '2025-12-06',
      podpis: 'Jan Kowalski',
    },
  };

  // Deep merge function to combine initialFormData with prefilledData
  const deepMerge = (target, source) => {
    const output = { ...target };
    if (isObject(target) && isObject(source)) {
      Object.keys(source).forEach(key => {
        if (isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] });
          } else {
            output[key] = deepMerge(target[key], source[key]);
          }
        } else {
          Object.assign(output, { [key]: source[key] });
        }
      });
    }
    return output;
  };

  const isObject = (item) => {
    return item && typeof item === 'object' && !Array.isArray(item);
  };

  // Check if there's prefilled data from scan
  const prefilledData = location.state?.prefilledData;
  const startingFormData = prefilledData ? deepMerge(initialFormData, prefilledData) : initialFormData;

  const [formData, setFormData] = useState(startingFormData);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [activeWitnesses, setActiveWitnesses] = useState([true, false, false]);

  // Show notification if data was prefilled from scan
  useEffect(() => {
    if (prefilledData) {
      // Scroll to top when form is loaded with prefilled data
      window.scrollTo({ top: 0, behavior: 'smooth' });
      
      setStatus({ 
        type: 'info', 
        message: '📋 Formularz został wypełniony danymi ze skanu. Sprawdź i popraw dane przed wysłaniem.' 
      });
    }
  }, [prefilledData]);

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

    // Wyczyść błąd dla danego pola po zmianie jego wartości
    const key = path.join('.');
    setFieldErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const buildPayload = (data) => {
    // Głęboka kopia, żeby nie mutować stanu Reacta
    const payload = JSON.parse(JSON.stringify(data));

    // Funkcja pomocnicza do usuwania pustych wartości
    const removeEmptyValues = (obj) => {
      if (obj === null || obj === undefined) return undefined;
      if (typeof obj !== 'object') return obj === '' ? undefined : obj;
      
      if (Array.isArray(obj)) {
        const filtered = obj.map(removeEmptyValues).filter(item => item !== undefined);
        return filtered.length > 0 ? filtered : undefined;
      }
      
      const cleaned = {};
      let hasContent = false;
      
      for (const [key, value] of Object.entries(obj)) {
        const cleanedValue = removeEmptyValues(value);
        if (cleanedValue !== undefined) {
          cleaned[key] = cleanedValue;
          hasContent = true;
        }
      }
      
      return hasContent ? cleaned : undefined;
    };

    // Jeśli osoba zawiadamiająca jest tą samą osobą co poszkodowana,
    // usuń WSZYSTKIE pola tej osoby oprócz flagi jestPoszkodowanym
    if (payload.daneOsobyKtoraZawiadamia?.jestPoszkodowanym) {
      // Zostaw tylko flagę
      payload.daneOsobyKtoraZawiadamia = {
        jestPoszkodowanym: true
      };

      delete payload.adresZamieszkaniaOsobyKtoraZawiadamia;
      delete payload.adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia;
      delete payload.adresDoKorespondencjiOsobyKtoraZawiadamia;
    }

    // Usuń puste obiekty świadków (gdy imię i nazwisko są puste)
    if (payload.daneSwiadkowWypadku && Array.isArray(payload.daneSwiadkowWypadku)) {
      payload.daneSwiadkowWypadku = payload.daneSwiadkowWypadku.filter(
        (swiadek) => swiadek.imie && swiadek.nazwisko
      );
      if (payload.daneSwiadkowWypadku.length === 0) {
        delete payload.daneSwiadkowWypadku;
      }
    }

    // Usuń dokumentTozsamosci jeśli jest pusty (gdy rodzaj i seriaINumer są puste)
    if (
      payload.daneOsobyPoszkodowanej?.dokumentTozsamosci &&
      !payload.daneOsobyPoszkodowanej.dokumentTozsamosci.rodzaj &&
      !payload.daneOsobyPoszkodowanej.dokumentTozsamosci.seriaINumer
    ) {
      delete payload.daneOsobyPoszkodowanej.dokumentTozsamosci;
    }

    // Wyczyść wszystkie puste wartości z całego payloadu
    const cleanedPayload = removeEmptyValues(payload);

    console.log('📤 Payload to send:', cleanedPayload);
    return cleanedPayload;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    setValidationErrors(null);

    try {
      const payload = buildPayload(formData);

      const response = await fetch(`${API_URL}/form`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (data.success && data.data?.valid) {
        setStatus({ type: 'success', message: data.message || t('form.success') });
        setValidationErrors(null);
        // Form is valid - navigate to success PDF page
        if (data.data.pdf_filename) {
          navigate('/success-pdf', {
            state: {
              pdfFilename: data.data.pdf_filename,
              peselFolderPath: data.data.pesel_folder_path,
              validationComment: data.data.comment
            }
          });
        }
      } else if (data.data && !data.data.valid) {
        // Form validation failed - show errors
        setValidationErrors({
          comment: data.data.comment,
          fieldErrors: data.data.fieldErrors || {},
        });
        setStatus({ type: 'error', message: data.data.comment || t('form.error') });
        // Scroll to top to show the validation comment
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        setStatus({ type: 'error', message: data.message || t('form.error') });
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

      {status && (
        <div className={`status-message status-${status.type}`}>
          {status.message}
        </div>
      )}

      <div className="form-card">
        <form onSubmit={handleSubmit}>
          {/* 1. Dane osoby poszkodowanej */}
          <h2 className="section-title">{t('form.sections.daneOsobyPoszkodowanej')}</h2>

          <div className="form-group">
            <label className="form-label">{t('form.fields.imie')}</label>
            <input
              type="text"
              className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.imie'] ? 'form-input-error' : ''}`}
              value={formData.daneOsobyPoszkodowanej.imie}
              onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'imie'], e.target.value)}
              required
            />
            {fieldErrors['daneOsobyPoszkodowanej.imie'] && (
              <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.imie']}</span>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.nazwisko')}</label>
            <input
              type="text"
              className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.nazwisko'] ? 'form-input-error' : ''}`}
              value={formData.daneOsobyPoszkodowanej.nazwisko}
              onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'nazwisko'], e.target.value)}
              required
            />
            {fieldErrors['daneOsobyPoszkodowanej.nazwisko'] && (
              <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.nazwisko']}</span>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.pesel')}</label>
            <input
              type="text"
              className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.pesel'] ? 'form-input-error' : ''}`}
              value={formData.daneOsobyPoszkodowanej.pesel}
              onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'pesel'], e.target.value)}
              required
            />
            {fieldErrors['daneOsobyPoszkodowanej.pesel'] && (
              <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.pesel']}</span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.dataUrodzenia')}</label>
              <input
                type="date"
                className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.dataUrodzenia'] ? 'form-input-error' : ''}`}
                value={formData.daneOsobyPoszkodowanej.dataUrodzenia}
                onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'dataUrodzenia'], e.target.value)}
                required
              />
              {fieldErrors['daneOsobyPoszkodowanej.dataUrodzenia'] && (
                <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.dataUrodzenia']}</span>
              )}
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.miejsceUrodzenia')}</label>
              <input
                type="text"
                className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.miejsceUrodzenia'] ? 'form-input-error' : ''}`}
                value={formData.daneOsobyPoszkodowanej.miejsceUrodzenia}
                onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'miejsceUrodzenia'], e.target.value)}
                required
              />
              {fieldErrors['daneOsobyPoszkodowanej.miejsceUrodzenia'] && (
                <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.miejsceUrodzenia']}</span>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.dokumentRodzaj')}</label>
              <input
                type="text"
                className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.dokumentTozsamosci.rodzaj'] ? 'form-input-error' : ''}`}
                value={formData.daneOsobyPoszkodowanej.dokumentTozsamosci.rodzaj}
                onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'dokumentTozsamosci', 'rodzaj'], e.target.value)}
                required
              />
              {fieldErrors['daneOsobyPoszkodowanej.dokumentTozsamosci.rodzaj'] && (
                <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.dokumentTozsamosci.rodzaj']}</span>
              )}
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.dokumentSeriaNumer')}</label>
              <input
                type="text"
                className={`form-input ${fieldErrors['daneOsobyPoszkodowanej.dokumentTozsamosci.seriaINumer'] ? 'form-input-error' : ''}`}
                value={formData.daneOsobyPoszkodowanej.dokumentTozsamosci.seriaINumer}
                onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'dokumentTozsamosci', 'seriaINumer'], e.target.value)}
                required
              />
              {fieldErrors['daneOsobyPoszkodowanej.dokumentTozsamosci.seriaINumer'] && (
                <span className="field-error-text">{fieldErrors['daneOsobyPoszkodowanej.dokumentTozsamosci.seriaINumer']}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.numer_telefonu')}</label>
            <input type="text" className="form-input" value={formData.daneOsobyPoszkodowanej.numerTelefonu} onChange={(e) => updateField(['daneOsobyPoszkodowanej', 'numerTelefonu'], e.target.value)} required />
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
            fieldErrors={fieldErrors}
            requiredFields={['ulica', 'numerDomu', 'kodPocztowy', 'miejscowosc', 'nazwaPanstwa']}
          />
          
          <AddressForm 
            data={formData.adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego} 
            path={['adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuPoszkodowanego']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresOstatniegoMiejsca')} 
            description={t('form.hints.adres_ostatniego_miejsca')}
            fieldErrors={fieldErrors}
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
            fieldErrors={fieldErrors}
            requiredFields={['sposobKorespondencji']}
          />
          
          <AddressForm 
            data={formData.adresMiejscaProwadzeniaPozarolniczejDzialalnosci} 
            path={['adresMiejscaProwadzeniaPozarolniczejDzialalnosci']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresDzialalnosci')}
            description={t('form.hints.adres_dzialalnosci')}
            includePhone={true}
            fieldErrors={fieldErrors}
          />
          
          <AddressForm 
            data={formData.adresSprawowaniaOpiekiNadDzieckiemDoLat3} 
            path={['adresSprawowaniaOpiekiNadDzieckiemDoLat3']} 
            updateField={updateField} 
            t={t} 
            title={t('form.sections.adresOpieki')} 
            description={t('form.hints.adres_opieki')}
            includePhone={true}
            fieldErrors={fieldErrors}
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
                fieldErrors={fieldErrors}
              />

              <AddressForm 
                data={formData.adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia} 
                path={['adresOstatniegoMiejscaZamieszkaniaWPolsceLubPobytuOsobyKtoraZawiadamia']} 
                updateField={updateField} 
                t={t} 
                title={t('form.sections.adresOstatniegoMiejsca')}
                description={t('form.hints.adres_ostatniego_miejsca_zawiadamiajacej')} 
                fieldErrors={fieldErrors}
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
                fieldErrors={fieldErrors}
                requiredFields={['sposobKorespondencji']}
              />
            </>
          )}


          {/* 3. Informacja o wypadku */}
          <h2 className="section-title">{t('form.sections.informacjaOWypadku')}</h2>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.data_wypadku')}</label>
              <input type="date" className={`form-input ${validationErrors?.fieldErrors?.dataWypadku ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.dataWypadku} onChange={(e) => updateField(['informacjaOWypadku', 'dataWypadku'], e.target.value)} required />
              <FieldWarning message={validationErrors?.fieldErrors?.dataWypadku} />
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.godzina_wypadku')}</label>
              <input type="time" className={`form-input ${validationErrors?.fieldErrors?.godzinaWypadku ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.godzinaWypadku} onChange={(e) => updateField(['informacjaOWypadku', 'godzinaWypadku'], e.target.value)} required />
              <FieldWarning message={validationErrors?.fieldErrors?.godzinaWypadku} />
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">{t('form.fields.planowana_godzina_rozpoczecia')}</label>
              <input type="time" className={`form-input ${validationErrors?.fieldErrors?.planowanaGodzinaRozpoczeciaPracy ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.planowanaGodzinaRozpoczeciaPracy} onChange={(e) => updateField(['informacjaOWypadku', 'planowanaGodzinaRozpoczeciaPracy'], e.target.value)} required />
              <FieldWarning message={validationErrors?.fieldErrors?.planowanaGodzinaRozpoczeciaPracy} />
            </div>
            <div className="form-group">
              <label className="form-label">{t('form.fields.planowana_godzina_zakonczenia')}</label>
              <input type="time" className={`form-input ${validationErrors?.fieldErrors?.planowanaGodzinaZakonczeniaPracy ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.planowanaGodzinaZakonczeniaPracy} onChange={(e) => updateField(['informacjaOWypadku', 'planowanaGodzinaZakonczeniaPracy'], e.target.value)} required />
              <FieldWarning message={validationErrors?.fieldErrors?.planowanaGodzinaZakonczeniaPracy} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.miejsce_wypadku')}</label>
            <input type="text" className={`form-input ${validationErrors?.fieldErrors?.miejsceWypadku ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.miejsceWypadku} onChange={(e) => updateField(['informacjaOWypadku', 'miejsceWypadku'], e.target.value)} required />
            <FieldWarning message={validationErrors?.fieldErrors?.miejsceWypadku} />
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.rodzaj_urazow')}</label>
            <input type="text" className={`form-input ${validationErrors?.fieldErrors?.rodzajDoznanychUrazow ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.rodzajDoznanychUrazow} onChange={(e) => updateField(['informacjaOWypadku', 'rodzajDoznanychUrazow'], e.target.value)} required />
            <FieldWarning message={validationErrors?.fieldErrors?.rodzajDoznanychUrazow} />
          </div>

          <div className="form-group">
            <label className="form-label">{t('form.fields.opis_okolicznosci')}</label>
            <textarea className={`form-textarea ${validationErrors?.fieldErrors?.opisOkolicznosciMiejscaIPrzyczyn ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.opisOkolicznosciMiejscaIPrzyczyn} onChange={(e) => updateField(['informacjaOWypadku', 'opisOkolicznosciMiejscaIPrzyczyn'], e.target.value)} required />
            <FieldWarning message={validationErrors?.fieldErrors?.opisOkolicznosciMiejscaIPrzyczyn} />
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
                <input type="text" className={`form-input ${validationErrors?.fieldErrors?.placowkaUdzielajacaPierwszejPomocy ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.placowkaUdzielajacaPierwszejPomocy} onChange={(e) => updateField(['informacjaOWypadku', 'placowkaUdzielajacaPierwszejPomocy'], e.target.value)} />
                <FieldWarning message={validationErrors?.fieldErrors?.placowkaUdzielajacaPierwszejPomocy} />
            </div>
          )}

          <div className="form-group">
             <label className="form-label">{t('form.fields.organ_prowadzacy')}</label>
             <input type="text" className={`form-input ${validationErrors?.fieldErrors?.organProwadzacyPostepowanie ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.organProwadzacyPostepowanie} onChange={(e) => updateField(['informacjaOWypadku', 'organProwadzacyPostepowanie'], e.target.value)} required />
             <FieldWarning message={validationErrors?.fieldErrors?.organProwadzacyPostepowanie} />
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
                  <textarea className={`form-textarea ${validationErrors?.fieldErrors?.opisStanuMaszynyIUzytkowania ? 'input-warning' : ''}`} value={formData.informacjaOWypadku.opisStanuMaszynyIUzytkowania} onChange={(e) => updateField(['informacjaOWypadku', 'opisStanuMaszynyIUzytkowania'], e.target.value)} />
                  <FieldWarning message={validationErrors?.fieldErrors?.opisStanuMaszynyIUzytkowania} />
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
          {formData.daneSwiadkowWypadku.map((swiadek, index) => {
            const witnessKey = `daneSwiadkowWypadku.${index}`;
            return (
              <div key={index} className="witness-block" style={{ border: '1px solid #eee', padding: '10px', marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <h3 className="section-subtitle" style={{ margin: 0 }}>{t('form.fields.swiadek')} {index + 1}</h3>
                  <label className="form-label" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="checkbox"
                      checked={activeWitnesses[index]}
                      onChange={(e) => {
                        const newActive = [...activeWitnesses];
                        newActive[index] = e.target.checked;
                        setActiveWitnesses(newActive);
                        
                        // Jeśli wyłączamy świadka, wyczyść jego dane
                        if (!e.target.checked) {
                          updateField(['daneSwiadkowWypadku', index, 'imie'], '');
                          updateField(['daneSwiadkowWypadku', index, 'nazwisko'], '');
                          updateField(['daneSwiadkowWypadku', index, 'adres'], {
                            ulica: '', numerDomu: '', numerLokalu: '', kodPocztowy: '', miejscowosc: '', nazwaPanstwa: ''
                          });
                        }
                      }}
                    />
                    Dodaj świadka
                  </label>
                </div>
                
                {activeWitnesses[index] && (
                  <>
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">{t('form.fields.imie')}</label>
                        <input
                          type="text"
                          className={`form-input ${
                            fieldErrors[`${witnessKey}.imie`] ? 'form-input-error' : ''
                          }`}
                          value={swiadek.imie}
                          onChange={(e) => updateField(['daneSwiadkowWypadku', index, 'imie'], e.target.value)}
                        />
                        {fieldErrors[`${witnessKey}.imie`] && (
                          <span className="field-error-text">{fieldErrors[`${witnessKey}.imie`]}</span>
                        )}
                      </div>
                      <div className="form-group">
                        <label className="form-label">{t('form.fields.nazwisko')}</label>
                        <input
                          type="text"
                          className={`form-input ${
                            fieldErrors[`${witnessKey}.nazwisko`] ? 'form-input-error' : ''
                          }`}
                          value={swiadek.nazwisko}
                          onChange={(e) => updateField(['daneSwiadkowWypadku', index, 'nazwisko'], e.target.value)}
                        />
                        {fieldErrors[`${witnessKey}.nazwisko`] && (
                          <span className="field-error-text">{fieldErrors[`${witnessKey}.nazwisko`]}</span>
                        )}
                      </div>
                    </div>
                    <AddressForm data={swiadek.adres} path={['daneSwiadkowWypadku', index, 'adres']} updateField={updateField} t={t} includeCountry={true} fieldErrors={fieldErrors} />
                  </>
                )}
              </div>
            );
          })}

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
            <select
              className={`form-input ${
                fieldErrors['sposobOdbioruOdpowiedzi'] ? 'form-input-error' : ''
              }`}
              value={formData.sposobOdbioruOdpowiedzi || ''}
              onChange={(e) => updateField(['sposobOdbioruOdpowiedzi'], e.target.value)}
              required
            >
              <option value="">{t('form.options.sposob_odbioru.placeholder')}</option>
              <option value="w_placowce_ZUS">
                {t('form.options.sposob_odbioru.w_placowce_ZUS')}
              </option>
              <option value="poczta_na_adres_wskazany_we_wniosku">
                {t('form.options.sposob_odbioru.poczta_na_adres_wskazany_we_wniosku')}
              </option>
              <option value="na_koncie_PUE_ZUS">
                {t('form.options.sposob_odbioru.na_koncie_PUE_ZUS')}
              </option>
            </select>
            {fieldErrors['sposobOdbioruOdpowiedzi'] && (
              <span className="field-error-text">
                {t('form.validation.sposob_odbioru')}
              </span>
            )}
          </div>


          <button type="submit" className="submit-button" disabled={loading}>
            {t('form.submit')}
          </button>
        </form>

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

// Success Page with PDF Preview (PDF is automatically saved to PESEL folder on backend)
function SuccessPdfPage({ t }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { pdfFilename, peselFolderPath, validationComment } = location.state || {};

  // Redirect if no PDF filename provided
  useEffect(() => {
    if (!pdfFilename) {
      navigate('/form');
    }
  }, [pdfFilename, navigate]);

  if (!pdfFilename) {
    return null;
  }

  // Use the PESEL folder path if available, otherwise fall back to filled_forms
  const pdfViewUrl = peselFolderPath 
    ? `${API_URL}/form/view/${peselFolderPath}`
    : `${API_URL}/form/view-filled/${pdfFilename}`;
  
  const pdfDownloadUrl = peselFolderPath
    ? `${API_URL}/form/download-from-pesel/${peselFolderPath}`
    : `${API_URL}/form/download/${pdfFilename}`;

  return (
    <div className="page-container success-pdf-page">
      {/* Success Header */}
      <div className="success-header">
        <div className="success-icon">✓</div>
        <h1 className="success-title">{t('success.title')}</h1>
        <p className="success-subtitle">{t('success.subtitle')}</p>
      </div>

      {/* Validation Comment */}
      {validationComment && (
        <div className="validation-success-banner">
          <span className="validation-success-icon">✓</span>
          <p className="validation-success-text">{validationComment}</p>
        </div>
      )}

      {/* PDF Preview Section */}
      <div className="pdf-preview-section">
        <h2 className="section-title">{t('success.pdf_preview')}</h2>
        <div className="pdf-embed-container">
          <iframe
            src={`${pdfViewUrl}#toolbar=0`}
            title="PDF Preview"
            className="pdf-iframe"
          />
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="success-navigation">
        <a 
          href={pdfDownloadUrl} 
          className="nav-action-button download-button"
          download={pdfFilename}
        >
          ⬇️ {t('success.download_pdf')}
        </a>
        <Link to="/form" className="nav-action-button primary-button">
          📝 {t('success.new_form')}
        </Link>
        <Link to="/" className="nav-action-button secondary-button">
          🏠 {t('success.go_home')}
        </Link>
      </div>
    </div>
  );
}

// Legacy Success Page (kept for backwards compatibility)
function SuccessPage({ t }) {
  const location = useLocation();
  const filename = location.state?.filename || 'formularz.json';

  return (
    <div className="page-container">
      <div className="success-container" style={{
        maxWidth: '600px',
        margin: '0 auto',
        textAlign: 'center',
        padding: '40px 20px'
      }}>
        <div style={{
          fontSize: '80px',
          marginBottom: '20px'
        }}>✅</div>
        
        <h1 className="page-title" style={{ color: '#22c55e', marginBottom: '20px' }}>
          Formularz wysłany pomyślnie!
        </h1>
        
        <div style={{
          background: '#f0fdf4',
          border: '2px solid #22c55e',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '30px'
        }}>
          <p style={{ 
            fontSize: '16px', 
            marginBottom: '12px',
            color: '#166534',
            fontWeight: '500'
          }}>
            Zawiadomienie o wypadku zostało zapisane
          </p>
          <p style={{
            fontSize: '14px',
            color: '#15803d',
            wordBreak: 'break-all',
            fontFamily: 'monospace',
            background: '#dcfce7',
            padding: '12px',
            borderRadius: '8px'
          }}>
            📄 {filename}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link 
            to="/form" 
            className="nav-button" 
            style={{
              display: 'inline-block',
              padding: '12px 24px',
              background: '#3b82f6',
              color: 'white',
              borderRadius: '8px',
              textDecoration: 'none',
              fontWeight: '500'
            }}
          >
            📝 Wypełnij kolejny formularz
          </Link>
          
          <Link 
            to="/" 
            className="nav-button"
            style={{
              display: 'inline-block',
              padding: '12px 24px',
              background: '#6b7280',
              color: 'white',
              borderRadius: '8px',
              textDecoration: 'none',
              fontWeight: '500'
            }}
          >
            🏠 Wróć do strony głównej
          </Link>
        </div>
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
        <Route path="/success" element={<SuccessPage t={t} />} />
        <Route path="/success-pdf" element={<SuccessPdfPage t={t} />} />
      </Routes>
    </div>
  );
}

export default App;
