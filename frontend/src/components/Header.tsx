import React from 'react';
import { Scale, MapPin, ShieldCheck, FileCheck, Layers, Users, Sparkles } from 'lucide-react';
import { PincodeInfo } from '../types';

interface HeaderProps {
  activeTab: 'chat' | 'catalog' | 'cases';
  setActiveTab: (tab: 'chat' | 'catalog' | 'cases') => void;
  pincodeInfo: PincodeInfo | null;
  onOpenPincodeModal: () => void;
  caseCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  pincodeInfo,
  onOpenPincodeModal,
  caseCount,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Hackathon Badge */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('chat')}>
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
              <Scale className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-xl tracking-tight text-white font-['Outfit']">
                  Rights<span className="text-blue-400">Navigator</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-widest">
                  AI 4.0
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                <span>OOSC 4.0 Hackathon</span>
                <span className="text-slate-600">•</span>
                <span className="text-blue-300/80 flex items-center gap-1">
                  <Users className="w-3 h-3 inline text-purple-400" /> Rishabh & Girish
                </span>
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                activeTab === 'chat'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>AI Navigator</span>
            </button>

            <button
              onClick={() => setActiveTab('catalog')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                activeTab === 'catalog'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Rights Catalog</span>
            </button>

            <button
              onClick={() => setActiveTab('cases')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all relative ${
                activeTab === 'cases'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <FileCheck className="w-4 h-4" />
              <span>My Cases</span>
              {caseCount > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 text-xs font-extrabold rounded-full bg-emerald-500 text-slate-950">
                  {caseCount}
                </span>
              )}
            </button>
          </nav>

          {/* PIN Code & Location Badge */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenPincodeModal}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700/70 text-slate-200 hover:border-blue-500/50 hover:bg-slate-850 transition-all text-xs font-semibold shadow-inner"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <MapPin className="w-3.5 h-3.5 text-blue-400" />
              <span>
                {pincodeInfo ? (
                  <>
                    <strong className="text-white">{pincodeInfo.pincode}</strong> ({pincodeInfo.type})
                  </>
                ) : (
                  'Set PIN Code'
                )}
              </span>
            </button>

            <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-purple-950/40 border border-purple-800/40 text-purple-300 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
              <span>PS3 Track</span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
};
