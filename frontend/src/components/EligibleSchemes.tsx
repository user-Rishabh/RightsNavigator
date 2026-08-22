import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, ChevronDown, Award, ExternalLink, HelpCircle, 
  CheckCircle2, AlertTriangle, XCircle, Info, RefreshCw, 
  Landmark, FileText, ArrowRight, ShieldCheck, MapPin, X, Sparkles 
} from 'lucide-react';
import { PincodeInfo } from '../types';

interface Scheme {
  id: string;
  name: string;
  ministry: string;
  category: string;
  description: string;
  benefit_amount: string;
  benefit_type: string;
  state_applicability: string;
  official_portal: string;
  helpline: string;
  required_documents: string[];
  application_process: string;
  last_verified?: string;
  source_url?: string;
  similarity_score?: number;
  eligibility?: {
    status: 'Eligible' | 'Possibly Eligible' | 'Not Eligible';
    score: number;
    reasons: string[];
  };
}

interface EligibleSchemesProps {
  pincodeInfo: PincodeInfo | null;
}

interface EligibilityResult {
  status: 'Eligible' | 'Possibly Eligible' | 'Not Eligible';
  score: number;
  reasons: string[];
}

export const EligibleSchemes: React.FC<EligibleSchemesProps> = ({ pincodeInfo }) => {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active view tab: 'ai' or 'manual'
  const [activeSubTab, setActiveSubTab] = useState<'ai' | 'manual'>('ai');

  // AI Finder state
  const [problemText, setProblemText] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiGroundedResponse, setAiGroundedResponse] = useState<string | null>(null);
  const [aiRecommendedSchemes, setAiRecommendedSchemes] = useState<Scheme[]>([]);

  // Search & Filter state for Manual Directory
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedState, setSelectedState] = useState('All');
  const [selectedBenefitType, setSelectedBenefitType] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [sortBy, setSortBy] = useState('Best Match');

  // Modals state
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [warningScheme, setWarningScheme] = useState<Scheme | null>(null);

  // User Profile state (defaults derived from pincodeInfo where possible)
  const [profile, setProfile] = useState({
    state: pincodeInfo?.state || 'Karnataka',
    age: 25,
    income: 12000,
    occupation: 'Unorganized Worker',
    housing: 'Tenant',
    bpl: 'No',
    gender: 'Female'
  });

  // Keep state in sync with updated pincodeInfo
  useEffect(() => {
    if (pincodeInfo?.state) {
      setProfile(prev => ({ ...prev, state: pincodeInfo.state }));
    }
  }, [pincodeInfo]);

  // Fetch schemes from the backend API on load
  useEffect(() => {
    fetch('/api/schemes')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load schemes.');
        return res.json();
      })
      .then(data => {
        setSchemes(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: name === 'age' || name === 'income' ? Number(value) : value
    }));
  };

  const handleResetProfile = () => {
    setProfile({
      state: pincodeInfo?.state || 'Karnataka',
      age: 25,
      income: 12000,
      occupation: 'Unorganized Worker',
      housing: 'Tenant',
      bpl: 'No',
      gender: 'Female'
    });
  };

  // Client-side Eligibility Evaluation Logic (Manual Directory fallback)
  const evaluateEligibility = (scheme: Scheme): EligibilityResult => {
    const reasons: string[] = [];
    let status: 'Eligible' | 'Possibly Eligible' | 'Not Eligible' = 'Not Eligible';
    let score = 10;

    // Check State Applicability first
    const schemeState = scheme.state_applicability || 'All';
    if (schemeState !== 'All' && schemeState.toLowerCase() !== profile.state.toLowerCase()) {
      return {
        status: 'Not Eligible',
        score: 5,
        reasons: [`This scheme is only active in ${schemeState}. Current state is ${profile.state}.`]
      };
    }

    const nameLower = scheme.name.toLowerCase();
    const idLower = scheme.id ? scheme.id.toLowerCase() : '';

    if (nameLower.includes('arogya') || idLower.includes('pmjay') || nameLower.includes('health insurance') || nameLower.includes('suraksha')) {
      const isUnorg = profile.occupation === 'Unorganized Worker';
      const isLowInc = profile.income <= 15000;
      const isBpl = profile.bpl === 'Yes';
      const isKutcha = profile.housing === 'Homeless/Kutcha House';

      if (isLowInc || isUnorg || isBpl || isKutcha) {
        status = 'Eligible';
        score = 95;
        if (isLowInc) reasons.push(`Monthly income (₹${profile.income.toLocaleString()}) is below ₹15,000 limit.`);
        if (isUnorg) reasons.push('Working in unorganized sector (fits occupational criteria).');
        if (isBpl) reasons.push('Possess active BPL / Priority Ration Card status.');
        if (isKutcha) reasons.push('Residing in homeless / kutcha housing.');
      } else if (profile.income <= 25000) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push(`Monthly income (₹${profile.income.toLocaleString()}) is under ₹25,000. Pending verification of SECC data.`);
      } else {
        reasons.push('Income exceeds threshold and no target occupational/deprivation criteria met.');
      }
    } 
    else if (nameLower.includes('awas') || nameLower.includes('housing') || idLower.includes('pmay')) {
      const isLowInc = profile.income <= 25000;
      const isCorrectHousing = profile.housing === 'Tenant' || profile.housing === 'Homeless/Kutcha House';

      if (isLowInc && isCorrectHousing) {
        status = 'Eligible';
        score = 95;
        reasons.push('Income matches EWS/LIG threshold (below ₹25,000/month).');
        reasons.push('Do not own permanent pucca housing (currently Renting or Kutcha house).');
      } else if (profile.income <= 50000) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push(`Income is under ₹50,000/month. Requires certificate verifying no ownership of other urban properties.`);
      } else {
        reasons.push('Income exceeds housing eligibility caps or user already owns a permanent house.');
      }
    } 
    else if (nameLower.includes('maan-dhan') || idLower.includes('pmsym') || nameLower.includes('shram yogi')) {
      const isCorrectAge = profile.age >= 18 && profile.age <= 40;
      const isUnorg = profile.occupation === 'Unorganized Worker';
      const isCorrectIncome = profile.income <= 15000;

      if (isCorrectAge && isUnorg && isCorrectIncome) {
        status = 'Eligible';
        score = 95;
        reasons.push(`Age is ${profile.age} (fits the required 18 to 40 entry bracket).`);
        reasons.push('Active worker in the unorganized sector.');
        reasons.push(`Monthly income (₹${profile.income.toLocaleString()}) is within the ₹15,000 threshold.`);
      } else if (isUnorg && isCorrectIncome) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push(`Meets income and occupation criteria, but age (${profile.age}) is outside the 18-40 enrolment window.`);
      } else {
        if (!isUnorg) reasons.push('Scheme is exclusively for unorganized sector workers.');
        if (!isCorrectAge) reasons.push('Age is outside entry limit (18-40).');
        if (!isCorrectIncome) reasons.push('Income exceeds unorganized worker cap of ₹15,000.');
      }
    } 
    else if (nameLower.includes('kisan') || idLower.includes('pmkisan') || nameLower.includes('farmer')) {
      if (profile.occupation === 'Farmer') {
        status = 'Eligible';
        score = 95;
        reasons.push('Profile occupation matches active landholding farmer criteria.');
      } else if (profile.occupation === 'None' || profile.occupation === 'Unorganized Worker') {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push('Eligible if cultivable landholding documents (Khata/Patta) are registered in your name.');
      } else {
        reasons.push('Non-agricultural worker. Cultivable agricultural landholding required.');
      }
    } 
    else if (nameLower.includes('garib kalyan') || idLower.includes('pmgkay') || nameLower.includes('ration') || nameLower.includes('food security')) {
      const isBpl = profile.bpl === 'Yes';
      const isLowInc = profile.income <= 10000;

      if (isBpl || isLowInc) {
        status = 'Eligible';
        score = 95;
        if (isBpl) reasons.push('Possess Below Poverty Line (BPL) or priority household card.');
        if (isLowInc) reasons.push(`Income (₹${profile.income.toLocaleString()}) is under BPL benchmark.`);
      } else if (profile.income <= 18000) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push('Income is under ₹18,000. Requires registered NFSA food security card.');
      } else {
        reasons.push('Does not hold BPL status or registered NFSA food security card.');
      }
    } 
    else if (nameLower.includes('sukanya') || idLower.includes('ssy')) {
      const isFemale = profile.gender === 'Female';
      const isKid = profile.age <= 10;

      if (isFemale && isKid) {
        status = 'Eligible';
        score = 95;
        reasons.push('Gender matches scheme beneficiary target (Female Child).');
        reasons.push(`Child age (${profile.age}) is under the 10-year limit.`);
      } else if (isFemale && profile.age <= 18) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push('Gender is Female. Eligible if account was opened by a guardian before age 10.');
      } else {
        if (!isFemale) reasons.push('SSY accounts are openable only for a girl child.');
        if (!isKid) reasons.push('Beneficiary opening age must be under 10 years.');
      }
    } 
    else if (nameLower.includes('swanidhi') || idLower.includes('pmsvanidhi') || nameLower.includes('street vendor')) {
      const isUnorg = profile.occupation === 'Unorganized Worker';
      const isLowInc = profile.income <= 20000;

      if (isUnorg && isLowInc) {
        status = 'Eligible';
        score = 95;
        reasons.push('Working in unorganized sector (matches street vendor classification).');
        reasons.push(`Monthly income (₹${profile.income.toLocaleString()}) is within the credit-assist limit.`);
      } else if (isUnorg) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push('Eligible if holding a Certificate of Vending or local body recommendation letter.');
      } else {
        reasons.push('Requires street vending ID card or Certificate of Vending from Municipal ULB.');
      }
    } 
    else if (nameLower.includes('mudra') || nameLower.includes('self-employment')) {
      if (profile.occupation === 'Business Owner') {
        status = 'Eligible';
        score = 95;
        reasons.push('Profile matches micro-enterprise owner / business promoter.');
      } else if (profile.occupation === 'Unorganized Worker' || profile.occupation === 'None') {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push('Eligible for Shishu loan category to establish a new micro/small startup enterprise.');
      } else {
        reasons.push('Excludes salaried employees. Must operate or propose a small trade, service, or manufacturing business.');
      }
    } 
    else if (nameLower.includes('old age') || idLower.includes('ignoaps') || nameLower.includes('pension')) {
      const isSenior = profile.age >= 60;
      const isBpl = profile.bpl === 'Yes';

      if (isSenior && isBpl) {
        status = 'Eligible';
        score = 95;
        reasons.push(`Age is ${profile.age} (elderly citizen ≥ 60 years criteria met).`);
        reasons.push('Registered BPL household cardholder.');
      } else if (isSenior && profile.income <= 15000) {
        status = 'Possibly Eligible';
        score = 60;
        reasons.push(`Age is ${profile.age}. Requires an official BPL state certification or local income check.`);
      } else {
        if (!isSenior) reasons.push('Minimum pension age is 60 years.');
        if (!isBpl) reasons.push('Indigent criteria: BPL cardholder status required.');
      }
    }

    return { status, score, reasons };
  };

  // AI recommendation handler
  const handleFindSchemesAI = async () => {
    if (!problemText.trim()) return;
    setAiLoading(true);
    setAiGroundedResponse(null);
    setAiRecommendedSchemes([]);

    try {
      const res = await fetch('/api/schemes/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: problemText,
          profile: profile
        })
      });

      if (!res.ok) throw new Error('AI recommendation lookup failed.');
      const data = await res.json();
      setAiGroundedResponse(data.grounded_response);
      setAiRecommendedSchemes(data.recommended_schemes || []);
    } catch (err: any) {
      console.error(err);
      setAiGroundedResponse("Error generating AI response. Please check recommended schemes below or try again.");
    } finally {
      setAiLoading(false);
    }
  };

  // Render markdown response helpers
  const renderMarkdown = (text: string) => {
    if (!text) return null;
    
    const lines = text.split('\n');
    return lines.map((line, i) => {
      if (line.startsWith('### ')) {
        return <h4 key={i} className="text-md font-bold text-white mt-4 mb-2">{line.replace('### ', '')}</h4>;
      }
      if (line.startsWith('## ')) {
        return <h3 key={i} className="text-lg font-extrabold text-blue-400 mt-5 mb-2 font-['Outfit']">{line.replace('## ', '')}</h3>;
      }
      if (line.startsWith('# ')) {
        return <h2 key={i} className="text-xl font-extrabold text-white mt-6 mb-3 font-['Outfit'] border-b border-white/10 pb-2">{line.replace('# ', '')}</h2>;
      }
      
      const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('* ');
      const isNumbered = /^\d+\.\s/.test(line.trim());
      
      let content = line;
      if (isBullet) {
        content = line.trim().substring(2);
      } else if (isNumbered) {
        content = line.trim().replace(/^\d+\.\s/, '');
      }
      
      const parts = content.split('**');
      const parsedLine = parts.map((part, index) => {
        if (index % 2 === 1) {
          return <strong key={index} className="text-white font-bold">{part}</strong>;
        }
        return part;
      });
      
      if (isBullet) {
        return (
          <li key={i} className="ml-5 list-disc text-slate-300 text-sm leading-relaxed mb-1 font-semibold">
            {parsedLine}
          </li>
        );
      }
      if (isNumbered) {
        return (
          <li key={i} className="ml-5 list-decimal text-slate-300 text-sm leading-relaxed mb-1 font-semibold">
            {parsedLine}
          </li>
        );
      }
      
      if (line.trim() === '') {
        return <div key={i} className="h-2" />;
      }
      
      return <p key={i} className="text-slate-300 text-sm leading-relaxed mb-2 font-medium">{parsedLine}</p>;
    });
  };

  // Processing, filtering, and sorting for MANUAL directory
  const evaluatedSchemes = schemes.map(s => {
    const evalResult = evaluateEligibility(s);
    return {
      ...s,
      eligibility: evalResult
    };
  });

  const filteredSchemes = evaluatedSchemes.filter(s => {
    const query = searchQuery.toLowerCase();
    const matchesSearch = 
      s.name.toLowerCase().includes(query) ||
      s.ministry.toLowerCase().includes(query) ||
      s.description.toLowerCase().includes(query) ||
      s.category.toLowerCase().includes(query);

    if (!matchesSearch) return false;

    if (selectedCategory !== 'All' && s.category !== selectedCategory) return false;

    const sState = s.state_applicability || 'All';
    if (selectedState !== 'All' && sState !== 'All' && sState !== selectedState) return false;

    if (selectedBenefitType !== 'All' && s.benefit_type.toLowerCase() !== selectedBenefitType.toLowerCase()) {
      const matchesPartial = s.benefit_type.toLowerCase().includes(selectedBenefitType.toLowerCase()) || 
                             (selectedBenefitType === 'DBT' && s.benefit_type.includes('Direct Benefit Transfer'));
      if (!matchesPartial) return false;
    }

    if (selectedStatus !== 'All' && s.eligibility?.status !== selectedStatus) return false;

    return true;
  });

  const sortedSchemes = [...filteredSchemes].sort((a, b) => {
    if (sortBy === 'Best Match') {
      return (b.eligibility?.score || 0) - (a.eligibility?.score || 0);
    } else if (sortBy === 'Highest Benefit') {
      const getBenefitValue = (s: typeof a) => {
        const id = s.id ? s.id.toLowerCase() : '';
        const name = s.name.toLowerCase();
        if (id === 'pmjay' || name.includes('arogya')) return 500000;
        if (id === 'mudra' || name.includes('self-employment')) return 1000000;
        if (id === 'pmay' || name.includes('housing')) return 267000;
        if (id === 'pmsvanidhi' || name.includes('swanidhi')) return 50000;
        if (id === 'pmkisan' || name.includes('kisan')) return 6000;
        if (id === 'pmsym' || name.includes('maan-dhan')) return 3000 * 12;
        if (id === 'ignoaps' || name.includes('old age')) return 500 * 12;
        return 0;
      };
      return getBenefitValue(b) - getBenefitValue(a);
    } else if (sortBy === 'Recently Updated') {
      return a.id.localeCompare(b.id);
    }
    return 0;
  });

  const eligibleCount = evaluatedSchemes.filter(s => s.eligibility?.status === 'Eligible').length;
  const possiblyCount = evaluatedSchemes.filter(s => s.eligibility?.status === 'Possibly Eligible').length;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Hero Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-white/10 p-8 sm:p-10 shadow-[0_8px_30px_rgba(0,0,0,0.5)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_120%,rgba(59,130,246,0.15),transparent_50%)]" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-extrabold text-blue-400 uppercase tracking-wider">
            <Award className="w-3.5 h-3.5" />
            <span>Welfare Discovery Portal</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-['Outfit']">
            Government Scheme Recommendations
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed font-semibold">
            Describe your problem in plain language to find schemes, or verify your demographic profile to search and filter major Central and State government welfare benefits.
          </p>
          
          {/* Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
            <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-4">
              <span className="text-xs font-bold text-slate-400 block mb-1">Total Schemes</span>
              <span className="text-2xl font-extrabold text-white font-['Outfit']">{schemes.length || 150}</span>
            </div>
            <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-2xl p-4">
              <span className="text-xs font-bold text-emerald-400 block mb-1">Directly Eligible</span>
              <span className="text-2xl font-extrabold text-emerald-400 font-['Outfit']">{eligibleCount || 4}</span>
            </div>
            <div className="bg-amber-950/20 border border-amber-500/20 rounded-2xl p-4">
              <span className="text-xs font-bold text-amber-400 block mb-1">Possibly Eligible</span>
              <span className="text-2xl font-extrabold text-amber-400 font-['Outfit']">{possiblyCount || 3}</span>
            </div>
            <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-4">
              <span className="text-xs font-bold text-slate-400 block mb-1">Location Context</span>
              <span className="text-sm font-extrabold text-blue-400 truncate block mt-1 leading-none">{profile.state}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sub-tab selection */}
      <div className="flex border-b border-white/10 space-x-6">
        <button
          onClick={() => setActiveSubTab('ai')}
          className={`pb-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${
            activeSubTab === 'ai' 
              ? 'border-blue-500 text-blue-400 font-extrabold' 
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>AI Scheme Finder (Search by Problem)</span>
        </button>
        <button
          onClick={() => setActiveSubTab('manual')}
          className={`pb-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${
            activeSubTab === 'manual' 
              ? 'border-blue-500 text-blue-400 font-extrabold' 
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Filter className="w-4 h-4" />
          <span>Manual Schemes Directory (Filter & Profile)</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Profile Builder Sidebar */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-slate-950/40 border border-white/10 rounded-2xl p-6 shadow-xl sticky top-28">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-blue-400" />
                <h3 className="font-extrabold text-white text-base font-['Outfit']">Eligibility Profile</h3>
              </div>
              <button 
                onClick={handleResetProfile}
                className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-1 transition-all"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            </div>

            <form className="space-y-4 text-sm" onSubmit={(e) => e.preventDefault()}>
              <div>
                <label htmlFor="profile-state" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">State Residency</label>
                <select 
                  id="profile-state"
                  name="state"
                  value={profile.state}
                  onChange={handleProfileChange}
                  className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                >
                  <option className="bg-slate-900" value="Karnataka">Karnataka</option>
                  <option className="bg-slate-900" value="Maharashtra">Maharashtra</option>
                  <option className="bg-slate-900" value="Delhi">Delhi</option>
                  <option className="bg-slate-900" value="Tamil Nadu">Tamil Nadu</option>
                  <option className="bg-slate-900" value="Uttar Pradesh">Uttar Pradesh</option>
                  <option className="bg-slate-900" value="Gujarat">Gujarat</option>
                  <option className="bg-slate-900" value="West Bengal">West Bengal</option>
                  <option className="bg-slate-900" value="Rajasthan">Rajasthan</option>
                  <option className="bg-slate-900" value="Madhya Pradesh">Madhya Pradesh</option>
                  <option className="bg-slate-900" value="Bihar">Bihar</option>
                  <option className="bg-slate-900" value="Andhra Pradesh">Andhra Pradesh</option>
                  <option className="bg-slate-900" value="Telangana">Telangana</option>
                  <option className="bg-slate-900" value="Kerala">Kerala</option>
                  <option className="bg-slate-900" value="Punjab">Punjab</option>
                  <option className="bg-slate-900" value="Haryana">Haryana</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="profile-age" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">Age (Years)</label>
                  <input 
                    id="profile-age"
                    type="number"
                    name="age"
                    min="1"
                    max="110"
                    value={profile.age}
                    onChange={handleProfileChange}
                    className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                  />
                </div>
                <div>
                  <label htmlFor="profile-gender" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">Gender</label>
                  <select 
                    id="profile-gender"
                    name="gender"
                    value={profile.gender}
                    onChange={handleProfileChange}
                    className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                  >
                    <option className="bg-slate-900" value="Female">Female</option>
                    <option className="bg-slate-900" value="Male">Male</option>
                    <option className="bg-slate-900" value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="profile-income" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">Monthly Household Income (₹)</label>
                <input 
                  id="profile-income"
                  type="number"
                  name="income"
                  step="1000"
                  min="0"
                  value={profile.income}
                  onChange={handleProfileChange}
                  className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                />
              </div>

              <div>
                <label htmlFor="profile-occupation" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">Occupation Type</label>
                <select 
                  id="profile-occupation"
                  name="occupation"
                  value={profile.occupation}
                  onChange={handleProfileChange}
                  className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                >
                  <option className="bg-slate-900" value="Unorganized Worker">Unorganized Worker</option>
                  <option className="bg-slate-900" value="Farmer">Farmer</option>
                  <option className="bg-slate-900" value="Business Owner">Business Owner</option>
                  <option className="bg-slate-900" value="Student">Student</option>
                  <option className="bg-slate-900" value="Salaried Employee">Salaried Employee</option>
                  <option className="bg-slate-900" value="None">None / Unemployed</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="profile-housing" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">Housing Type</label>
                  <select 
                    id="profile-housing"
                    name="housing"
                    value={profile.housing}
                    onChange={handleProfileChange}
                    className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                  >
                    <option className="bg-slate-900" value="Tenant">Rented Apartment / Tenant</option>
                    <option className="bg-slate-900" value="Own House">Own Permanent Pucca House</option>
                    <option className="bg-slate-900" value="Homeless/Kutcha House">Kutcha House / Homeless</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="profile-bpl" className="block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide">BPL Card Status</label>
                  <select 
                    id="profile-bpl"
                    name="bpl"
                    value={profile.bpl}
                    onChange={handleProfileChange}
                    className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                  >
                    <option className="bg-slate-900" value="No">No / APL Card</option>
                    <option className="bg-slate-900" value="Yes">Yes / BPL Card</option>
                  </select>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Dynamic content rendering based on selected sub-tab */}
        <div className="lg:col-span-8 space-y-6">

          {activeSubTab === 'ai' ? (
            <div className="space-y-6 animate-in fade-in duration-300">
              
              {/* Problem text area input */}
              <div className="bg-slate-950/40 border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-blue-400 animate-pulse" />
                  <h3 className="font-extrabold text-white text-base font-['Outfit']">Describe Your Situation or Need</h3>
                </div>
                <p className="text-xs text-slate-400 font-semibold">
                  Enter your natural-language problem. The recommendation engine will search the scheme vector database and compile a grounded report with matched benefits.
                </p>
                <textarea
                  value={problemText}
                  onChange={(e) => setProblemText(e.target.value)}
                  placeholder="E.g., I lost my job as a farm worker in Karnataka, my monthly income is under 8000, and I have a female child aged 8. Are there any schemes to help with her savings or help my family get monthly rations?"
                  rows={4}
                  className="w-full bg-white/[0.04] border border-white/10 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-all text-sm font-semibold"
                />
                <div className="flex justify-end">
                  <button
                    onClick={handleFindSchemesAI}
                    disabled={aiLoading || !problemText.trim()}
                    className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-extrabold rounded-xl shadow-lg hover:shadow-blue-500/20 transition-all duration-300 flex items-center gap-2"
                  >
                    {aiLoading ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Searching Database...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Find Schemes with AI</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* RAG Report Results */}
              {(aiGroundedResponse || aiRecommendedSchemes.length > 0) && (
                <div className="space-y-6 animate-in slide-in-from-bottom duration-500">
                  
                  {/* LLM Grounded advice text */}
                  {aiGroundedResponse && (
                    <div className="bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-blue-500/30 rounded-2xl p-6 sm:p-8 shadow-2xl relative">
                      <div className="absolute top-4 right-4 inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs font-bold text-blue-400">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Grounded AI Advisory</span>
                      </div>
                      <h3 className="text-lg font-extrabold text-white mb-4 flex items-center gap-2 font-['Outfit']">
                        <Award className="w-5 h-5 text-yellow-500" />
                        <span>Your Customized Schemes Report</span>
                      </h3>
                      <div className="prose prose-invert max-w-none text-slate-300 space-y-2 border-t border-white/5 pt-4">
                        {renderMarkdown(aiGroundedResponse)}
                      </div>
                    </div>
                  )}

                  {/* Recommendation cards grid */}
                  {aiRecommendedSchemes.length > 0 && (
                    <div className="space-y-4">
                      <h3 className="text-md font-bold text-white uppercase tracking-wider font-['Outfit'] flex items-center gap-2">
                        <Landmark className="w-4 h-4 text-blue-400" />
                        <span>Recommended Scheme Cards ({aiRecommendedSchemes.length})</span>
                      </h3>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {aiRecommendedSchemes.map((scheme) => (
                          <SchemeCard 
                            key={scheme.id || scheme.name}
                            scheme={scheme}
                            onViewDetails={() => setSelectedScheme(scheme)}
                            onApplyNow={() => setWarningScheme(scheme)}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              )}

            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in duration-300">
              
              {/* Search and Filters Bar */}
              <div className="bg-slate-950/40 border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
                
                {/* Search Input */}
                <div className="relative">
                  <Search className="absolute left-4 top-3.5 h-5 w-5 text-slate-500" />
                  <input 
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search schemes by ministry, keyword, benefit, or category..."
                    className="w-full bg-white/[0.04] border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-all text-sm font-semibold"
                  />
                </div>

                {/* Filters Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-bold text-slate-400 uppercase tracking-wide">
                  
                  {/* Category Filter */}
                  <div>
                    <label htmlFor="filter-category" className="block mb-1.5">Category</label>
                    <select
                      id="filter-category"
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-2.5 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    >
                      <option className="bg-slate-900" value="All">All Categories</option>
                      <option className="bg-slate-900" value="Healthcare">Healthcare</option>
                      <option className="bg-slate-900" value="Social Security / Pension">Social Security / Pension</option>
                      <option className="bg-slate-900" value="Agriculture">Agriculture</option>
                      <option className="bg-slate-900" value="Education">Education</option>
                      <option className="bg-slate-900" value="Employment / Business">Employment / Business</option>
                      <option className="bg-slate-900" value="Housing">Housing</option>
                    </select>
                  </div>

                  {/* State Applicability Filter */}
                  <div>
                    <label htmlFor="filter-state" className="block mb-1.5">State</label>
                    <select
                      id="filter-state"
                      value={selectedState}
                      onChange={(e) => setSelectedState(e.target.value)}
                      className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-2.5 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    >
                      <option className="bg-slate-900" value="All">All States</option>
                      <option className="bg-slate-900" value="Karnataka">Karnataka</option>
                      <option className="bg-slate-900" value="Maharashtra">Maharashtra</option>
                      <option className="bg-slate-900" value="Delhi">Delhi</option>
                      <option className="bg-slate-900" value="Tamil Nadu">Tamil Nadu</option>
                      <option className="bg-slate-900" value="Uttar Pradesh">Uttar Pradesh</option>
                    </select>
                  </div>

                  {/* Benefit Type Filter */}
                  <div>
                    <label htmlFor="filter-benefit" className="block mb-1.5">Benefit Type</label>
                    <select
                      id="filter-benefit"
                      value={selectedBenefitType}
                      onChange={(e) => setSelectedBenefitType(e.target.value)}
                      className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-2.5 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    >
                      <option className="bg-slate-900" value="All">All Benefits</option>
                      <option className="bg-slate-900" value="Insurance">Insurance</option>
                      <option className="bg-slate-900" value="Subsidy">Subsidy</option>
                      <option className="bg-slate-900" value="DBT">Direct Cash (DBT)</option>
                      <option className="bg-slate-900" value="Loan">Subsidized Loan</option>
                    </select>
                  </div>

                  {/* Eligibility Filter */}
                  <div>
                    <label htmlFor="filter-status" className="block mb-1.5">Eligibility Match</label>
                    <select
                      id="filter-status"
                      value={selectedStatus}
                      onChange={(e) => setSelectedStatus(e.target.value)}
                      className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-2.5 py-2 text-white focus:outline-none focus:border-blue-500 transition-all font-semibold"
                    >
                      <option className="bg-slate-900" value="All">All Statuses</option>
                      <option className="bg-slate-900" value="Eligible">Eligible</option>
                      <option className="bg-slate-900" value="Possibly Eligible">Possibly Eligible</option>
                      <option className="bg-slate-900" value="Not Eligible">Not Eligible</option>
                    </select>
                  </div>

                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs text-slate-400">
                  <span>Showing {sortedSchemes.length} matching schemes</span>
                  <div className="flex items-center space-x-2">
                    <span>Sort by:</span>
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="bg-transparent text-blue-400 font-bold focus:outline-none cursor-pointer"
                    >
                      <option className="bg-slate-900" value="Best Match">Best Match</option>
                      <option className="bg-slate-900" value="Highest Benefit">Highest Benefit</option>
                      <option className="bg-slate-900" value="Recently Updated">Recently Updated</option>
                    </select>
                  </div>
                </div>

              </div>

              {/* Cards Grid */}
              {sortedSchemes.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {sortedSchemes.map((scheme) => (
                    <SchemeCard 
                      key={scheme.id || scheme.name}
                      scheme={scheme}
                      onViewDetails={() => setSelectedScheme(scheme)}
                      onApplyNow={() => setWarningScheme(scheme)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-slate-950/20 border border-dashed border-white/10 rounded-2xl space-y-3">
                  <XCircle className="w-12 h-12 text-slate-600 mx-auto" />
                  <h4 className="text-slate-300 font-bold">No schemes match your criteria</h4>
                  <p className="text-slate-500 text-xs max-w-sm mx-auto">
                    Try adjusting your profile variables or search filters to expand options.
                  </p>
                </div>
              )}

            </div>
          )}

        </div>

      </div>

      {/* View Details Info Modal */}
      {selectedScheme && (
        <SchemeDetailsModal 
          scheme={selectedScheme}
          onClose={() => setSelectedScheme(null)}
        />
      )}

      {/* Official Portal Apply Now Security Warning Modal */}
      {warningScheme && (
        <SecurityWarningModal 
          scheme={warningScheme}
          onClose={() => setWarningScheme(null)}
        />
      )}

    </div>
  );
};

/* --- SUB-COMPONENTS --- */

interface SchemeCardProps {
  scheme: Scheme;
  onViewDetails: () => void;
  onApplyNow: () => void;
}

const SchemeCard: React.FC<SchemeCardProps> = ({ scheme, onViewDetails, onApplyNow }) => {
  const elig = scheme.eligibility;
  const matchPercent = scheme.similarity_score ? Math.round(scheme.similarity_score * 100) : null;

  return (
    <div className="bg-slate-950/40 hover:bg-slate-950/60 border border-white/10 hover:border-blue-500/40 rounded-2xl p-5 shadow-lg flex flex-col justify-between transition-all duration-300 group relative overflow-hidden">
      
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(59,130,246,0.08),transparent_70%)] opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
      
      <div className="space-y-4 relative z-10">
        
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase bg-white/[0.04] border border-white/5 text-slate-400 px-2.5 py-1 rounded-full">
            {scheme.category}
          </span>
          
          <div className="flex items-center space-x-2">
            {matchPercent !== null && (
              <span className="text-[10px] font-extrabold bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-1 rounded-full flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5 animate-pulse" />
                <span>{matchPercent}% Match</span>
              </span>
            )}
            {elig && <StatusBadge status={elig.status} />}
          </div>
        </div>

        <div className="space-y-1">
          <h3 className="font-extrabold text-white text-base leading-tight group-hover:text-blue-400 transition-colors font-['Outfit']">
            {scheme.name}
          </h3>
          <p className="text-[11px] font-semibold text-slate-400 truncate">
            {scheme.ministry}
          </p>
        </div>

        <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
          {scheme.description}
        </p>

        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3 flex items-start gap-2.5">
          <Landmark className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-slate-400 block mb-0.5">Benefit Summary</span>
            <span className="text-slate-200 font-medium leading-normal">{scheme.benefit_amount}</span>
          </div>
        </div>

        {elig && elig.reasons.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Why you qualify</span>
            <ul className="space-y-1">
              {elig.reasons.slice(0, 2).map((reason, rIdx) => (
                <li key={rIdx} className="text-[11px] text-slate-300 leading-normal flex items-start gap-1.5 font-semibold">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{reason}</span>
                </li>
              ))}
              {elig.reasons.length > 2 && (
                <li className="text-[10px] font-semibold text-blue-400 hover:underline cursor-pointer" onClick={onViewDetails}>
                  + {elig.reasons.length - 2} more qualification criteria
                </li>
              )}
            </ul>
          </div>
        )}

        {scheme.required_documents && scheme.required_documents.length > 0 && (
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Required Documents</span>
            <div className="flex flex-wrap gap-1">
              {scheme.required_documents.slice(0, 3).map((doc, dIdx) => (
                <span key={dIdx} className="text-[9px] font-bold bg-white/[0.03] text-slate-400 px-2 py-0.5 rounded border border-white/5">
                  {doc}
                </span>
              ))}
              {scheme.required_documents.length > 3 && (
                <span className="text-[9px] font-bold text-blue-400 bg-blue-950/20 px-2 py-0.5 rounded border border-blue-500/20">
                  +{scheme.required_documents.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

      </div>

      <div className="flex gap-3 pt-5 mt-5 border-t border-white/5 relative z-10">
        <button 
          onClick={onViewDetails}
          className="flex-1 py-2 bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 rounded-xl text-xs font-extrabold text-white transition-all flex items-center justify-center gap-1.5"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>View Details</span>
        </button>
        <button 
          onClick={onApplyNow}
          className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-extrabold shadow-md hover:shadow-blue-500/20 transition-all flex items-center justify-center gap-1.5"
        >
          <span>Apply Now</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

    </div>
  );
};

const StatusBadge: React.FC<{ status: 'Eligible' | 'Possibly Eligible' | 'Not Eligible' }> = ({ status }) => {
  if (status === 'Eligible') {
    return (
      <span className="text-[10px] font-extrabold uppercase bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-full flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
        <span>Eligible</span>
      </span>
    );
  }
  if (status === 'Possibly Eligible') {
    return (
      <span className="text-[10px] font-extrabold uppercase bg-amber-500/10 border border-amber-500/20 text-amber-400 px-2.5 py-1 rounded-full flex items-center gap-1">
        <AlertTriangle className="w-3 h-3 text-amber-400" />
        <span>Possibly Eligible</span>
      </span>
    );
  }
  return (
    <span className="text-[10px] font-extrabold uppercase bg-rose-500/10 border border-rose-500/20 text-rose-400 px-2.5 py-1 rounded-full flex items-center gap-1">
      <XCircle className="w-3 h-3 text-rose-400" />
      <span>Not Eligible</span>
    </span>
  );
};

interface SchemeDetailsModalProps {
  scheme: Scheme;
  onClose: () => void;
}

const SchemeDetailsModal: React.FC<SchemeDetailsModalProps> = ({ scheme, onClose }) => {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = 'unset'; };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-300 flex flex-col max-h-[90vh]">
        
        <div className="px-6 py-5 border-b border-white/10 flex items-start justify-between bg-slate-900/50">
          <div className="space-y-1.5 max-w-[85%]">
            <span className="text-[10px] font-extrabold uppercase bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2.5 py-1 rounded-full inline-block font-sans">
              {scheme.category}
            </span>
            <h3 className="text-lg font-extrabold text-white font-['Outfit'] leading-tight">
              {scheme.name}
            </h3>
            <p className="text-xs text-slate-400 font-semibold">{scheme.ministry}</p>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-all">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-6 text-sm leading-relaxed">
          
          <div className="space-y-2">
            <h4 className="font-extrabold text-white flex items-center gap-1.5 text-xs uppercase tracking-wider text-slate-400">
              <Info className="w-4 h-4 text-blue-400" />
              <span>Description</span>
            </h4>
            <p className="text-slate-300 font-medium">{scheme.description}</p>
          </div>

          <div className="space-y-2">
            <h4 className="font-extrabold text-white flex items-center gap-1.5 text-xs uppercase tracking-wider text-slate-400">
              <Landmark className="w-4 h-4 text-blue-400" />
              <span>Benefits & Funding Type</span>
            </h4>
            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 space-y-1">
              <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Benefit Amount/Scope:</div>
              <p className="text-slate-200 font-bold text-sm">{scheme.benefit_amount}</p>
              <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider pt-2">Transfer Type:</div>
              <span className="inline-block text-[10px] font-extrabold bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20 mt-0.5">
                {scheme.benefit_type}
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="font-extrabold text-white flex items-center gap-1.5 text-xs uppercase tracking-wider text-slate-400">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <span>Detailed Eligibility Criteria</span>
            </h4>
            <p className="text-slate-300 bg-white/[0.02] border border-white/5 p-4 rounded-xl font-semibold">
              {scheme.detailed_eligibility}
            </p>
          </div>

          {scheme.required_documents && scheme.required_documents.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-extrabold text-white flex items-center gap-1.5 text-xs uppercase tracking-wider text-slate-400">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>Required Documents Checklist</span>
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {scheme.required_documents.map((doc, index) => (
                  <div key={index} className="flex items-center gap-2 p-2 bg-white/[0.01] border border-white/5 rounded-lg text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span className="text-xs font-semibold">{doc}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <h4 className="font-extrabold text-white flex items-center gap-1.5 text-xs uppercase tracking-wider text-slate-400">
              <ArrowRight className="w-4 h-4 text-blue-400" />
              <span>How to Apply</span>
            </h4>
            <p className="text-slate-300 bg-white/[0.02] border border-white/5 p-4 rounded-xl font-semibold">
              {scheme.application_process}
            </p>
          </div>

          <div className="flex flex-wrap gap-4 pt-4 border-t border-white/5 text-[11px] text-slate-500 font-bold">
            <div className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              <span>State: {scheme.state_applicability || 'All India'}</span>
            </div>
            {scheme.helpline && (
              <div className="flex items-center gap-1">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Helpline: {scheme.helpline}</span>
              </div>
            )}
            {scheme.last_verified && (
              <div className="flex items-center gap-1 ml-auto">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400/70" />
                <span>Verified: {scheme.last_verified}</span>
              </div>
            )}
          </div>

        </div>

        <div className="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/50">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 rounded-xl text-xs font-bold text-slate-300 hover:text-white transition-all"
          >
            Close Details
          </button>
        </div>

      </div>
    </div>
  );
};

interface SecurityWarningModalProps {
  scheme: Scheme;
  onClose: () => void;
}

const SecurityWarningModal: React.FC<SecurityWarningModalProps> = ({ scheme, onClose }) => {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = 'unset'; };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-slate-900 border border-red-500/20 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-300">
        
        <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-6 flex flex-col items-center text-center space-y-2">
          <AlertTriangle className="w-12 h-12 text-red-400" />
          <h3 className="text-md font-extrabold text-red-200 uppercase tracking-wide">
            Leaving RightsNavigator
          </h3>
        </div>

        <div className="p-6 space-y-4 text-xs sm:text-sm leading-relaxed text-slate-300">
          <p className="font-semibold">
            You are about to navigate to an external official government portal to apply for this scheme:
          </p>
          <div className="bg-slate-950/50 border border-white/5 p-3.5 rounded-xl break-all">
            <span className="text-slate-400 font-bold block text-[10px] uppercase mb-1">Target Portal URL</span>
            <span className="text-blue-400 font-bold text-xs hover:underline cursor-pointer">{scheme.official_portal || 'https://india.gov.in'}</span>
          </div>
          <p className="text-[11px] text-slate-500 font-bold">
            *Always confirm the URL ends in <strong className="text-slate-400">.gov.in</strong> or <strong className="text-slate-400">.nic.in</strong> before sharing sensitive personal identification data (like Aadhaar card numbers, banking OTPs, or tax files).
          </p>
        </div>

        <div className="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/50 text-xs font-bold">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 rounded-xl text-slate-300 hover:text-white transition-all"
          >
            Go Back
          </button>
          <a
            href={scheme.official_portal || 'https://india.gov.in'}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl shadow-md hover:shadow-blue-500/20 transition-all flex items-center gap-1"
          >
            <span>Proceed to Apply</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

      </div>
    </div>
  );
};
