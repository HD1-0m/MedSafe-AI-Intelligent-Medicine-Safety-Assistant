import React, { useState, useRef } from 'react';
import { 
  Search, 
  Upload, 
  AlertTriangle, 
  Activity, 
  Pill, 
  FileText, 
  ChevronRight, 
  X, 
  CheckCircle2,
  Info,
  Loader2,
  Camera,
  Stethoscope,
  MessageSquare,
  Siren,
  User
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Medicine, medicineDb } from './medicineDb';
import { identifyMedicine, checkInteractions } from './logic';
import { explainRisk, parsePrescription, monitorSideEffects, predictEmergencyRisk } from './geminiService';

type Tab = 'interactions' | 'ocr' | 'symptoms' | 'sideEffects' | 'emergency';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('interactions');
  const [medsInput, setMedsInput] = useState('');
  const [interactions, setInteractions] = useState<any[]>([]);
  const [ocrResult, setOcrResult] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Side Effect Monitor State
  const [age, setAge] = useState('25');
  const [gender, setGender] = useState('Male');
  const [medsTaken, setMedsTaken] = useState('');
  const [dosesTaken, setDosesTaken] = useState('');
  const [sideEffectAdvice, setSideEffectAdvice] = useState<string | null>(null);

  // Symptoms State
  const [symptoms, setSymptoms] = useState('');
  const [symptomAdvice, setSymptomAdvice] = useState<string | null>(null);

  // Emergency State
  const [emergencySymptoms, setEmergencySymptoms] = useState('');
  const [medicalHistory, setMedicalHistory] = useState('');
  const [emergencyAdvice, setEmergencyAdvice] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleCheckInteractions = () => {
    const names = medsInput.split(',').map(n => n.trim()).filter(n => n);
    const identified = names.map(n => identifyMedicine(n)).filter(m => m) as Medicine[];
    const results = checkInteractions(identified);
    setInteractions(results);
    
    if (results.length > 0) {
      setIsProcessing(true);
      explainRisk(results[0].risk, results.map(r => r.description)).then(advice => {
        setSymptomAdvice(advice);
        setIsProcessing(false);
      });
    } else {
      setSymptomAdvice(null);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64 = event.target?.result as string;
      const result = await parsePrescription(base64, file.type);
      setOcrResult(result);
      setIsProcessing(false);
    };
    reader.readAsDataURL(file);
  };

  const handleMonitorSideEffects = async () => {
    setIsProcessing(true);
    const advice = await monitorSideEffects(age, gender, medsTaken, dosesTaken);
    setSideEffectAdvice(advice);
    setIsProcessing(false);
  };

  const handlePredictEmergency = async () => {
    setIsProcessing(true);
    const advice = await predictEmergencyRisk(emergencySymptoms, medicalHistory);
    setEmergencyAdvice(advice);
    setIsProcessing(false);
  };

  const AIAdviceBox = ({ title, content }: { title: string, content: string }) => (
    <div className="mt-8 p-6 bg-[#0B2418] border border-emerald-900/30 rounded-lg text-[#4ADE80] font-medium leading-relaxed">
      <div className="flex items-center gap-2 mb-4 text-[#4ADE80]">
        <span className="text-lg">🤖</span>
        <span className="font-bold">{title}</span>
      </div>
      <div className="whitespace-pre-wrap text-sm">
        {content}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0F172A] text-white font-sans selection:bg-emerald-500/30">
      {/* Header */}
      <header className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-[#0F172A] shadow-xl">
            <Stethoscope size={28} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            MedSafe AI – Intelligent Medicine Safety Assistant
          </h1>
        </div>
        
        <nav className="flex flex-wrap items-center gap-x-8 gap-y-4 border-b border-slate-800 pb-2">
          {[
            { id: 'interactions', label: 'Medicine Interaction Checker', icon: Pill },
            { id: 'ocr', label: 'Prescription OCR', icon: FileText },
            { id: 'symptoms', label: 'Symptom & Doubt Solver', icon: MessageSquare },
            { id: 'sideEffects', label: 'Side-Effect Monitor', icon: AlertTriangle },
            { id: 'emergency', label: 'Emergency Risk Predictor', icon: Siren },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`flex items-center gap-2 pb-3 text-sm font-medium transition-all relative ${
                activeTab === tab.id 
                  ? 'text-red-500' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <tab.icon size={16} className={activeTab === tab.id ? 'text-red-500' : 'text-amber-500'} />
              {tab.label}
              {activeTab === tab.id && (
                <motion.div 
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-red-500"
                />
              )}
            </button>
          ))}
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 pb-20">
        <AnimatePresence mode="wait">
          {activeTab === 'interactions' && (
            <motion.div
              key="interactions"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center text-white rotate-12">
                  <Pill size={24} />
                </div>
                <h2 className="text-3xl font-bold">Medicine Interaction Checker</h2>
              </div>

              <div className="space-y-4 max-w-2xl">
                <label className="block text-sm font-medium text-slate-400">Enter medicines :</label>
                <input
                  type="text"
                  value={medsInput}
                  onChange={(e) => setMedsInput(e.target.value)}
                  placeholder="e.g. Aspirin, Warfarin"
                  className="w-full bg-[#1E293B] border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                />
                <button
                  onClick={handleCheckInteractions}
                  className="bg-[#1E293B] hover:bg-slate-800 border border-slate-700 text-white px-6 py-2.5 rounded-lg font-medium text-sm transition-all"
                >
                  Check Interactions
                </button>
              </div>

              {symptomAdvice && (
                <AIAdviceBox title="AI Enhanced Advice: Here's a friendly medical guidance paragraph for you:" content={symptomAdvice} />
              )}
            </motion.div>
          )}

          {activeTab === 'ocr' && (
            <motion.div
              key="ocr"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-slate-900">
                  <FileText size={24} />
                </div>
                <h2 className="text-3xl font-bold">Extract Medicines From Prescription Image</h2>
              </div>

              <div className="max-w-xl">
                <p className="text-sm text-slate-400 mb-4">Upload prescription image</p>
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-emerald-500/50 transition-all cursor-pointer bg-[#1E293B]/50 group"
                >
                  <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*" />
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-left">
                      <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center text-slate-400 group-hover:text-emerald-500">
                        <Upload size={24} />
                      </div>
                      <div>
                        <p className="font-bold">Drag and drop file here</p>
                        <p className="text-xs text-slate-500">Limit 200MB per file • JPG, PNG, JPEG</p>
                      </div>
                    </div>
                    <button className="bg-[#1E293B] border border-slate-700 px-4 py-2 rounded-lg text-sm font-medium">
                      Browse files
                    </button>
                  </div>
                </div>
              </div>

              {isProcessing && (
                <div className="flex items-center gap-3 text-emerald-500">
                  <Loader2 className="animate-spin" />
                  <span>Processing prescription...</span>
                </div>
              )}

              {ocrResult && (
                <AIAdviceBox title="AI Enhanced Advice: Extracted Prescription Details" content={ocrResult} />
              )}
            </motion.div>
          )}

          {activeTab === 'sideEffects' && (
            <motion.div
              key="sideEffects"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="grid grid-cols-1 lg:grid-cols-2 gap-12"
            >
              <div className="space-y-8">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center text-white">
                    <AlertTriangle size={24} />
                  </div>
                  <h2 className="text-3xl font-bold">Experience & Side-Effect Monitor</h2>
                </div>

                <div className="space-y-6 bg-[#1E293B] p-8 rounded-2xl border border-slate-800">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Enter your age:</label>
                    <div className="flex items-center gap-2 bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-2">
                      <input 
                        type="number" 
                        value={age} 
                        onChange={(e) => setAge(e.target.value)}
                        className="bg-transparent w-full focus:outline-none"
                      />
                      <div className="flex items-center gap-2 text-slate-500">
                        <button onClick={() => setAge(String(Number(age)-1))}>-</button>
                        <button onClick={() => setAge(String(Number(age)+1))}>+</button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Select your gender:</label>
                    <select 
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-3 focus:outline-none"
                    >
                      <option>Male</option>
                      <option>Female</option>
                      <option>Other</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Enter medicine(s) taken (comma-separated):</label>
                    <textarea 
                      value={medsTaken}
                      onChange={(e) => setMedsTaken(e.target.value)}
                      className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-3 h-24 focus:outline-none"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Enter dose(s) taken (mg, comma-separated if multiple):</label>
                    <textarea 
                      value={dosesTaken}
                      onChange={(e) => setDosesTaken(e.target.value)}
                      className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-3 h-24 focus:outline-none"
                    />
                  </div>

                  <button 
                    onClick={handleMonitorSideEffects}
                    disabled={isProcessing}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2"
                  >
                    {isProcessing ? <Loader2 className="animate-spin" /> : <Activity size={20} />}
                    Monitor Side Effects
                  </button>
                </div>
              </div>

              <div>
                {sideEffectAdvice && (
                  <AIAdviceBox title="AI Enhanced Advice: Side Effect Analysis" content={sideEffectAdvice} />
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'symptoms' && (
            <motion.div
              key="symptoms"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-3xl mx-auto space-y-8"
            >
               <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center text-white">
                  <MessageSquare size={24} />
                </div>
                <h2 className="text-3xl font-bold">Symptom & Doubt Solver</h2>
              </div>

              <div className="bg-[#1E293B] p-8 rounded-2xl border border-slate-800 space-y-6">
                <textarea 
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  placeholder="Describe your symptoms or ask a medical question..."
                  className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-4 h-48 focus:outline-none"
                />
                <button 
                  onClick={async () => {
                    setIsProcessing(true);
                    const advice = await explainRisk("Symptom Analysis", [symptoms]);
                    setSymptomAdvice(advice);
                    setIsProcessing(false);
                  }}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-4 rounded-xl font-bold transition-all"
                >
                  Get AI Advice
                </button>
              </div>

              {symptomAdvice && (
                <AIAdviceBox title="AI Enhanced Advice: Symptom Guidance" content={symptomAdvice} />
              )}
            </motion.div>
          )}

          {activeTab === 'emergency' && (
            <motion.div
              key="emergency"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-3xl mx-auto space-y-8"
            >
               <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-600 rounded-lg flex items-center justify-center text-white">
                  <Siren size={24} />
                </div>
                <h2 className="text-3xl font-bold">Emergency Risk Predictor</h2>
              </div>

              <div className="bg-[#1E293B] p-8 rounded-2xl border border-slate-800 space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-300">Current Emergency Symptoms:</label>
                  <textarea 
                    value={emergencySymptoms}
                    onChange={(e) => setEmergencySymptoms(e.target.value)}
                    className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-3 h-32 focus:outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-300">Brief Medical History:</label>
                  <textarea 
                    value={medicalHistory}
                    onChange={(e) => setMedicalHistory(e.target.value)}
                    className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-4 py-3 h-32 focus:outline-none"
                  />
                </div>
                <button 
                  onClick={handlePredictEmergency}
                  className="w-full bg-red-600 hover:bg-red-700 text-white py-4 rounded-xl font-bold transition-all"
                >
                  Predict Risk Level
                </button>
              </div>

              {emergencyAdvice && (
                <AIAdviceBox title="AI Enhanced Advice: Emergency Risk Analysis" content={emergencyAdvice} />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="max-w-7xl mx-auto px-6 py-12 border-t border-slate-800 text-center text-slate-500 text-xs">
        <p>© 2026 MedSafe AI – Intelligent Medicine Safety Assistant. For educational purposes only.</p>
      </footer>
    </div>
  );
}
