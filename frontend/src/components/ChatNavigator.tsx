import React, { useEffect, useState } from 'react';
import { Sparkles, Send, MapPin, CheckCircle2, AlertTriangle, FileText, Mail, Clock, ArrowRight, ShieldCheck, HelpCircle, RefreshCw, BookmarkPlus } from 'lucide-react';
import { NavigatorResponse, PincodeInfo } from '../types';

interface ChatNavigatorProps {
  pincodeInfo: PincodeInfo | null;
  onOpenPincodeModal: () => void;
  onOpenDraftModal: (docType: string, prefillData: any) => void;
  onSaveCase: (caseData: any) => void;
  suggestedPrompt: string;
  navigationRequest: number;
}

const SAMPLE_PROMPTS = [
  { icon: '🚗', title: 'Road & Potholes', prompt: 'I fell off my two-wheeler due to a deep un-repaired pothole on the main road. Who is legally responsible and how do I file a compensation claim?' },
  { icon: '🏠', title: 'Tenant Deposit', prompt: 'I vacated my rented flat 45 days ago after giving 1 month notice. The landlord is refusing to refund my Rs 50,000 security deposit.' },
  { icon: '💧', title: 'Water Contamination', prompt: 'Our tap water has been yellow and smelling like sewage for 3 days. What emergency complaint channel should I use?' },
  { icon: '🛒', title: 'Consumer Refund', prompt: 'I bought a smartphone online that stopped working in 2 days. The company is refusing refund or replacement.' },
  { icon: '📜', title: 'RTI Inspection', prompt: 'I want to file an RTI application to inspect contractor tender documents and funds allocated for road repairs in my ward.' },
  { icon: '🗑️', title: 'Garbage Dump', prompt: 'Huge pile of garbage has been dumped outside our colony gate for 5 days attracting stray animals and stink.' },
];

export const ChatNavigator: React.FC<ChatNavigatorProps> = ({
  pincodeInfo,
  onOpenPincodeModal,
  onOpenDraftModal,
  onSaveCase,
  suggestedPrompt,
  navigationRequest,
}) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<NavigatorResponse | null>(null);
  const [savedCaseId, setSavedCaseId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (userPrompt: string) => {
    if (!userPrompt || userPrompt.trim().length < 3) return;
    setLoading(true);
    setSavedCaseId(null);
    setError('');

    try {
      const res = await fetch('/api/navigator/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userPrompt,
          pincode: pincodeInfo?.pincode || '560001',
        }),
      });

      if (!res.ok) throw new Error('Failed to analyze prompt');
      const data: NavigatorResponse = await res.json();
      setResponse(data);
    } catch (err) {
      console.error('Chat error:', err);
      setError('We could not reach the navigator. Please ensure the FastAPI backend is running, then try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (navigationRequest > 0 && suggestedPrompt) {
      setQuery(suggestedPrompt);
      handleSubmit(suggestedPrompt);
    }
  }, [navigationRequest]);

  const handleSaveToTracker = async () => {
    if (!response) return;
    try {
      const res = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: response.category_title,
          category: response.category_id,
          pincode: response.location.pincode,
          location_type: response.location.type,
          authority: response.location.authority,
          status: 'In Progress',
          details_json: {
            act: response.act_name,
            sla_days: response.sla_days,
            query: response.query,
          },
        }),
      });

      const result = await res.json();
      setSavedCaseId(result.case_id);
      onSaveCase(result);
    } catch (e) {
      console.error('Error saving case', e);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Hero Header */}
      <div className="text-center space-y-3 pt-4">
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold uppercase tracking-widest">
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Citizen Rights & Grievance Engine</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight font-['Outfit']">
          Translate Bureaucracy into <span className="text-gradient">Guided Action</span>
        </h1>
        <p className="text-base text-slate-400 max-w-2xl mx-auto">
          Describe your civic or legal problem in simple plain language. Our AI determines your applicable rights, statutory resolution SLA, official grievance channel, and generates legal draft letters.
        </p>
      </div>

      {/* PIN Code Location Context Alert Bar */}
      <div className="glass-card rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 border border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-600/20 text-blue-400">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Jurisdiction Context</p>
            <p className="text-sm font-bold text-white">
              {pincodeInfo ? (
                <>
                  {pincodeInfo.district}, {pincodeInfo.state} —{' '}
                  <span className={pincodeInfo.type === 'Rural' ? 'text-amber-400' : 'text-emerald-400'}>
                    {pincodeInfo.type} ({pincodeInfo.body})
                  </span>
                </>
              ) : (
                'PIN Code: 560001 (Bengaluru Urban — BBMP)'
              )}
            </p>
          </div>
        </div>

        <button
          onClick={onOpenPincodeModal}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-blue-300 border border-slate-700 transition-all"
        >
          Change Location PIN
        </button>
      </div>

      {/* Input Form Box */}
      <div className="glass-card rounded-3xl p-4 sm:p-6 shadow-2xl border border-slate-800 relative">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(query);
          }}
          className="space-y-3"
        >
          <div className="relative">
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe your civic problem (e.g. 'Potholes causing accidents on main road', 'Landlord holding deposit', 'Garbage dump near home')..."
              className="w-full p-4 rounded-2xl glass-input text-white text-sm focus:ring-2 focus:ring-blue-500 placeholder:text-slate-500 resize-none font-medium"
            />
          </div>

          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-400" /> Free & Anonymous Citizen Navigator
            </p>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-blue-600/30 flex items-center space-x-2 transition-all disabled:opacity-40"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing Law & SLA...</span>
                </>
              ) : (
                <>
                  <span>Navigate My Rights</span>
                  <Send className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
        {error && <p className="mt-3 px-2 text-xs font-medium text-rose-300">{error}</p>}
      </div>

      {/* Sample Query Starter Chips */}
      {!response && (
        <div className="space-y-3">
          <p className="text-xs font-extrabold uppercase tracking-wider text-slate-400 text-center">
            Or select a sample situation to test:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {SAMPLE_PROMPTS.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(item.prompt);
                  handleSubmit(item.prompt);
                }}
                className="glass-card glass-card-hover p-4 rounded-2xl text-left border border-slate-800/80 space-y-1.5 group"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{item.icon}</span>
                  <strong className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">
                    {item.title}
                  </strong>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2">{item.prompt}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* AI Analysis & Action Plan Result Output */}
      {response && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Header Result Summary Card */}
          <div className="glass-card rounded-3xl p-6 border-l-4 border-l-blue-500 border-slate-800 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                  {response.category_id.replace('_', ' ')}
                </span>
                <h2 className="text-2xl font-extrabold text-white mt-1 font-['Outfit']">
                  {response.category_title}
                </h2>
              </div>

              <div className="flex items-center space-x-3">
                <div className="px-4 py-2 rounded-2xl bg-slate-900 border border-slate-800 text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Statutory SLA</span>
                  <span className="text-emerald-400 font-extrabold text-sm flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 inline" /> {response.sla_days} Days Max
                  </span>
                </div>

                <button
                  onClick={handleSaveToTracker}
                  disabled={!!savedCaseId}
                  className={`px-4 py-2.5 rounded-2xl text-xs font-bold flex items-center space-x-2 transition-all ${
                    savedCaseId
                      ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20'
                  }`}
                >
                  <BookmarkPlus className="w-4 h-4" />
                  <span>{savedCaseId ? `Saved (${savedCaseId})` : 'Save to Tracker'}</span>
                </button>
              </div>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed font-medium">{response.summary}</p>

            {/* Applicable Law & Compensation Clause */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-0.5">Applicable Statutory Act:</span>
                <strong className="text-blue-300">{response.act_name}</strong>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-0.5">Statutory Authority ({response.location.type}):</span>
                <strong className="text-amber-300">{response.location.authority}</strong>
              </div>
            </div>

            {response.compensation_clause && (
              <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-800/40 text-purple-200 text-xs">
                <strong>💡 Citizen Right & Penalty Provision:</strong> {response.compensation_clause}
              </div>
            )}
          </div>

          {/* Step-by-Step Guided Action Plan */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-white font-['Outfit'] flex items-center gap-2">
              <ArrowRight className="w-5 h-5 text-blue-400" />
              <span>Step-by-Step Action Roadmap</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {response.steps.map((st) => (
                <div
                  key={st.step}
                  className="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col justify-between relative overflow-hidden group hover:border-blue-500/40 transition-all"
                >
                  <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-extrabold flex items-center justify-center text-sm shadow-md mb-3">
                    {st.step}
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-white mb-1.5">{st.title}</h4>
                    <p className="text-xs text-slate-400 leading-relaxed">{st.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* DOs and DONTs Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* DOs */}
            <div className="glass-card rounded-3xl p-6 border-t-4 border-t-emerald-500 border-slate-800 space-y-3">
              <h4 className="text-base font-extrabold text-emerald-400 flex items-center gap-2 font-['Outfit']">
                <CheckCircle2 className="w-5 h-5" />
                <span>What TO DO (Best Practices)</span>
              </h4>
              <ul className="space-y-2.5">
                {response.dos.map((d, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* DONTs */}
            <div className="glass-card rounded-3xl p-6 border-t-4 border-t-rose-500 border-slate-800 space-y-3">
              <h4 className="text-base font-extrabold text-rose-400 flex items-center gap-2 font-['Outfit']">
                <AlertTriangle className="w-5 h-5" />
                <span>What NOT TO DO (Avoid Pitfalls)</span>
              </h4>
              <ul className="space-y-2.5">
                {response.donts.map((d, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Instant Legal & Grievance Generator Actions */}
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4">
            <h4 className="text-lg font-bold text-white font-['Outfit']">Generate Instant Ready-to-File Documents</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <button
                onClick={() =>
                  onOpenDraftModal('rti', {
                    authority_name: response.location.authority,
                    pincode: response.location.pincode,
                    subject: response.query,
                  })
                }
                className="p-4 rounded-2xl bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/30 text-left transition-all group"
              >
                <FileText className="w-6 h-6 text-blue-400 mb-2 group-hover:scale-110 transition-transform" />
                <h5 className="text-sm font-bold text-white">Generate RTI Section 6(1)</h5>
                <p className="text-xs text-slate-400 mt-0.5">Formally request tender, file notes & delay reasons</p>
              </button>

              <button
                onClick={() =>
                  onOpenDraftModal(
                    response.category_id === 'tenant_rights' ? 'tenant_notice' : response.category_id === 'consumer_rights' ? 'consumer_notice' : 'municipal_complaint',
                    {
                      authority_name: response.location.authority,
                      pincode: response.location.pincode,
                      details: response.query,
                    }
                  )
                }
                className="p-4 rounded-2xl bg-purple-600/10 hover:bg-purple-600/20 border border-purple-500/30 text-left transition-all group"
              >
                <Mail className="w-6 h-6 text-purple-400 mb-2 group-hover:scale-110 transition-transform" />
                <h5 className="text-sm font-bold text-white">Generate Legal Notice</h5>
                <p className="text-xs text-slate-400 mt-0.5">15-day statutory notice for refund/repairs</p>
              </button>

              <a
                href={response.location.portal.includes('http') ? response.location.portal : 'https://pgportal.gov.in/'}
                target="_blank"
                rel="noreferrer"
                className="p-4 rounded-2xl bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/30 text-left transition-all group"
              >
                <ShieldCheck className="w-6 h-6 text-emerald-400 mb-2 group-hover:scale-110 transition-transform" />
                <h5 className="text-sm font-bold text-white">File on Official Portal</h5>
                <p className="text-xs text-slate-400 mt-0.5">{response.location.portal}</p>
              </a>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};
