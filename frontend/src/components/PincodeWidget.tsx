import React, { useEffect, useState } from 'react';
import { MapPin, Building2, Trees, Phone, Globe, CheckCircle2, Search, X } from 'lucide-react';
import { PincodeInfo } from '../types';

interface PincodeWidgetProps {
  currentPincode: PincodeInfo | null;
  onSelectPincode: (info: PincodeInfo) => void;
  onClose?: () => void;
}

const POPULAR_PRESETS = [
  { code: '560001', label: 'Bengaluru Urban (BBMP)', type: 'Urban' },
  { code: '110001', label: 'New Delhi (NDMC)', type: 'Urban' },
  { code: '400001', label: 'Mumbai Fort (BMC)', type: 'Urban' },
  { code: '413512', label: 'Latur Rural (Gram Panchayat)', type: 'Rural' },
  { code: '273001', label: 'Gorakhpur (Nagar Nigam & Block)', type: 'Semi-Urban' },
];

interface LocationSuggestion {
  name: string;
  area: string;
  pincode: string;
  is_village?: boolean;
}

export const PincodeWidget: React.FC<PincodeWidgetProps> = ({
  currentPincode,
  onSelectPincode,
  onClose,
}) => {
  const [inputCode, setInputCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [searchingLocations, setSearchingLocations] = useState(false);

  useEffect(() => {
    const query = inputCode.trim();
    if (query.length < 2 || /^\d+$/.test(query)) {
      setSuggestions([]);
      return;
    }

    const timer = window.setTimeout(async () => {
      setSearchingLocations(true);
      try {
        const response = await fetch(`/api/locations/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      } catch {
        setSuggestions([]);
      } finally {
        setSearchingLocations(false);
      }
    }, 250);
    return () => window.clearTimeout(timer);
  }, [inputCode]);

  const fetchPincode = async (code: string, locality = '', isVillage = false) => {
    if (!code || code.trim().length !== 6 || isNaN(Number(code))) {
      setError('Please choose a location from the matching suggestions.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      if (locality) params.set('locality', locality);
      if (isVillage) params.set('is_village', 'true');
      const res = await fetch(`/api/pincode/${code.trim()}${params.size ? `?${params}` : ''}`);
      if (!res.ok) throw new Error('PIN Code lookup failed');
      const data: PincodeInfo = await res.json();
      onSelectPincode(data);
      if (onClose) onClose();
    } catch (err) {
      setError('Unable to fetch location details. Using smart fallback.');
      // Fallback object
      onSelectPincode({
        pincode: code,
        state: 'Karnataka / State Jurisdiction',
        district: 'District Office',
        taluka: 'Taluka Jurisdiction',
        type: isVillage || Number(code.slice(-2)) > 50 ? 'Rural' : 'Urban',
        body: isVillage ? `${locality} Gram Panchayat / District Zilla Parishad` : (Number(code.slice(-2)) > 50 ? 'Gram Panchayat & BDO' : 'Municipal Corporation PWD'),
        ward: isVillage ? `${locality} Village Gram Sabha` : 'Ward 10',
        portal: isVillage ? 'e-GramSwaraj Portal & CPGRAMS' : 'State Public Grievance Portal & CPGRAMS',
        helpline: isVillage ? '1800-180-2000 (Panchayati Raj)' : '1916 / 1800-180-2000'
      });
      if (onClose) onClose();
    } finally {
      setLoading(false);
    }
  };

  const handlePresetClick = (code: string) => {
    setInputCode(code);
    fetchPincode(code);
  };

  const selectLocation = (location: LocationSuggestion) => {
    setInputCode(location.pincode);
    setSuggestions([]);
    fetchPincode(location.pincode, location.name, Boolean(location.is_village));
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
      {/* Background Accent Blur */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-full bg-slate-800/80 hover:bg-slate-700"
        >
          <X className="w-5 h-5" />
        </button>
      )}

      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <MapPin className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white font-['Outfit']">Location & Jurisdiction Detector</h3>
          <p className="text-xs text-slate-400">
            Search your locality, landmark, town or village to adapt recommendations for <span className="text-emerald-400 font-semibold">Urban Municipalities</span> vs <span className="text-amber-400 font-semibold">Rural Gram Panchayats</span>.
          </p>
        </div>
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError('Choose one of the matching locations below to set your jurisdiction.');
        }}
        className="flex gap-2 mb-4"
      >
        <div className="relative flex-1">
          <input
            type="text"
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value)}
            placeholder="Search a locality, village, landmark or city"
            className="w-full px-4 py-3 rounded-2xl glass-input text-white text-sm font-semibold tracking-wider placeholder:text-slate-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-semibold text-sm transition-all flex items-center gap-2 shadow-lg shadow-blue-600/30 disabled:opacity-50"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          <span>Search</span>
        </button>
      </form>

      {(suggestions.length > 0 || searchingLocations) && (
        <div className="mb-4 rounded-2xl border border-slate-700 bg-slate-950/80 overflow-hidden">
          <p className="px-4 py-2 text-xs font-semibold text-slate-400 border-b border-slate-800">
            {searchingLocations ? 'Searching matching places…' : `${suggestions.length} matching location${suggestions.length === 1 ? '' : 's'} — choose one`}
          </p>
          {suggestions.map((location) => (
            <button
              key={`${location.name}-${location.pincode}`}
              type="button"
              onClick={() => selectLocation(location)}
              className="w-full px-4 py-3 text-left hover:bg-slate-800/80 transition-colors flex items-center gap-3"
            >
              <MapPin className="w-4 h-4 text-blue-400 shrink-0" />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold text-white">{location.name}</span>
                <span className="block text-xs text-slate-400 truncate">{location.area}{location.is_village ? ' · Village Gram Panchayat' : ''}</span>
              </span>
            </button>
          ))}
        </div>
      )}

      {error && <p className="text-xs text-rose-400 mb-3">{error}</p>}

      {/* Preset Chips */}
      <div className="mb-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Popular Locations:</p>
        <div className="flex flex-wrap gap-2">
          {POPULAR_PRESETS.map((p) => (
            <button
              key={p.code}
              onClick={() => handlePresetClick(p.code)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all flex items-center gap-1.5 ${
                currentPincode?.pincode === p.code
                  ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                  : 'bg-slate-800/60 border-slate-700/60 text-slate-300 hover:border-slate-500'
              }`}
            >
              <span className="text-slate-300">{p.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Active PIN Information Card */}
      {currentPincode && (
        <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2">
              <span className="text-lg font-extrabold text-white">{currentPincode.district}</span>
              <span className="text-xs text-slate-400">({currentPincode.state})</span>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-extrabold flex items-center gap-1 border ${
                currentPincode.type === 'Rural'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              }`}
            >
              {currentPincode.type === 'Rural' ? (
                <Trees className="w-3.5 h-3.5 inline" />
              ) : (
                <Building2 className="w-3.5 h-3.5 inline" />
              )}
              {currentPincode.type} Jurisdiction
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="flex items-start space-x-2 text-slate-300">
              <Building2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-slate-500 block font-medium">Designated Local Body:</span>
                <strong className="text-white font-semibold">{currentPincode.body}</strong>
              </div>
            </div>

            <div className="flex items-start space-x-2 text-slate-300">
              <Globe className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-slate-500 block font-medium">Official Grievance Channel:</span>
                <strong className="text-blue-300 font-semibold">{currentPincode.portal}</strong>
              </div>
            </div>

            <div className="flex items-start space-x-2 text-slate-300 md:col-span-2">
              <Phone className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-slate-500 block font-medium">Emergency Helplines:</span>
                <strong className="text-emerald-300 font-semibold">{currentPincode.helpline}</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
