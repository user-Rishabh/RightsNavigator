import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PincodeWidget } from './components/PincodeWidget';
import { ChatNavigator } from './components/ChatNavigator';
import { RightsCatalog } from './components/RightsCatalog';
import { CaseTracker } from './components/CaseTracker';
import { DocumentModal } from './components/DocumentModal';
import { Footer } from './components/Footer';
import { PincodeInfo } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'catalog' | 'cases'>('chat');
  const [pincodeInfo, setPincodeInfo] = useState<PincodeInfo | null>(null);
  const [showPincodeModal, setShowPincodeModal] = useState(false);
  const [caseCount, setCaseCount] = useState(0);
  const [suggestedPrompt, setSuggestedPrompt] = useState('');
  const [navigationRequest, setNavigationRequest] = useState(0);
  const [isLightMode, setIsLightMode] = useState(() => {
    const savedTheme = localStorage.getItem('rights-navigator-theme');
    if (savedTheme) {
      return savedTheme === 'light';
    }
    return window.matchMedia('(prefers-color-scheme: light)').matches;
  });

  // Document Draft Modal State
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [draftDocType, setDraftDocType] = useState('rti');
  const [draftPrefill, setDraftPrefill] = useState<any>({});

  // Initial PIN code lookup on mount
  useEffect(() => {
    fetch('/api/pincode/560001')
      .then((res) => res.json())
      .then((data) => setPincodeInfo(data))
      .catch((err) => console.error(err));

    fetch('/api/cases')
      .then((res) => res.json())
      .then((data) => setCaseCount(data.cases?.length || 0))
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (isLightMode) {
      root.classList.remove('dark');
      root.classList.add('light');
      root.setAttribute('data-theme', 'light');
      localStorage.setItem('rights-navigator-theme', 'light');
    } else {
      root.classList.remove('light');
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
      localStorage.setItem('rights-navigator-theme', 'dark');
    }
  }, [isLightMode]);

  const handleOpenDraftModal = (docType: string, prefillData: any) => {
    setDraftDocType(docType);
    setDraftPrefill(prefillData);
    setShowDraftModal(true);
  };

  const handleSelectCatalogCategory = (catId: string, promptText: string) => {
    setActiveTab('chat');
    setSuggestedPrompt(promptText);
    setNavigationRequest((current) => current + 1);
  };

  const handleSaveCase = (newCase: any) => {
    setCaseCount((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen flex flex-col bg-page text-txtprimary font-sans selection:bg-accent selection:text-page transition-colors duration-200">
      {/* Navigation Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pincodeInfo={pincodeInfo}
        onOpenPincodeModal={() => setShowPincodeModal(true)}
        caseCount={caseCount}
        isLightMode={isLightMode}
        onToggleTheme={() => setIsLightMode((current) => !current)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {activeTab === 'chat' && (
          <ChatNavigator
            pincodeInfo={pincodeInfo}
            onOpenPincodeModal={() => setShowPincodeModal(true)}
            onOpenDraftModal={handleOpenDraftModal}
            onSaveCase={handleSaveCase}
            suggestedPrompt={suggestedPrompt}
            navigationRequest={navigationRequest}
          />
        )}

        {activeTab === 'catalog' && (
          <RightsCatalog onSelectCategory={handleSelectCatalogCategory} />
        )}

        {activeTab === 'cases' && (
          <CaseTracker
            onNewCase={() => setActiveTab('chat')}
            onOpenDraftModal={handleOpenDraftModal}
          />
        )}
      </main>

      {/* PIN Code Lookup Modal */}
      {showPincodeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
          <div className="w-full max-w-xl">
            <PincodeWidget
              currentPincode={pincodeInfo}
              onSelectPincode={(info) => {
                setPincodeInfo(info);
                setShowPincodeModal(false);
              }}
              onClose={() => setShowPincodeModal(false)}
            />
          </div>
        </div>
      )}

      {/* Document Draft Modal */}
      <DocumentModal
        isOpen={showDraftModal}
        onClose={() => setShowDraftModal(false)}
        initialDocType={draftDocType}
        prefillData={draftPrefill}
      />

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default App;
