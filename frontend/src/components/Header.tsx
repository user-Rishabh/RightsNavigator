import React from 'react';
import { Scale, MapPin, FileCheck, Layers, Users, Sparkles, Moon, Sun, Award } from 'lucide-react';
import { PincodeInfo } from '../types';

interface HeaderProps {
  activeTab: 'chat' | 'catalog' | 'cases' | 'schemes';
  setActiveTab: (tab: 'chat' | 'catalog' | 'cases' | 'schemes') => void;
  pincodeInfo: PincodeInfo | null;
  onOpenPincodeModal: () => void;
  caseCount: number;
  isLightMode: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  pincodeInfo,
  onOpenPincodeModal,
  caseCount,
  isLightMode,
  onToggleTheme,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-black/80 backdrop-blur-xl border-b border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.28)]">
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
              </div>
              <p className="hidden" aria-hidden="true">
                <span>OOSC 4.0 Hackathon</span>
                <span className="text-slate-600">•</span>
                <span className="text-blue-300/80 flex items-center gap-1">
                  <Users className="w-3 h-3 inline text-purple-400" /> Rishabh & Girish
                </span>
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 bg-white/[0.045] p-1.5 rounded-2xl border border-white/10">
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
              onClick={() => setActiveTab('schemes')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                activeTab === 'schemes'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Award className="w-4 h-4" />
              <span>Eligible Schemes</span>
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
              type="button"
              onClick={onToggleTheme}
              aria-label={isLightMode ? 'Switch to dark mode' : 'Switch to light mode'}
              title={isLightMode ? 'Switch to dark mode' : 'Switch to light mode'}
              className="theme-toggle w-10 h-10 rounded-xl bg-white/[0.045] border border-white/10 text-slate-200 hover:border-blue-500/50 hover:bg-white/[0.08] transition-all flex items-center justify-center"
            >
              {isLightMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>
            <button
              onClick={onOpenPincodeModal}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-white/[0.045] border border-white/10 text-slate-200 hover:border-blue-500/50 hover:bg-white/[0.08] transition-all text-xs font-semibold shadow-inner"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <MapPin className="w-3.5 h-3.5 text-blue-400" />
              <span>
                {pincodeInfo ? (
                  <>
                    <strong className="text-white">{pincodeInfo.district}</strong>
                  </>
                ) : (
                  'Set Location / PIN Code'
                )}
              </span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};
