import React from 'react';
import { Scale, Heart, ShieldCheck, Github, ExternalLink } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-white/10 bg-black mt-auto py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-lg text-white font-['Outfit']">
                Rights<span className="text-blue-400">Navigator</span> AI
              </span>
              <p className="text-xs text-slate-400">Empowering Indian Citizens with AI-Guided Legal & Civic Action</p>
            </div>
          </div>

          <div className="hidden" aria-hidden="true">
            <span className="flex items-center gap-1.5 text-blue-300">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <strong>OOSC 4.0 Hackathon</strong> — Track PS3
            </span>
            <span>
              Built with <Heart className="w-3.5 h-3.5 inline text-rose-500 mx-0.5 fill-rose-500" /> by <strong>Rishabh & Girish</strong>
            </span>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
          <p>© 2026 RightsNavigator AI. Open-source civic empowerment tool.</p>
          <div className="flex items-center space-x-4">
            <span className="hover:text-slate-300 transition-colors">Consumer Protection Act 2019 & RTI 2005</span>
          </div>
        </div>

      </div>
    </footer>
  );
};
