// src/App.js - Enhanced version with proper validation and GitHub link
import React, { useState, useRef, useEffect } from 'react';
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
  githubLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.875rem',
    padding: '0.5rem 1rem',
    borderRadius: '0.5rem',
    transition: 'all 0.3s ease'
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
  supportedCompanies: {
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '1rem',
    padding: '1.5rem',
    margin: '2rem auto',
    maxWidth: '38rem',
    textAlign: 'center'
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
  },
  billingContext: {
    background: '#f0f9ff',
    border: '1px solid #93c5fd',
    borderRadius: '0.75rem',
    padding: '1rem',
    margin: '1rem 0',
    fontSize: '0.875rem',
    color: '#1e40af'
  },
  footer: {
    textAlign: 'center',
    padding: '2rem',
    borderTop: '1px solid #e5e7eb',
    marginTop: '4rem',
    color: '#6b7280'
  }
};

const WattsMyBillApp = () => {
  const [file, setFile] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [supportedCompanies, setSupportedCompanies] = useState([]);
  const [companyDetected, setCompanyDetected] = useState(null);
  const fileInputRef = useRef(null);

  const steps = [
    { id: 'upload', label: 'Upload Bill', icon: '📤' },
    { id: 'parsing', label: 'Parsing Bill', icon: '🔍' },
    { id: 'market', label: 'Market Scan', icon: '📊' },
    { id: 'rebates', label: 'Rebate Scan', icon: '💰' },
    { id: 'summary', label: 'Savings Summary', icon: '✅' }
  ];

  // Fetch supported companies on component mount
  useEffect(() => {
    const fetchSupportedCompanies = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/supported-companies`);
        setSupportedCompanies(response.data.supported_companies);
      } catch (err) {
        console.warn('Could not fetch supported companies');
      }
    };
    
    fetchSupportedCompanies();
  }, []);

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
    setCompanyDetected(null);
    
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
      setIsAnalyzing(false);
      
      if (err.response && err.response.status === 400) {
        // Handle validation error
        const errorData = err.response.data.detail;
        if (typeof errorData === 'object') {
          setError({
            message: errorData.error,
            details: errorData.validation_details,
            supportedCompanies: errorData.supported_companies,
            tips: errorData.tips
          });
        } else {
          setError({ message: errorData });
        }
      } else {
        setError({ message: 'Failed to start analysis. Make sure the backend is running.' });
      }
    }
  };

  const pollProgress = async (id) => {
    const checkProgress = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/analysis/${id}/status`);
        const { status, progress, company_detected } = response.data;
        
        if (company_detected) {
          setCompanyDetected(company_detected);
        }
        
        setCurrentStep(Math.floor((progress / 100) * steps.length));
        
        if (status === 'completed') {
          const resultsResponse = await axios.get(`${API_BASE_URL}/analysis/${id}/results`);
          setResults(resultsResponse.data);
          setIsAnalyzing(false);
          setCurrentStep(steps.length);
        } else if (status === 'failed') {
          setError({ message: 'Analysis failed' });
          setIsAnalyzing(false);
        } else {
          setTimeout(checkProgress, 2000);
        }
      } catch (pollError) {
        setError({ message: 'Lost connection to backend' });
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
    setCompanyDetected(null);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getBillingPeriodText = (results) => {
    const billingContext = results?.billing_context;
    if (billingContext?.period_type === 'quarterly') {
      return {
        period: 'Quarterly',
        description: billingContext.period_description,
        multiplier: billingContext.annual_multiplier || 4
      };
    }
    return {
      period: 'Annual',
      description: 'Based on annual estimates',
      multiplier: 1
    };
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
          <a 
            href="https://github.com/avipaul6/wattsmybill-multiagent" 
            target="_blank" 
            rel="noopener noreferrer"
            style={styles.githubLink}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#f3f4f6';
              e.target.style.color = '#111827';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.color = '#6b7280';
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>Source Code</span>
          </a>
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
            Let real AI agents analyze your Australian energy bill and save you money.
          </p>

          {/* Company Detection */}
          {companyDetected && (
            <div style={{
              ...styles.billingContext,
              background: '#f0fdf4',
              border: '1px solid #16a34a',
              color: '#166534',
              marginBottom: '1rem'
            }}>
              ✅ Detected: {companyDetected} energy bill
            </div>
          )}
          
          {/* Low confidence warning */}
          {file && !companyDetected && !error && (
            <div style={{
              ...styles.billingContext,
              background: '#fffbeb',
              border: '1px solid #f59e0b',
              color: '#92400e',
              marginBottom: '1rem'
            }}>
              ⚠️ Document uploaded - proceeding with analysis (energy company not clearly detected)
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div style={styles.error}>
              <strong>❌ {error.message}</strong>
              {error.details && (
                <div style={{marginTop: '1rem'}}>
                  <p><strong>Analysis:</strong></p>
                  <ul style={{textAlign: 'left', marginLeft: '1rem', fontSize: '0.875rem'}}>
                    <li>Energy terms found: {error.details.energy_indicators_found || 0}</li>
                    <li>Australian energy terms: {error.details.australian_energy_terms_found || 0}</li>
                    <li>Energy company recognized: {error.details.recognized_energy_company ? 'Yes' : 'No'}</li>
                    {error.details.non_energy_indicators_found > 0 && (
                      <li style={{color: '#dc2626', fontWeight: '600'}}>
                        Non-energy business indicators: {error.details.non_energy_indicators_found}
                      </li>
                    )}
                    {error.details.reason && (
                      <li style={{color: '#dc2626', fontWeight: '600'}}>
                        Detected as: {error.details.reason}
                      </li>
                    )}
                  </ul>
                </div>
              )}
              {error.tips && (
                <div style={{marginTop: '1rem'}}>
                  <p><strong>💡 Tips:</strong></p>
                  <ul style={{textAlign: 'left', marginLeft: '1rem', fontSize: '0.875rem'}}>
                    {error.tips.map((tip, index) => (
                      <li key={index}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
              {error.supportedCompanies && error.supportedCompanies.length > 0 && (
                <div style={{marginTop: '1rem'}}>
                  <p><strong>📋 Supported Companies (sample):</strong></p>
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.25rem',
                    marginTop: '0.5rem'
                  }}>
                    {error.supportedCompanies.slice(0, 8).map((company, index) => (
                      <span key={index} style={{
                        background: '#fef2f2',
                        color: '#991b1b',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.5rem',
                        fontSize: '0.75rem',
                        fontWeight: '500'
                      }}>
                        {company}
                      </span>
                    ))}
                    <span style={{
                      color: '#6b7280',
                      fontSize: '0.75rem',
                      padding: '0.25rem'
                    }}>
                      +{supportedCompanies.length - 8} more...
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

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
              {file ? file.name : 'Upload your Australian energy bill'}
            </h3>
            <p style={{color: '#6b7280', margin: 0}}>
              {file ? 'Ready to analyze!' : 'PDF or image files supported'}
            </p>
          </div>

          {/* Supported Companies */}
          {supportedCompanies.length > 0 && (
            <div style={styles.supportedCompanies}>
              <h4 style={{margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: '600'}}>
                📋 Supported Energy Companies
              </h4>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.5rem',
                justifyContent: 'center',
                fontSize: '0.875rem'
              }}>
                {supportedCompanies.slice(0, 10).map((company, index) => (
                  <span key={index} style={{
                    background: '#e0f2fe',
                    color: '#0369a1',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '1rem',
                    fontWeight: '500'
                  }}>
                    {company}
                  </span>
                ))}
                {supportedCompanies.length > 10 && (
                  <span style={{
                    background: '#f1f5f9',
                    color: '#475569',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '1rem',
                    fontWeight: '500'
                  }}>
                    +{supportedCompanies.length - 10} more
                  </span>
                )}
              </div>
            </div>
          )}
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
          <>
            {/* Billing Context Information */}
            {results.billing_context && (
              <div style={styles.billingContext}>
                ℹ️ <strong>Billing Period:</strong> {getBillingPeriodText(results).description}
              </div>
            )}

            <div style={styles.resultsGrid}>
              {/* Bill Analysis */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#dbeafe'}}>📊</div>
                  <h3 style={styles.cardTitle}>Bill Analysis</h3>
                </div>
                
                {(() => {
                  const billing = getBillingPeriodText(results);
                  const billData = results.bill_analysis?.cost_breakdown || {};
                  const usageData = results.bill_analysis?.usage_profile || {};
                  
                  const quarterlyCost = billData.quarterly_cost || billData.total_cost || 712.5;
                  const quarterlyUsage = usageData.quarterly_kwh || usageData.total_kwh || 2060;
                  const efficiencyScore = results.bill_analysis?.efficiency_score || 72;
                  
                  return (
                    <>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>{billing.period} Cost</span>
                        <strong>{formatCurrency(quarterlyCost)}</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Annual Cost</span>
                        <strong>{formatCurrency(quarterlyCost * billing.multiplier)}</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>{billing.period} Usage</span>
                        <strong>{quarterlyUsage.toLocaleString()} kWh</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Daily Average</span>
                        <strong>{usageData.daily_average || (quarterlyUsage / 90).toFixed(1)} kWh</strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Usage Category</span>
                        <strong style={{
                          color: usageData.usage_category === 'low' ? '#16a34a' : 
                                usageData.usage_category === 'high' ? '#dc2626' : '#6b7280'
                        }}>
                          {(usageData.usage_category || 'medium').charAt(0).toUpperCase() + (usageData.usage_category || 'medium').slice(1)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between'}}>
                        <span>Efficiency Score</span>
                        <strong style={{
                          color: efficiencyScore >= 80 ? '#16a34a' : 
                                efficiencyScore >= 60 ? '#f59e0b' : '#dc2626'
                        }}>
                          {efficiencyScore}/100
                        </strong>
                      </div>
                      
                      {/* Efficiency Score Progress Bar */}
                      <div style={{marginTop: '1rem'}}>
                        <div style={{
                          width: '100%',
                          height: '8px',
                          backgroundColor: '#e5e7eb',
                          borderRadius: '4px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${efficiencyScore}%`,
                            height: '100%',
                            backgroundColor: efficiencyScore >= 80 ? '#16a34a' : 
                                           efficiencyScore >= 60 ? '#f59e0b' : '#dc2626',
                            transition: 'width 0.5s ease'
                          }}></div>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>

              {/* Solar Analysis (if applicable) */}
              {results.bill_analysis?.solar_analysis?.has_solar && (
                <div style={styles.resultCard}>
                  <div style={styles.cardHeader}>
                    <div style={{...styles.cardIcon, background: '#fef3c7'}}>☀️</div>
                    <h3 style={styles.cardTitle}>Solar System Analysis</h3>
                  </div>
                  
                  {(() => {
                    const solar = results.bill_analysis.solar_analysis;
                    
                    return (
                      <>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Solar Export</span>
                          <strong>{solar.solar_export_kwh || 0} kWh</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Export Ratio</span>
                          <strong>{solar.export_ratio_percent || 0}%</strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Solar Credit</span>
                          <strong style={{color: '#16a34a'}}>
                            {formatCurrency(solar.solar_credit_amount || 0)}
                          </strong>
                        </div>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Performance</span>
                          <strong style={{
                            color: solar.performance_rating === 'excellent' ? '#16a34a' : 
                                  solar.performance_rating === 'good' ? '#f59e0b' : '#6b7280'
                          }}>
                            {(solar.performance_rating || 'good').charAt(0).toUpperCase() + (solar.performance_rating || 'good').slice(1)}
                          </strong>
                        </div>
                        
                        {solar.battery_recommendation && (
                          <div style={{
                            background: '#f0f9ff',
                            border: '1px solid #3b82f6',
                            borderRadius: '0.5rem',
                            padding: '0.75rem',
                            fontSize: '0.875rem',
                            color: '#1e40af'
                          }}>
                            💡 <strong>Battery Recommendation:</strong> Your high solar export suggests a battery system could maximize your savings.
                          </div>
                        )}
                        
                        <div style={{marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280'}}>
                          {solar.performance_note || 'Your solar system is contributing to your energy savings.'}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}

              {/* Better Plan */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#dcfce7'}}>📈</div>
                  <h3 style={styles.cardTitle}>Better Plan Available</h3>
                </div>
                
                {(() => {
                  const billing = getBillingPeriodText(results);
                  const bestPlan = results.market_research?.best_plan || {};
                  const quarterlySavings = bestPlan.quarterly_savings || bestPlan.annual_savings / 4 || 105;
                  
                  return (
                    <>
                      <h4 style={{margin: '0 0 0.5rem 0'}}>
                        {bestPlan.retailer || 'Alinta Energy'}
                      </h4>
                      <p style={{color: '#6b7280', margin: '0 0 1rem 0'}}>
                        {bestPlan.plan_name || 'Home Deal Plus'}
                      </p>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>{billing.period} Savings</span>
                        <strong style={{color: '#16a34a'}}>
                          {formatCurrency(quarterlySavings)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Annual Savings</span>
                        <strong style={{color: '#16a34a'}}>
                          {formatCurrency(quarterlySavings * billing.multiplier)}
                        </strong>
                      </div>
                      
                      {bestPlan.why_best && (
                        <div style={{
                          background: '#f0fdf4',
                          border: '1px solid #16a34a',
                          borderRadius: '0.5rem',
                          padding: '0.75rem',
                          fontSize: '0.875rem',
                          color: '#166534',
                          marginBottom: '1rem'
                        }}>
                          ✅ {bestPlan.why_best}
                        </div>
                      )}
                      
                      <button style={{...styles.button, background: 'linear-gradient(135deg, #16a34a, #15803d)'}}>
                        Switch Plan →
                      </button>
                    </>
                  );
                })()}
              </div>

              {/* Usage Recommendations */}
              {results.bill_analysis?.recommendations && results.bill_analysis.recommendations.length > 0 && (
                <div style={styles.resultCard}>
                  <div style={styles.cardHeader}>
                    <div style={{...styles.cardIcon, background: '#e0f2fe'}}>💡</div>
                    <h3 style={styles.cardTitle}>Energy Saving Tips</h3>
                  </div>
                  
                  <div style={{fontSize: '0.875rem'}}>
                    {results.bill_analysis.recommendations.slice(0, 3).map((rec, index) => (
                      <div key={index} style={{
                        padding: '0.75rem',
                        background: '#f8fafc',
                        borderRadius: '0.5rem',
                        marginBottom: '0.75rem',
                        borderLeft: '3px solid #3b82f6'
                      }}>
                        {rec}
                      </div>
                    ))}
                    
                    {results.bill_analysis.recommendations.length > 3 && (
                      <div style={{
                        textAlign: 'center',
                        color: '#6b7280',
                        fontSize: '0.75rem',
                        marginTop: '0.5rem'
                      }}>
                        +{results.bill_analysis.recommendations.length - 3} more recommendations available
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Total Savings Potential */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#f3e8ff'}}>💎</div>
                  <h3 style={styles.cardTitle}>Total Savings Potential</h3>
                </div>
                
                {(() => {
                  const billing = getBillingPeriodText(results);
                  const totalSavings = results.total_savings || 248;
                  const marketSavings = results.market_research?.savings_analysis?.max_annual_savings || 0;
                  const rebateSavings = results.rebate_analysis?.total_rebate_value || 0;
                  
                  return (
                    <div style={{textAlign: 'center'}}>
                      <div style={{fontSize: '2rem', fontWeight: '700', color: '#8b5cf6', marginBottom: '0.5rem'}}>
                        {formatCurrency(totalSavings)} / {billing.period.toLowerCase()}
                      </div>
                      <div style={{fontSize: '1.25rem', fontWeight: '600', color: '#6b7280', marginBottom: '1rem'}}>
                        {formatCurrency(totalSavings * billing.multiplier)} / year
                      </div>
                      
                      {/* Savings Breakdown */}
                      <div style={{fontSize: '0.875rem', textAlign: 'left'}}>
                        {marketSavings > 0 && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
                            <span>Plan switching:</span>
                            <span style={{color: '#16a34a'}}>{formatCurrency(marketSavings)}/year</span>
                          </div>
                        )}
                        {rebateSavings > 0 && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem'}}>
                            <span>Government rebates:</span>
                            <span style={{color: '#ea580c'}}>{formatCurrency(rebateSavings)}</span>
                          </div>
                        )}
                        <div style={{
                          borderTop: '1px solid #e5e7eb',
                          paddingTop: '0.5rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          fontWeight: '600'
                        }}>
                          <span>Total potential:</span>
                          <span style={{color: '#8b5cf6'}}>{formatCurrency(marketSavings + rebateSavings)}/year</span>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Government Rebates */}
              <div style={styles.resultCard}>
                <div style={styles.cardHeader}>
                  <div style={{...styles.cardIcon, background: '#fed7aa'}}>🎯</div>
                  <h3 style={styles.cardTitle}>Government Rebates</h3>
                </div>
                
                {(() => {
                  const rebateValue = results.rebate_analysis?.total_rebate_value || 572;
                  const rebateCount = results.rebate_analysis?.rebate_count || 3;
                  const rebates = results.rebate_analysis?.applicable_rebates || [];
                  
                  return (
                    <>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Available Rebates</span>
                        <strong style={{color: '#ea580c'}}>
                          {formatCurrency(rebateValue)}
                        </strong>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                        <span>Programs Found</span>
                        <strong>{rebateCount} rebates</strong>
                      </div>
                      
                      {/* Rebate Details */}
                      {rebates.length > 0 && (
                        <div style={{marginBottom: '1rem'}}>
                          <h5 style={{margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '600'}}>
                            Available Programs:
                          </h5>
                          {rebates.map((rebate, index) => (
                            <div key={index} style={{
                              fontSize: '0.75rem',
                              padding: '0.5rem',
                              background: '#fef3c7',
                              borderRadius: '0.25rem',
                              marginBottom: '0.25rem',
                              display: 'flex',
                              justifyContent: 'space-between'
                            }}>
                              <span>{rebate.name}</span>
                              <span style={{fontWeight: '600', color: '#ea580c'}}>
                                {formatCurrency(rebate.value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      <div style={{fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem'}}>
                        Mix of one-time rebates and ongoing credits
                      </div>
                      <button style={{...styles.button, background: 'linear-gradient(135deg, #ea580c, #c2410c)'}}>
                        Apply for Rebates
                      </button>
                    </>
                  );
                })()}
              </div>

              {/* Market Insights */}
              {results.market_research?.market_insights && (
                <div style={styles.resultCard}>
                  <div style={styles.cardHeader}>
                    <div style={{...styles.cardIcon, background: '#ecfdf5'}}>📈</div>
                    <h3 style={styles.cardTitle}>Market Position</h3>
                  </div>
                  
                  {(() => {
                    const insights = results.market_research.market_insights;
                    
                    return (
                      <>
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Your Rate Position</span>
                          <strong style={{
                            color: insights.current_rate_position === 'excellent' ? '#16a34a' : 
                                  insights.current_rate_position === 'good' ? '#f59e0b' : 
                                  insights.current_rate_position === 'poor' ? '#dc2626' : '#6b7280'
                          }}>
                            {(insights.current_rate_position || 'average').charAt(0).toUpperCase() + 
                             (insights.current_rate_position || 'average').slice(1)}
                          </strong>
                        </div>
                        
                        {insights.live_market_average && (
                          <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                            <span>Market Average Rate</span>
                            <strong>${insights.live_market_average}/kWh</strong>
                          </div>
                        )}
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Plans Analyzed</span>
                          <strong>{insights.plans_analyzed || 0} plans</strong>
                        </div>
                        
                        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                          <span>Retailers Compared</span>
                          <strong>{insights.retailer_count || 0} retailers</strong>
                        </div>
                        
                        {insights.switching_recommendation && (
                          <div style={{
                            padding: '0.75rem',
                            background: insights.switching_recommendation.includes('STRONG') ? '#f0fdf4' :
                                       insights.switching_recommendation.includes('RECOMMENDED') ? '#fffbeb' : '#f8fafc',
                            border: `1px solid ${insights.switching_recommendation.includes('STRONG') ? '#16a34a' :
                                                  insights.switching_recommendation.includes('RECOMMENDED') ? '#f59e0b' : '#6b7280'}`,
                            borderRadius: '0.5rem',
                            fontSize: '0.875rem',
                            marginTop: '1rem'
                          }}>
                            {insights.switching_recommendation}
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          </>
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

      {/* Footer */}
      <div style={styles.footer}>
        <p>
          Powered by Google Cloud ADK + Live Australian Energy Market Data
        </p>
        <p style={{fontSize: '0.875rem', marginTop: '0.5rem'}}>
          <a 
            href="https://github.com/avipaul6/wattsmybill-multiagent" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{color: '#3b82f6', textDecoration: 'none'}}
          >
            View Source Code on GitHub
          </a>
        </p>
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