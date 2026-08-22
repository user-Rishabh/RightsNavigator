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
    <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-xl border-b border-themeborder shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Hackathon Badge */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('chat')}>
            <div className="w-11 h-11 rounded-xl bg-primary border border-accent/20 flex items-center justify-center shadow-lg">
              <Scale className="w-5.5 h-5.5 text-page" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl tracking-tight text-txtprimary font-display">
                  Rights<span className="text-accent font-medium">Navigator</span>
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
          <nav className="hidden md:flex items-center space-x-1 bg-page/80 p-1.5 rounded-2xl border border-themeborder">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all focus:outline-none ${
                activeTab === 'chat'
                  ? 'bg-primary text-page border border-accent/20 shadow-md'
                  : 'text-txtsecondary hover:text-txtprimary hover:bg-surface/50'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>AI Navigator</span>
            </button>

            <button
              onClick={() => setActiveTab('catalog')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all focus:outline-none ${
                activeTab === 'catalog'
                  ? 'bg-primary text-page border border-accent/20 shadow-md'
                  : 'text-txtsecondary hover:text-txtprimary hover:bg-surface/50'
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
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all focus:outline-none relative ${
                activeTab === 'cases'
                  ? 'bg-primary text-page border border-accent/20 shadow-md'
                  : 'text-txtsecondary hover:text-txtprimary hover:bg-surface/50'
              }`}
            >
              <FileCheck className="w-4 h-4" />
              <span>My Cases</span>
              {caseCount > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 text-xs font-extrabold rounded-full bg-success text-page">
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
              className="theme-toggle w-10 h-10 rounded-xl bg-surface border border-themeborder text-txtprimary hover:border-accent hover:bg-page transition-all flex items-center justify-center focus:outline-none"
            >
              {isLightMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>
            <button
              onClick={onOpenPincodeModal}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-surface border border-themeborder text-txtprimary hover:border-accent hover:bg-page transition-all text-xs font-semibold shadow-inner focus:outline-none"
            >
              <div className="w-2 h-2 rounded-full bg-success animate-ping" />
              <MapPin className="w-3.5 h-3.5 text-accent" />
              <span>
                {pincodeInfo ? (
                  <>
                    <strong className="text-txtprimary">{pincodeInfo.district}</strong>
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
