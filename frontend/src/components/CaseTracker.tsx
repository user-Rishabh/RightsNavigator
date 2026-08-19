import React, { useEffect, useState } from 'react';
import { FileCheck, Clock, MapPin, Building2, CheckCircle2, AlertCircle, ArrowUpRight, PlusCircle } from 'lucide-react';
import { TrackedCase } from '../types';

interface CaseTrackerProps {
  onNewCase: () => void;
  onOpenDraftModal: (docType: string, prefillData: any) => void;
}

export const CaseTracker: React.FC<CaseTrackerProps> = ({ onNewCase, onOpenDraftModal }) => {
  const [cases, setCases] = useState<TrackedCase[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchCases = async () => {
    try {
      const res = await fetch('/api/cases');
      const data = await res.json();
      setCases(data.cases || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-white font-['Outfit']">
            My Tracked <span className="text-gradient">Grievances & Cases</span>
          </h2>
          <p className="text-sm text-slate-400">
            Monitor statutory SLA timelines, pending escalation dates, and quick legal follow-up actions.
          </p>
        </div>

        <button
          onClick={onNewCase}
          className="px-5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center space-x-2 transition-all shadow-lg shadow-blue-600/20"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Navigate New Grievance</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-400">Fetching cases...</p>
        </div>
      ) : cases.length === 0 ? (
        <div className="glass-card rounded-3xl p-12 text-center border border-slate-800 space-y-4">
          <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
            <FileCheck className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">No Tracked Grievances Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Start by describing any civic problem or consumer/tenant issue in the AI Navigator to automatically track statutory resolution deadlines.
            </p>
          </div>
          <button
            onClick={onNewCase}
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all inline-block"
          >
            Start AI Navigation
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {cases.map((c) => (
            <div
              key={c.id}
              className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-extrabold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-lg border border-blue-500/20">
                      {c.id}
                    </span>
                    <span className="text-xs text-slate-400">PIN: {c.pincode}</span>
                  </div>

                  <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> {c.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white font-['Outfit']">{c.title}</h3>
                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span>Authority: <strong className="text-slate-300">{c.authority}</strong></span>
                  </p>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between text-slate-400">
                    <span>Target Statutory SLA:</span>
                    <strong className="text-emerald-400 font-extrabold">{c.details?.sla_days || 7} Days</strong>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Location Jurisdiction:</span>
                    <span className="text-slate-300 font-medium">{c.location_type}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                <button
                  onClick={() =>
                    onOpenDraftModal('rti', {
                      authority_name: c.authority,
                      pincode: c.pincode,
                      subject: `Follow-up RTI for Case ${c.id}: ${c.title}`,
                    })
                  }
                  className="py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center gap-1 transition-all"
                >
                  <span>Draft RTI Application</span>
                </button>

                <button
                  onClick={() =>
                    onOpenDraftModal('municipal_complaint', {
                      authority_name: c.authority,
                      pincode: c.pincode,
                      subject: `Statutory Escalation Notice for ${c.title}`,
                    })
                  }
                  className="py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-semibold flex items-center justify-center gap-1 transition-all border border-blue-500/30"
                >
                  <span>Escalate Notice</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
