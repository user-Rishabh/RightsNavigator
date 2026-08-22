import React, { useEffect, useState } from 'react';
import { Sparkles, Send, MapPin, CheckCircle2, AlertTriangle, FileText, Mail, Clock, ArrowRight, ShieldCheck, RefreshCw, BookmarkPlus } from 'lucide-react';
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
    if (!userPrompt || userPrompt.trim().length < 12) {
      setError('Please describe what happened in a little more detail so the AI can give useful guidance.');
      return;
    }
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

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to analyze prompt');
      }
      const data: NavigatorResponse = await res.json();
      setResponse(data);
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(err.message || 'We could not reach the navigator. Please ensure the FastAPI backend is running, then try again.');
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
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 border border-primary/20 bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider rounded-md shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-accent" />
          <span>AI Citizen Rights & Grievance Engine</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-txtprimary tracking-tight font-display">
          Translate Bureaucracy into <span className="text-gradient">Guided Action</span>
        </h1>
        <p className="text-base text-txtsecondary max-w-2xl mx-auto font-normal">
          Describe your civic or legal problem in simple plain language. Our AI determines your applicable rights, statutory resolution SLA, official grievance channel, and generates legal draft letters.
        </p>
      </div>

      {/* PIN Code Location Context Alert Bar */}
      <div className="hidden" aria-hidden="true">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-semibold text-txtsecondary uppercase tracking-wider">Active Jurisdiction Context</p>
            <p className="text-sm font-bold text-txtprimary font-display">
              {pincodeInfo ? (
                <>
                  {pincodeInfo.district}, {pincodeInfo.state} —{' '}
                  <span className={pincodeInfo.type === 'Rural' ? 'text-accent' : 'text-success'}>
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
          className="px-4 py-2 rounded-xl bg-surface hover:bg-page text-xs font-semibold text-accent border border-themeborder transition-all focus:outline-none"
        >
          Change Location PIN
        </button>
      </div>

      {/* Input Form Box (Petition Docket Entry) */}
      <div className="glass-card rounded-2xl p-4 sm:p-6 shadow-2xl border border-themeborder relative">
        <div className="absolute top-0 left-6 -translate-y-1/2 bg-surface border border-themeborder px-3 py-1 rounded text-[10px] font-extrabold tracking-widest text-accent uppercase">
          Petition Submission Form
        </div>
        
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(query);
          }}
          className="space-y-4 pt-2"
        >
          <div className="relative">
            <label htmlFor="civic-query" className="sr-only">Describe your civic or legal situation</label>
            <textarea
              id="civic-query"
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe your civic problem (e.g. 'Potholes causing accidents on main road', 'Landlord holding deposit', 'Garbage dump near home')..."
              className="w-full p-4 rounded-xl glass-input text-txtprimary text-sm placeholder:text-txtsecondary resize-none font-medium focus:outline-none"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <p className="text-xs text-txtsecondary flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-accent" /> Free & Anonymous Citizen Rights Protection
            </p>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-accent-solid hover:opacity-90 text-accent-text font-bold text-sm shadow-md flex items-center justify-center space-x-2 transition-all disabled:opacity-40 focus:outline-none"
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
        {error && <p className="mt-3 px-2 text-xs font-medium text-danger">{error}</p>}
      </div>

      {/* Sample Query Starter Chips */}
      {!response && (
        <div className="space-y-4">
          <p className="text-xs font-bold uppercase tracking-wider text-txtsecondary text-center">
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
                className="glass-card glass-card-hover p-4 rounded-xl text-left border border-themeborder space-y-1.5 group border-l-2 border-l-accent focus:outline-none"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{item.icon}</span>
                  <strong className="text-sm font-bold text-txtprimary group-hover:text-accent transition-colors font-display">
                    {item.title}
                  </strong>
                </div>
                <p className="text-xs text-txtsecondary line-clamp-2">{item.prompt}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* AI Analysis & Action Plan Result Output (Parchment Docket Sheet) */}
      {response && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Header Result Summary Card */}
          <div className="docket-sheet rounded-2xl p-6 md:p-8 space-y-6 court-margin shadow-2xl relative">
            
            {/* Signature Element: Rotated distressed ink stamp seal */}
            {response.grounded !== false && (
              <div className="absolute top-4 right-4 sm:top-6 sm:right-6 rotate-[-5deg] z-10">
                <div className="ink-stamp ink-stamp-danger select-none pointer-events-none">
                  <Clock className="w-3.5 h-3.5 inline mr-1" />
                  <span>SLA LIMIT: {response.sla_days} DAYS</span>
                </div>
              </div>
            )}

            <div className="court-content space-y-6">
              
              {/* Top Meta info */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-themeborder pb-4 pr-0 sm:pr-32">
                <div>
                  <span className="px-2 py-0.5 rounded border border-accent/20 bg-accent/10 text-accent text-[10px] font-bold uppercase tracking-wider">
                    {response.category_id.replace('_', ' ')}
                  </span>
                  <h2 className="text-2xl sm:text-3xl font-bold text-txtprimary mt-2 font-display">
                    {response.category_title}
                  </h2>
                </div>

                <div className="flex items-center space-x-3 mt-2 sm:mt-0">
                  <button
                    onClick={handleSaveToTracker}
                    disabled={!!savedCaseId}
                    className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-2 transition-all focus:outline-none ${
                      savedCaseId
                        ? 'bg-success/20 text-success border border-success/30'
                        : 'bg-primary hover:bg-primary/95 text-page shadow-md'
                    }`}
                  >
                    <BookmarkPlus className="w-4 h-4" />
                    <span>{savedCaseId ? `Saved (${savedCaseId})` : 'Save to Case Tracker'}</span>
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {response.grounded === false && (
                  <div className="p-4 rounded-xl bg-slate-500/10 border border-slate-500/20 text-xs text-txtsecondary flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <span>General guidance for {response.location.state || "your state"} - not yet verified against local statute. Confirm with your municipal office.</span>
                  </div>
                )}
                <p className="text-sm text-txtprimary leading-relaxed font-normal">{response.summary}</p>

                {response.applicable_rights?.length > 0 && (
                  <div className="rounded-xl bg-primary/5 border border-primary/15 p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-primary mb-2 font-display">Rights identified for your situation</p>
                    <ul className="space-y-2">
                      {response.applicable_rights.map((right, index) => (
                        <li key={index} className="text-sm text-txtprimary flex items-start gap-2">
                          <CheckCircle2 className="w-4 h-4 text-accent mt-0.5 shrink-0" />
                          <span>{right}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Applicable Law & Compensation Clause */}
                {response.grounded !== false ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-2">
                      <div className="p-3.5 rounded-xl bg-page border border-themeborder">
                        <span className="text-txtsecondary font-semibold block mb-0.5 uppercase tracking-wider text-[10px]">Applicable Statutory Act:</span>
                        <strong className="text-primary font-display text-sm font-medium">{response.act_name}</strong>
                      </div>

                      <div className="p-3.5 rounded-xl bg-page border border-themeborder">
                        <span className="text-txtsecondary font-semibold block mb-0.5 uppercase tracking-wider text-[10px]">Statutory Authority ({response.location.type}):</span>
                        <strong className="text-accent font-display text-sm font-medium">{response.location.authority}</strong>
                      </div>
                    </div>

                    {response.compensation_clause && (
                      <div className="p-3.5 rounded-xl bg-danger/10 border border-danger/20 text-danger text-xs">
                        <strong>💡 Statutory Compensation Clause:</strong> {response.compensation_clause}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="grid grid-cols-1 gap-3 text-xs pt-2">
                    <div className="p-3.5 rounded-xl bg-page border border-themeborder">
                      <span className="text-txtsecondary font-semibold block mb-0.5 uppercase tracking-wider text-[10px]">General Grievance Authority ({response.location.type}):</span>
                      <strong className="text-accent font-display text-sm font-medium">{response.location.authority}</strong>
                    </div>
                  </div>
                )}
              </div>
              
            </div>
          </div>

          {/* Step-by-Step Guided Action Plan (Filing Index Tabs) */}
          {response.steps && response.steps.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-txtprimary font-display flex items-center gap-2">
                <ArrowRight className="w-5 h-5 text-accent" />
                <span>Step-by-Step Action Roadmap</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {response.steps.map((st) => (
                  <div
                    key={st.step}
                    className="glass-card rounded-xl p-5 border border-themeborder flex flex-col justify-between relative overflow-hidden group hover:border-accent transition-all pt-8 focus:outline-none"
                  >
                    {/* Folder Tab Effect */}
                    <div className="absolute top-0 left-0 bg-primary/10 text-primary font-bold text-[10px] uppercase tracking-wider px-3 py-1 rounded-br-lg border-r border-b border-themeborder">
                      INDEX SEC. {st.step}
                    </div>
                    <div className="mt-2">
                      <h4 className="text-base font-bold text-txtprimary mb-1.5 font-display">{st.title}</h4>
                      <p className="text-xs text-txtsecondary leading-relaxed">{st.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* DOs and DONTs Section (Translucent Panels) */}
          {((response.dos && response.dos.length > 0) || (response.donts && response.donts.length > 0)) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* DOs */}
              <div className="bg-success-low rounded-xl p-6 border-l-4 border-l-success border border-success/20 space-y-4">
                <h4 className="text-base font-bold text-success flex items-center gap-2 font-display uppercase tracking-wide">
                  <CheckCircle2 className="w-5 h-5 text-success" />
                  <span>What TO DO (Best Practices)</span>
                </h4>
                <ul className="space-y-3">
                  {response.dos.map((d, i) => (
                    <li key={i} className="text-xs text-txtprimary flex items-start space-x-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-success mt-1.5 shrink-0" />
                      <span>{d}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* DONTs */}
              <div className="bg-danger-low rounded-xl p-6 border-l-4 border-l-danger border border-danger/20 space-y-4">
                <h4 className="text-base font-bold text-danger flex items-center gap-2 font-display uppercase tracking-wide">
                  <AlertTriangle className="w-5 h-5 text-danger" />
                  <span>What NOT TO DO (Avoid Pitfalls)</span>
                </h4>
                <ul className="space-y-3">
                  {response.donts.map((d, i) => (
                    <li key={i} className="text-xs text-txtprimary flex items-start space-x-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-danger mt-1.5 shrink-0" />
                      <span>{d}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Instant Legal & Grievance Generator Actions */}
          <div className="glass-card rounded-xl p-6 border border-themeborder space-y-4">
            <h4 className="text-lg font-bold text-txtprimary font-display">Generate Instant Ready-to-File Documents</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <button
                onClick={() =>
                  onOpenDraftModal('rti', {
                    authority_name: response.location.authority,
                    pincode: response.location.pincode,
                    subject: response.query,
                  })
                }
                className="p-4 rounded-xl bg-primary/5 hover:bg-primary/10 border border-primary/20 text-left transition-all group focus:outline-none"
              >
                <FileText className="w-6 h-6 text-primary mb-2 group-hover:scale-105 transition-transform" />
                <h5 className="text-sm font-bold text-txtprimary font-display">Generate RTI Section 6(1)</h5>
                <p className="text-xs text-txtsecondary mt-0.5">Formally request tender, file notes & delay reasons</p>
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
                className="p-4 rounded-xl bg-danger/5 hover:bg-danger/10 border border-danger/20 text-left transition-all group focus:outline-none"
              >
                <Mail className="w-6 h-6 text-danger mb-2 group-hover:scale-105 transition-transform" />
                <h5 className="text-sm font-bold text-txtprimary font-display">Generate Legal Notice</h5>
                <p className="text-xs text-txtsecondary mt-0.5">15-day statutory notice for refund/repairs</p>
              </button>

              <a
                href={response.location.portal.includes('http') ? response.location.portal : 'https://pgportal.gov.in/'}
                target="_blank"
                rel="noreferrer"
                className="p-4 rounded-xl bg-success/5 hover:bg-success/10 border border-success/20 text-left transition-all group focus:outline-none"
              >
                <ShieldCheck className="w-6 h-6 text-success mb-2 group-hover:scale-105 transition-transform" />
                <h5 className="text-sm font-bold text-txtprimary font-display">File on Official Portal</h5>
                <p className="text-xs text-txtsecondary mt-0.5">{response.location.portal}</p>
              </a>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};
