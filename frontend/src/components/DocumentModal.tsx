import React, { useState, useEffect } from 'react';
import { X, Copy, Download, Check, Sparkles, FileText, Send, Printer } from 'lucide-react';
import confetti from 'canvas-confetti';

interface DocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialDocType: string;
  prefillData: {
    authority_name?: string;
    pincode?: string;
    subject?: string;
    details?: string;
  };
}

export const DocumentModal: React.FC<DocumentModalProps> = ({
  isOpen,
  onClose,
  initialDocType,
  prefillData,
}) => {
  const [docType, setDocType] = useState(initialDocType || 'rti');
  const [citizenName, setCitizenName] = useState('');
  const [address, setAddress] = useState('');
  const [pincode, setPincode] = useState(prefillData?.pincode || '560001');
  const [authorityName, setAuthorityName] = useState(prefillData?.authority_name || '');
  const [opponentName, setOpponentName] = useState('');
  const [subject, setSubject] = useState(prefillData?.subject || prefillData?.details || '');
  const [details, setDetails] = useState(prefillData?.details || prefillData?.subject || '');

  const [generatedDoc, setGeneratedDoc] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [draftSource, setDraftSource] = useState<'gemini' | 'template'>('template');

  useEffect(() => {
    if (initialDocType) setDocType(initialDocType);
    if (prefillData?.pincode) setPincode(prefillData.pincode);
    if (prefillData?.authority_name) setAuthorityName(prefillData.authority_name);
    if (prefillData?.subject || prefillData?.details) {
      setSubject(prefillData.subject || prefillData.details || '');
      setDetails(prefillData.details || prefillData.subject || '');
    }
  }, [initialDocType, prefillData]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/generator/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_type: docType,
          citizen_name: citizenName,
          address: address,
          pincode: pincode,
          authority_name: authorityName,
          opponent_name: opponentName,
          subject: subject,
          details: details,
          questions: [
            `Provide certified copies of tenders, work orders, and completion certificates for the subject location.`,
            `Provide daily progress report, measurement book entries, and names of officers accountable.`,
            `State exact reason for delay and expected resolution date under State Right to Public Services Act.`
          ]
        }),
      });

      const data = await res.json();
      setGeneratedDoc(data.content);
      setDraftSource(data.source === 'gemini' ? 'gemini' : 'template');

      // Trigger celebration confetti
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.6 }
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      handleGenerate();
    }
  }, [isOpen, docType]);

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedDoc);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([generatedDoc], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = `${docType.toUpperCase()}_Draft_${pincode}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0d0d0f] border border-white/10 rounded-3xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-[0_30px_80px_rgba(0,0,0,0.65)] overflow-hidden relative">
        
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-[#101012]">
          <div className="flex items-center space-x-3">
            <div className="p-3 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white font-['Outfit']">Legal Notice & RTI Draft Generator</h3>
              <p className="text-xs text-slate-400">{draftSource === 'gemini' ? 'Personalised by Gemini AI with legal-template safeguards' : 'Statutory legal template — add Gemini API key for AI personalisation'}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-white/10 text-slate-400 hover:text-white hover:bg-white/15 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Split View */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 flex-1 overflow-hidden">
          
          {/* Controls Column */}
          <div className="lg:col-span-5 p-6 border-r border-white/10 space-y-4 overflow-y-auto bg-[#09090a]">
            <div>
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">Document Type:</label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full p-3 rounded-2xl glass-input text-white text-xs font-semibold"
              >
                <option value="rti" className="bg-[#0d0d0f] text-white">Section 6(1) RTI Application</option>
                <option value="consumer_notice" className="bg-[#0d0d0f] text-white">Consumer Court Legal Notice (CPA 2019)</option>
                <option value="tenant_notice" className="bg-[#0d0d0f] text-white">Tenant Security Deposit Demand Notice</option>
                <option value="municipal_complaint" className="bg-[#0d0d0f] text-white">Municipal Statutory Complaint Notice</option>
              </select>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Your Full Name:</label>
                <input
                  type="text"
                  value={citizenName}
                  onChange={(e) => setCitizenName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl glass-input text-white text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Communication Address & PIN:</label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl glass-input text-white text-xs mb-2"
                />
                <input
                  type="text"
                  maxLength={6}
                  value={pincode}
                  onChange={(e) => setPincode(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl glass-input text-white text-xs font-mono"
                  placeholder="PIN Code"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Target Authority / Opponent:</label>
                <input
                  type="text"
                  value={docType === 'rti' || docType === 'municipal_complaint' ? authorityName : opponentName}
                  onChange={(e) =>
                    docType === 'rti' || docType === 'municipal_complaint'
                      ? setAuthorityName(e.target.value)
                      : setOpponentName(e.target.value)
                  }
                  className="w-full px-3.5 py-2.5 rounded-xl glass-input text-white text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Subject / Details:</label>
                <textarea
                  rows={3}
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                  className="w-full p-3 rounded-xl glass-input text-white text-xs resize-none"
                />
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-md shadow-blue-600/30"
            >
              <Sparkles className="w-4 h-4" />
              <span>Update Draft Document</span>
            </button>
          </div>

          {/* Document Content Live Preview */}
          <div className="lg:col-span-7 p-6 flex flex-col justify-between overflow-y-auto bg-[#111113]">
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <span className="text-xs font-extrabold text-blue-400 uppercase tracking-widest flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-emerald-400" /> Formatted Legal Notice Preview
                </span>
                <div className="flex space-x-2">
                  <button
                    onClick={handleCopy}
                    className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 text-xs font-semibold text-slate-200 flex items-center gap-1.5 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                  </button>

                  <button
                    onClick={handleDownload}
                    className="px-3 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-xs font-semibold text-blue-300 border border-blue-500/30 flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download TXT</span>
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-16">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-xs text-slate-400">Formatting legal clauses...</p>
                </div>
              ) : (
                <pre className="p-4 rounded-2xl bg-[#050505] border border-white/10 text-slate-200 font-mono text-xs leading-relaxed whitespace-pre-wrap select-all max-h-[50vh] overflow-y-auto">
                  {generatedDoc}
                </pre>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-400">
              <span>💡 Ready to print or attach with court fee stamp / Speed Post AD</span>
              <span className="font-semibold text-emerald-400">100% Free Public Tool</span>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
