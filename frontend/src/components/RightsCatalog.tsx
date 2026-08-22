import React, { useEffect, useState } from 'react';
import { 
  Construction, Trash2, Droplets, ShoppingBag, Home, FileText, 
  Zap, HeartPulse, Briefcase, GraduationCap, ShieldAlert, HeartHandshake, Building2,
  Clock, ArrowRight, ShieldCheck 
} from 'lucide-react';
import { CategoryItem } from '../types';

interface RightsCatalogProps {
  onSelectCategory: (catId: string, promptText: string) => void;
}

const ICON_MAP: Record<string, any> = {
  Construction: Construction,
  Trash2: Trash2,
  Droplets: Droplets,
  ShoppingBag: ShoppingBag,
  Home: Home,
  FileText: FileText,
  Zap: Zap,
  HeartPulse: HeartPulse,
  Briefcase: Briefcase,
  GraduationCap: GraduationCap,
  ShieldAlert: ShieldAlert,
  HeartHandshake: HeartHandshake,
  Building2: Building2,
};

const ACTIVE_CATEGORIES = [
  'potholes_roads',
  'garbage_sanitation',
  'water_supply',
  'tenant_rights',
  'rti_access',
  'consumer_rights'
];

export const RightsCatalog: React.FC<RightsCatalogProps> = ({ onSelectCategory }) => {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/rights/categories')
      .then((res) => res.json())
      .then((data) => {
        setCategories(data.categories || []);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleComingSoonClick = (catId: string) => {
    setActiveTooltip(catId);
    setTimeout(() => {
      setActiveTooltip((current) => current === catId ? null : current);
    }, 3000);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Catalog Title Header */}
      <div className="text-center space-y-3">
        <h2 className="text-4xl font-extrabold text-white font-['Outfit'] tracking-tight">
          Civic & Legal <span className="text-gradient">Rights Catalog</span>
        </h2>
        <p className="text-sm text-slate-400 max-w-2xl mx-auto">
          Explore statutory guarantees, resolution SLAs under State Right to Public Services Acts, and urban vs rural grievance escalation paths.
        </p>
      </div>

      <div className="text-center">
        <p className="text-xs text-txtsecondary">
          We're launching with 6 fully verified categories — more are being added.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading Rights Catalog...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((cat) => {
            const IconComp = ICON_MAP[cat.icon] || ShieldCheck;
            const urbanRule = cat.rules?.urban || {};
            const ruralRule = cat.rules?.rural || {};
            const isComingSoon = !ACTIVE_CATEGORIES.includes(cat.id);

            return (
              <div
                key={cat.id}
                className={`glass-card rounded-3xl p-6 border border-slate-800 flex flex-col justify-between space-y-4 group relative ${
                  isComingSoon ? 'opacity-70' : 'glass-card-hover'
                }`}
              >
                {isComingSoon && (
                  <span className="absolute top-4 right-4 px-2 py-0.5 rounded-full text-[10px] font-bold border border-[var(--text-muted)]/20 bg-[var(--text-muted)]/10 text-[var(--text-muted)]">
                    Coming soon
                  </span>
                )}

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className={`p-3 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 transition-transform ${
                      isComingSoon ? 'grayscale saturate-50' : 'group-hover:scale-110'
                    }`}>
                      <IconComp className="w-6 h-6" />
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-extrabold text-xs flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" /> SLA: {cat.default_sla_days} Days
                    </span>
                  </div>

                  <div>
                    <h3 className={`text-xl font-bold text-white transition-colors font-['Outfit'] ${
                      isComingSoon ? '' : 'group-hover:text-blue-400'
                    }`}>
                      {cat.name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">{cat.description}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800/80 text-xs">
                    <span className="text-slate-500 block font-semibold">Statutory Act:</span>
                    <strong className="text-blue-300 font-medium">{cat.act_name}</strong>
                  </div>

                  {/* Urban vs Rural Authorities */}
                  <div className="space-y-2 text-xs">
                    <div className="flex items-start space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 mt-1 shrink-0" />
                      <div>
                        <strong className="text-emerald-300">Urban:</strong>{' '}
                        <span className="text-slate-300">{urbanRule.authority}</span>
                      </div>
                    </div>
                    <div className="flex items-start space-x-2">
                      <span className="w-2 h-2 rounded-full bg-amber-400 mt-1 shrink-0" />
                      <div>
                        <strong className="text-amber-300">Rural:</strong>{' '}
                        <span className="text-slate-300">{ruralRule.authority}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  {activeTooltip === cat.id && (
                    <div className="text-[11px] text-amber-500 bg-amber-500/10 border border-amber-500/20 p-2 rounded-xl text-center transition-all duration-300">
                      This category is in progress — check back soon
                    </div>
                  )}

                  <button
                    onClick={() => {
                      if (isComingSoon) {
                        handleComingSoonClick(cat.id);
                      } else {
                        onSelectCategory(
                          cat.id,
                          `I need guidance regarding ${cat.name}. What are my rights and how do I file a complaint?`
                        );
                      }
                    }}
                    className={`w-full py-3 rounded-2xl font-bold text-xs transition-all flex items-center justify-center space-x-2 shadow-sm ${
                      isComingSoon
                        ? 'bg-slate-800/50 text-slate-500 hover:bg-slate-800/50 cursor-pointer'
                        : 'bg-slate-800 hover:bg-blue-600 text-slate-200 hover:text-white'
                    }`}
                  >
                    <span>{isComingSoon ? 'Coming Soon' : `Navigate ${cat.name}`}</span>
                    {!isComingSoon && <ArrowRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
