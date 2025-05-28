// src/App.js - Simple version with emoji icons
import React, { useState, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #f0f9ff 0%, #ffffff 50%, #f0fdf4 100%)',
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif"
  },
  header: {
    background: 'rgba(255, 255, 255, 0.9)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid rgba(229, 231, 235, 0.5)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
    padding: '1rem 1.5rem'
  },
  headerContent: {
    maxWidth: '72rem',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem'
  },
  logoIcon: {
    width: '2.5rem',
    height: '2.5rem',
    background: 'linear-gradient(135deg, #2563eb, #16a34a)',
    borderRadius: '0.75rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.5rem'
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #2563eb, #16a34a)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    margin: 0
  },
  subtitle: {
    fontSize: '0.875rem',
    color: '#6b7280',
    margin: 0
  },
  main: {
    maxWidth: '72rem',
    margin: '0 auto',
    padding: '3rem 1.5rem'
  },
  heroTitle: {
    fontSize: '3rem',
    fontWeight: '700',
    textAlign: 'center',
    color: '#111827',
    marginBottom: '1.5rem',
    lineHeight: '1.2'
  },
  heroGradientText: {
    background: 'linear-gradient(135deg, #2563eb, #16a34a)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent'
  },
  heroSubtitle: {
    fontSize: '1.25rem',
    textAlign: 'center',
    color: '#6b7280',
    marginBottom: '3rem',
    maxWidth: '32rem',
    marginLeft: 'auto',
    marginRight: 'auto'
  },
  uploadArea: {
    background: 'white',
    border: '3px dashed #d1d5db',
    borderRadius: '1.5rem',
    padding: '3rem 2.5rem',
    textAlign: 'center',
    margin: '2.5rem auto',
    maxWidth: '38rem',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
  },
  uploadAreaSuccess: {
    borderColor: '#16a34a',
    background: '#f0fdf4'
  },
  uploadIcon: {
    fontSize: '3rem',
    marginBottom: '1rem'
  },
  progressContainer: {
    margin: '4rem 0',
    background: 'white',
    borderRadius: '1.5rem',
    padding: '2rem',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
  },
  progressSteps: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '2rem',
    flexWrap: 'wrap',
    gap: '1rem'
  },
  progressStep: {
    flex: 1,
    minWidth: '120px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  },
  progressIcon: {
    width: '3rem',
    height: '3rem',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '0.75rem',
    fontSize: '1.5rem',
    transition: 'all 0.5s ease'
  },
  progressIconCompleted: {
    background: '#16a34a',
    color: 'white',
    transform: 'scale(1.1)'
  },
  progressIconCurrent: {
    background: '#3b82f6',
    color: 'white',
    animation: 'pulse 2s infinite',
    transform: 'scale(1.1)'
  },
  progressIconPending: {
    background: '#e5e7eb',
    color: '#9ca3af'
  },
  resultsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '2rem',
    margin: '4rem 0'
  },
  resultCard: {
    background: 'white',
    borderRadius: '1.5rem',
    padding: '2rem',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
    border: '1px solid rgba(229, 231, 235, 0.5)',
    transition: 'all 0.3s ease'
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '1.5rem'
  },
  cardIcon: {
    width: '2.5rem',
    height: '2.5rem',
    borderRadius: '0.75rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.25rem'
  },
  cardTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#111827',
    margin: 0
  },
  button: {
    background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
    color: 'white',
    border: 'none',
    padding: '1rem 2rem',
    borderRadius: '0.75rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    fontSize: '1rem',
    width: '100%'
  },
  error: {
    background: '#fef2f2',
    border: '1px solid #fca5a5',
    color: '#dc2626',
    padding: '1rem',
    borderRadius: '0.75rem',
    marginBottom: '1.5rem',
    maxWidth: '32rem',
    margin: '0 auto 1.5rem'
  }
};

const WattsMyBillApp = () => {
  const [file, setFile] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const steps = [
    { id: 'upload', label: 'Upload Bill', icon: '📤' },
    { id: 'parsing', label: 'Parsing Bill', icon: '🔍' },
    { id: 'market', label: 'Market Scan', icon: '📊' },
    { id: 'rebates', label: 'Rebate Scan', icon: '💰' },
    { id: 'summary', label: 'Savings Summary', icon: '✅' }
  ];

  const handleFileUpload = async (event) => {
    const uploadedFile = event.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setError(null);
      await startAnalysis(uploadedFile);
    }
  };

  const startAnalysis = async (uploadedFile) => {
    setIsAnalyzing(true);
    setCurrentStep(0);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('state', 'QLD');

      const response = await axios.post(`${API_BASE_URL}/upload-bill`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { analysis_id } = response.data;
      pollProgress(analysis_id);
      
    } catch (err) {
      setError('Failed to start analysis. Make sure the backend is running.');
      setIsAnalyzing(false);
    }
  };

  const pollProgress = async (id) => {
    const checkProgress = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/analysis/${id}/status`);
        const { status, progress } = response.data;
        
        setCurrentStep(Math.floor((progress / 100) * steps.length));
        
        if (status === 'completed') {
          const resultsResponse = await axios.get(`${API_BASE_URL}/analysis/${id}/results`);
          setResults(resultsResponse.data);
          setIsAnalyzing(false);
          setCurrentStep(steps.length);
        } else if (status === 'failed') {
          setError('Analysis failed');
          setIsAnalyzing(false);
        } else {
          setTimeout(checkProgress, 2000);
        }
      } catch (pollError) {
        setError('Lost connection to backend');
        setIsAnalyzing(false);
      }
    };
    
    checkProgress();
  };

  const resetAnalysis = () => {
    setFile(null);
    setCurrentStep(0);
    setIsAnalyzing(false);
    setResults(null);
    setError(null);
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.logo}>
            <div style={styles.logoIcon}>⚡</div>
            <div>
              <h1 style={styles.title}>WattsMyBill</h1>
              <p style={styles.subtitle}>AI Energy Analysis</p>
            </div>
          </div>
          <div style={{fontSize: '0.875rem', color: '#6b7280'}}>
            Powered by Google Cloud ADK + Live API Data
          </div>
        </div>
      </div>

      <div style={styles.main}>
        {/* Hero Section */}
        <div style={{textAlign: 'center', marginBottom: '4rem'}}>
          <h2 style={styles.heroTitle}>
            What's Really Going On<br />
            <span style={styles.heroGradientText}>With Your Energy Bill?</span>
          </h2>
          <p style={styles.heroSubtitle}>
            Let real AI agents analyze your energy bill and save you money.
          </p>

          {/* Error Display */}
          {error && <div style={styles.error}>{error}</div>}

          {/* Upload Area */}
          <div 
            style={{
              ...styles.uploadArea,
              ...(file ? styles.uploadAreaSuccess : {})
            }}
            onClick={() => fileInputRef.current?.click()}
            onMouseEnter={(e) => {
              if (!file) {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.background = '#f8faff';
                e.target.style.transform = 'translateY(-2px)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = file ? '#16a34a' : '#d1d5db';
              e.target.style.background = file ? '#f0fdf4' : 'white';
              e.target.style.transform = 'translateY(0)';
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileUpload}
              style={{display: 'none'}}
              disabled={isAnalyzing}
            />
            
            <div style={styles.uploadIcon}>
              {file ? '✅' : '📤'}
            </div>
            
            <h3 style={{fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem'}}>
              {file ? file.name : 'Upload your bill'}
            </h3>
            <p style={{color: '#6b7280', margin: 0}}>
              {file ? 'Ready to analyze!' : 'PDF or image'}
            </p>
          </div>
        </div>

        {/* Progress Steps */}
        {(isAnalyzing || results) && (
          <div style={styles.progressContainer}>
            <h3 style={{textAlign: 'center', marginBottom: '2rem'}}>Analysis Progress</h3>
            <div style={styles.progressSteps}>
              {steps.map((step, index) => {
                const isCompleted = currentStep > index;
                const isCurrent = currentStep === index && isAnalyzing;
                
                return (
                  <div key={step.id} style={styles.progressStep}>
                    <div style={{
                      ...styles.progressIcon,
                      ...(isCompleted ? styles.progressIconCompleted : 
                          isCurrent ? styles.progressIconCurrent : 
                          styles.progressIconPending)
                    }}>
                      {isCompleted ? '✅' : step.icon}
                    </div>
                    <span style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: isCompleted || isCurrent ? '#111827' : '#9ca3af'
                    }}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Results Cards */}
        {results && (
          <div style={styles.resultsGrid}>
            {/* Bill Analysis */}
            <div style={styles.resultCard}>
              <div style={styles.cardHeader}>
                <div style={{...styles.cardIcon, background: '#dbeafe'}}>📊</div>
                <h3 style={styles.cardTitle}>Bill Analysis</h3>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                <span>Annual Cost</span>
                <strong>${(results.bill_analysis?.cost_breakdown?.total_cost || 2850).toLocaleString()}</strong>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                <span>Usage</span>
                <strong>{(results.bill_analysis?.usage_profile?.total_kwh || 8240).toLocaleString()} kWh</strong>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between'}}>
                <span>Efficiency Score</span>
                <strong>{results.bill_analysis?.efficiency_score || 72}/100</strong>
              </div>
            </div>

            {/* Better Plan */}
            <div style={styles.resultCard}>
              <div style={styles.cardHeader}>
                <div style={{...styles.cardIcon, background: '#dcfce7'}}>📈</div>
                <h3 style={styles.cardTitle}>Better Plan Available</h3>
              </div>
              <h4 style={{margin: '0 0 0.5rem 0'}}>
                {results.market_research?.best_plan?.retailer || 'Alinta Energy'}
              </h4>
              <p style={{color: '#6b7280', margin: '0 0 1rem 0'}}>
                {results.market_research?.best_plan?.plan_name || 'Home Deal Plus'}
              </p>
              <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                <span>Annual Savings</span>
                <strong style={{color: '#16a34a'}}>
                  ${(results.market_research?.best_plan?.annual_savings || 420).toLocaleString()}
                </strong>
              </div>
              <button style={{...styles.button, background: 'linear-gradient(135deg, #16a34a, #15803d)'}}>
                Switch Plan →
              </button>
            </div>

            {/* Potential Savings */}
            <div style={styles.resultCard}>
              <div style={styles.cardHeader}>
                <div style={{...styles.cardIcon, background: '#f3e8ff'}}>💎</div>
                <h3 style={styles.cardTitle}>Potential Savings</h3>
              </div>
              <div style={{textAlign: 'center'}}>
                <div style={{fontSize: '2.5rem', fontWeight: '700', color: '#8b5cf6', marginBottom: '0.5rem'}}>
                  ${(results.total_savings || 992).toLocaleString()}
                </div>
                <p style={{margin: 0}}>Total annual savings potential</p>
              </div>
            </div>

            {/* Rebates Found */}
            <div style={styles.resultCard}>
              <div style={styles.cardHeader}>
                <div style={{...styles.cardIcon, background: '#fed7aa'}}>🎯</div>
                <h3 style={styles.cardTitle}>Rebate Found</h3>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                <span>Government Rebates</span>
                <strong style={{color: '#ea580c'}}>
                  ${(results.rebate_analysis?.total_rebate_value || 572).toLocaleString()}
                </strong>
              </div>
              <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                <span>Programs Found</span>
                <strong>{results.rebate_analysis?.rebate_count || 3} rebates</strong>
              </div>
              <button style={{...styles.button, background: 'linear-gradient(135deg, #ea580c, #c2410c)'}}>
                Apply for Rebates
              </button>
            </div>
          </div>
        )}

        {/* CTA Button - Only show after analysis or if there's an error */}
        {(results || error) && (
          <div style={{textAlign: 'center', marginTop: '3rem'}}>
            <button 
              onClick={resetAnalysis}
              style={{
                ...styles.button,
                fontSize: '1.125rem',
                padding: '1.25rem 2.5rem',
                width: 'auto',
                maxWidth: '300px',
                margin: '0 auto'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(59, 130, 246, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              Try Another Bill
            </button>
          </div>
        )}
      </div>
      
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
      `}</style>
    </div>
  );
};

export default WattsMyBillApp;